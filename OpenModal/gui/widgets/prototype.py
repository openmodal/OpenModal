__author__ = 'Matjaz'

from PyQt4 import QtGui

import OpenModal.preferences as preferences_

class SubWidget(QtGui.QWidget):
    """Widget stub."""
    def __init__(self, modaldata, status_bar, lang, preferences=dict(), desktop_widget=None,
                 preferences_window=None, action_new=None, action_open=None, parent=None):
        super(SubWidget, self).__init__(parent)

        self.settings = preferences
        self.desktop_widget = desktop_widget
        self.preferences_window = preferences_window
        self.action_new = action_new
        self.action_open = action_open

        if len(self.settings) == 0:
            for key, value in preferences_.DEFAULTS.items():
                self.settings[key] = value

        self._lang = lang
        self.modaldata = modaldata
        self.status_bar = status_bar

        self.setContentsMargins(0, 0, 0, 0)

    def reload(self, *args, **kwargs):
        raise NotImplementedError

    def refresh(self):
        self.reload()

    def closeEvent(self, *args, **kwargs):
        pass