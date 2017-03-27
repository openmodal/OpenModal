
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

from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets
# from PyQt4 import QtGui, QtCore, QtWebKit

import qtawesome as qta

import OpenModal.gui.widgets.prototype as prototype

import OpenModal.gui.templates as templ


class WelcomeWidget(prototype.SubWidget):
    """Welcome widget stub."""
    def __init__(self, *args, **kwargs):
        super(WelcomeWidget, self).__init__(*args, **kwargs)
        layout = QtWidgets.QHBoxLayout()

        view = QtWebEngineWidgets.QWebEngineView()
        view.load(QtCore.QUrl("http://openmodal.com/draft/alpha_greeting.html"))

        self.label = QtWidgets.QLabel('Welcome')
        self.label.setObjectName('big')
        # font = self.label.font()
        # font.setPointSize(25)
        # font.setFamily('Verdana')
        # self.label.setFont(font)
        self.label.setContentsMargins(15, 50, 50, 50)

        global_layout = QtWidgets.QVBoxLayout()
        # global_layout.addWidget(self.label)
        # global_layout.addStretch(1)

        choices_layout = QtWidgets.QVBoxLayout()

        self.button_start = QtWidgets.QPushButton(qta.icon('fa.rocket', color='white', scale_factor=1.2), 'New')
        self.button_start.setObjectName('altpushbutton')
        self.button_start.clicked.connect(self.action_new)

        # self.button_open_project = QtGui.QPushButton(qta.icon('fa.folder-open', color='white', active='fa.folder-open', color_active='white', scale_factor=1.2), 'Open')
        self.button_open_project = QtWidgets.QPushButton(qta.icon('fa.folder-open', color='white', scale_factor=1.2), 'Open')
        self.button_open_project.setObjectName('altpushbutton')
        self.button_open_project.clicked.connect(self.action_open)

        self.button_open_help = QtWidgets.QPushButton(qta.icon('fa.life-saver', color='#d35400'), 'Help')
        self.button_open_help.setObjectName('linkbutton')
        self.button_open_help.clicked.connect(lambda: view.load(QtCore.QUrl("http://openmodal.com/draft/first_steps.html")))
        # self.button_open_project.setMinimumHeight(40)
        # self.button_open_project.setMaximumHeight(40)
        choices_layout.addWidget(self.button_start)
        choices_layout.addWidget(self.button_open_project)
        # choices_layout.addStretch(1)
        choices_layout.addWidget(self.button_open_help)
        choices_layout.addStretch()
        choices_layout.setContentsMargins(20, 0, 20, 20)

        h_layout = QtWidgets.QHBoxLayout()
        # h_layout.addStretch()
        h_layout.addLayout(choices_layout)
        # h_layout.addStretch()
        view.setMinimumWidth(1000)
        # view.setMaximumWidth(1000)
        # h_layout.addStretch()
        h_layout.addWidget(view)
        # h_layout.addStretch()
        global_layout.setContentsMargins(50, 50, 50, 50)

        global_layout.addLayout(h_layout)
        # global_layout.addStretch()


        # layout.addWidget(view)
        self.setLayout(global_layout)

    def reload(self, *args, **kwargs):
        # Nothing so far
        pass
