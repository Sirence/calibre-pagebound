from calibre.customize import InterfaceActionBase


class PageboundSearchPlugin(InterfaceActionBase):
    """
    Entry point Calibre looks for when loading the plugin.
    The actual UI logic lives in ui.py (actual_plugin below) because
    Qt-related imports must not happen at the top level of this file.
    """

    name = 'Pagebound Search'
    description = 'Adds a toolbar/menu button that opens a Pagebound.co search for the selected book.'
    supported_platforms = ['windows', 'osx', 'linux']
    author = 'You'
    version = (1, 0, 0)
    minimum_calibre_version = (5, 0, 0)

    actual_plugin = 'calibre_plugins.pagebound_search.ui:PageboundSearchAction'

    def is_customizable(self):
        return False
