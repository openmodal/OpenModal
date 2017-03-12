
# Copyright (C) 2014-2017 Matjaž Mršnik, Miha Pirnat, Janko Slavič, Blaž Starc (in alphabetic order)
# 
# This file is part of OpenModal.
# 
# OpenModal is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# 
# OpenModal is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with OpenModal.  If not, see <http://www.gnu.org/licenses/>.


__author__ = 'Matjaz'

from PyQt5 import QtGui, QtWidgets

import OpenModal.preferences as preferences_

class SubWidget(QtWidgets.QWidget):
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
        """The method is called when new data is loaded into
        OpenModal, for example when a saved project is opened."""
        raise NotImplementedError

    def refresh(self):
        """The method is called when the widget is opened. When,
        for example, someone switches from Geometry to Measurement,
        refresh() is called on MeasurementWidget object."""
        self.reload()

    def closeEvent(self, *args, **kwargs):
        pass
