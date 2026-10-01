import os
import shutil
import subprocess
from urllib.parse import quote

from qt.core import QMenu, QUrl, QDesktopServices
from calibre.gui2.actions import InterfaceAction
from calibre.gui2 import error_dialog


#this might not work on every browser sorry
BROWSER_CANDIDATES = (
    'vivaldi', 'vivaldi-stable', 'firefox', 'firefox-esr', 'chromium',
    'chromium-browser', 'google-chrome', 'google-chrome-stable',
    'brave-browser', 'opera', 'epiphany', 'konqueror',
    'x-www-browser', 'xdg-open',
)


class PageboundSearchAction(InterfaceAction):

    name = 'Pagebound Search'

    action_spec = ('Pagebound Search', 'images/icon.png', 'Search for this book on Pagebound.co', None)

    action_type = 'current'

    def genesis(self):
        icon = get_icons('images/icon.png', 'Pagebound Search')
        self.qaction.setIcon(icon)

        # Left click on the toolbar button = search title + author
        self.qaction.triggered.connect(self.search_current_book_with_author)

        # Dropdown with both options
        self.menu = QMenu(self.gui)
        self.menu.addAction(icon, 'Search title + author on Pagebound', self.search_current_book_with_author)
        self.menu.addAction(icon, 'Search title only on Pagebound', self.search_current_book)
        self.qaction.setMenu(self.menu)

    def search_current_book(self):
        self._search_current_book(with_author=False)

    def search_current_book_with_author(self):
        self._search_current_book(with_author=True)

    def _search_current_book(self, with_author):
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows:
            return error_dialog(
                self.gui,
                'No book selected',
                'Select a book in your library first.',
                show=True,
            )

        db = self.gui.current_db.new_api
        for row in rows:
            book_id = self.gui.library_view.model().id(row)
            title = db.field_for('title', book_id)
            if not title:
                continue
            if with_author:
                authors = db.field_for('authors', book_id) or ()
                query = ' '.join([title] + list(authors))
            else:
                query = title
            self.open_pagebound(query)

    def open_pagebound(self, query):
        url = 'https://pagebound.co/results?query={}&type=Book'.format(quote(str(query)))
        if not self._open_with_default_browser(url) and not self._open_with_browser_binary(url):
            # Last resort: let Qt/the desktop environment figure it out
            QDesktopServices.openUrl(QUrl(url))

    def _open_with_default_browser(self, url):
        xdg_settings = shutil.which('xdg-settings')
        if not xdg_settings:
            return False
        try:
            result = subprocess.run(
                [xdg_settings, 'get', 'default-web-browser'],
                capture_output=True, text=True, timeout=3,
            )
            desktop_file = result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            return False
        if not desktop_file:
            return False

        search_dirs = [
            os.path.expanduser('~/.local/share/applications'),
            '/usr/local/share/applications',
            '/usr/share/applications',
        ]
        for directory in search_dirs:
            desktop_path = os.path.join(directory, desktop_file)
            if not os.path.isfile(desktop_path):
                continue
            try:
                with open(desktop_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if not line.startswith('Exec='):
                            continue
                        # Strip desktop field codes like %u, %U, %f, etc.
                        parts = [p for p in line[len('Exec='):].strip().split() if not p.startswith('%')]
                        if not parts:
                            return False
                        binary = shutil.which(parts[0])
                        if not binary:
                            return False
                        try:
                            subprocess.Popen([binary, url])
                            return True
                        except OSError:
                            return False
            except OSError:
                continue
        return False

    def _open_with_browser_binary(self, url):
        env_browser = os.environ.get('BROWSER')
        candidates = ([env_browser] if env_browser else []) + list(BROWSER_CANDIDATES)
        for name in candidates:
            path = shutil.which(name)
            if not path:
                continue
            try:
                subprocess.Popen([path, url])
                return True
            except OSError:
                continue
        return False
