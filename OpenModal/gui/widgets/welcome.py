__author__ = 'Matjaz'

from PyQt4 import QtGui, QtCore, QtWebKit
# from PyQt4 import QtGui, QtCore, QtWebKit

import qtawesome as qta

import OpenModal.gui.widgets.prototype as prototype

import OpenModal.gui.templates as templ


class WelcomeWidget(prototype.SubWidget):
    """Welcome widget stub."""
    def __init__(self, *args, **kwargs):
        super(WelcomeWidget, self).__init__(*args, **kwargs)
        layout = QtGui.QHBoxLayout()

        view = QtWebKit.QWebView()
        view.load(QtCore.QUrl("http://openmodal.com/draft/alpha_greeting.html"))
        view.setContentsMargins(100, 200, 100, 200)
        # view.setStyleSheet('border: 1px solid black;')

        self.label = QtGui.QLabel('Welcome')
        self.label.setObjectName('big')
        # font = self.label.font()
        # font.setPointSize(25)
        # font.setFamily('Verdana')
        # self.label.setFont(font)
        self.label.setContentsMargins(15, 50, 50, 50)

        global_layout = QtGui.QVBoxLayout()
        # global_layout.addWidget(self.label)
        # global_layout.addStretch(1)

        choices_layout = QtGui.QVBoxLayout()

        self.button_start = QtGui.QPushButton(qta.icon('fa.rocket', color='white', scale_factor=1.2), 'New')
        self.button_start.setObjectName('altpushbutton')
        self.button_start.clicked.connect(self.action_new)

        # self.button_open_project = QtGui.QPushButton(qta.icon('fa.folder-open', color='white', active='fa.folder-open', color_active='white', scale_factor=1.2), 'Open')
        self.button_open_project = QtGui.QPushButton(qta.icon('fa.folder-open', color='white', scale_factor=1.2), 'Open')
        self.button_open_project.setObjectName('altpushbutton')
        self.button_open_project.clicked.connect(self.action_open)

        self.button_open_help = QtGui.QPushButton(qta.icon('fa.life-saver', color='#d35400'), 'Help')
        self.button_open_help.setObjectName('linkbutton')
        self.button_open_help.clicked.connect(lambda: view.load(QtCore.QUrl("http://openmodal.com/draft/help_404.html")))
        # self.button_open_project.setMinimumHeight(40)
        # self.button_open_project.setMaximumHeight(40)
        choices_layout.addWidget(self.button_start)
        choices_layout.addWidget(self.button_open_project)
        # choices_layout.addStretch(1)
        choices_layout.addWidget(self.button_open_help)
        choices_layout.addStretch()
        choices_layout.setContentsMargins(20, 0, 20, 20)

        h_layout = QtGui.QHBoxLayout()
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