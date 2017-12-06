
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

import pickle
import sys, time
from string import Template

from PyQt5 import QtCore, QtGui, QtWidgets

import qtawesome as qta

from OpenModal.gui.widgets.welcome import WelcomeWidget
from OpenModal.gui.widgets.geometry import GeometryWidget
from OpenModal.gui.widgets.measurement import MeasurementWidget
from OpenModal.gui.widgets.animation import AnimationWidget
from OpenModal.gui.widgets.analysis import IdentificationWidget


# dodal miha ---------
from OpenModal.gui.widgets.languages import LANG_DICT
import locale

import pyqtgraph
# -------------------
import OpenModal.modaldata as modaldata

from OpenModal.preferences import DEFAULTS

import OpenModal.gui.preferences_window as cf

import OpenModal.gui.export_window as ew

from OpenModal.gui.templates import COLOR_PALETTE, LIST_FONT_FAMILY, LIST_FONT_SIZE, MENUBAR_WIDTH

# TODO: Sort out file loading/saving and widget management!

MAIN_WINDOW_TITLE = 'Sample GUI'
_FRAME_SIZE = (1500, 950)
# LIST_FONT_FAMILY = 'Consolas'
# LIST_FONT_SIZE = 10
#
# MENUBAR_WIDTH = 110
#
# _COLOR_PALETTE_ORANGE = dict(primary='#d35400', hover='#e67e22')
# _COLOR_PALETTE_BW = dict(primary='#333333', hover='#666666')
#
# COLOR_PALETTE = _COLOR_PALETTE_ORANGE

##### ADD YOUR WIDGET HERE (menuitems)
menu_items = ['Geometry',
              'Measurement',
              'Animation',
              'Identification']

icons = ['gui/icons/geometry_big.png',
         'gui/icons/measurement_3.png',
         'gui/icons/Icon_animation_widget.png',
         'gui/icons/analysis_4.png']

##### ADD YOUR WIDGET HERE! (widget classes)
widgets = {0: WelcomeWidget,
           1: GeometryWidget,
           2: MeasurementWidget,
           3: IdentificationWidget,
           4: AnimationWidget}

widgets_names = {0: 'Welcome',
                 1: 'Geometry',
                 2: 'Measurement',
                 3: 'Identification',
                 4: 'Animation'}

# TODO: Height of sidebar should be fixed in the upper region not bottom.
# TODO: Big problems. App does not always close.
pyqtgraph.setConfigOptions(antialias=True)
pyqtgraph.setConfigOption('background', 'w')
pyqtgraph.setConfigOption('foreground', 'k')

# TODO: Put it inside a thread.
class StatusWidget(QtWidgets.QWidget):
    """Custom statusbar widget.
    """
    def __init__(self):
        super(StatusWidget, self).__init__()

        self.button_weird = QtWidgets.QPushButton(' ready')
        self.button_weird.setObjectName('linkbutton')
        self.spin_icon = qta.icon('fa.spinner', color='red', animation=qta.Spin(self.button_weird))
        self.button_weird.setIcon(self.spin_icon)

        self.label = QtWidgets.QLabel('busy')
        self.label.setObjectName('small')
        self.label.setStyleSheet('color: {0};'.format(COLOR_PALETTE['primary']))
        self.label_mov = QtWidgets.QLabel()
        self.movie = QtGui.QMovie('gui/icons/loader-ring.gif')
        self.movie.setScaledSize(QtCore.QSize(20,20))
        self.label_mov.setMovie(self.movie)
        self.movie.start()
        self.label_mov.hide()

        status_layout = QtWidgets.QHBoxLayout()
        status_layout.addWidget(self.label_mov)
        status_layout.addWidget(self.label)

        self.setLayout(status_layout)

        self.active_identities = dict(root=(0, 'ready'))
        self.last_identity = 'root'

        # self._refresh_status()

    def _refresh_status(self):
        status_all = sum([value[0] for key, value in self.active_identities.items()])
        last_id_msg = self.active_identities[self.last_identity][1]
        if status_all > 0:
            self.label.setText(last_id_msg)
            self.label_mov.show()
        else:
            self.label.setText(last_id_msg)
            self.label_mov.hide()

    def setBusy(self, identity, msg='busy'):
        """Set progress bar into busy mode."""
        self.active_identities[identity] = (1, msg)
        self._refresh_status()

    def setNotBusy(self, identity, msg='ready'):
        """Set progress bar into busy mode."""
        self.active_identities[identity] = (0, msg)
        self._refresh_status()

class AboutWindow(QtWidgets.QWidget):
    """Measurement configuration window.
    """
    def __init__(self):
        super(AboutWindow, self).__init__()

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.white)
        self.setPalette(p)

        self.setAutoFillBackground(True)
        self.fields = dict()

        self.dismiss = QtWidgets.QPushButton('Dismiss')
        self.dismiss.setObjectName('small')
        self.dismiss.clicked.connect(self.close)

        self.main_area = QtWidgets.QWidget()

        self.main_description = QtWidgets.QLabel('''
OpenModal

OpenModal is an open source program for performing experimental modal analysis from data aquisition to mode animation.

Version: Alpha
Date: July 2016
Team: Matjaž Mršnik, Blaž Starc, Miha Pirnat, Janko Slavič'''


                             )
        self.webpage = QtWidgets.QLabel('''Webpage: <a href='http://openmodal.com'>OpenModal</a>''')
        self.webpage.setOpenExternalLinks(True)
        self.main_description.setWordWrap(True)
        # self.main_description.setFixedSize(550, 500)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.main_description)
        layout.addWidget(self.webpage)

        self.main_area.setLayout(layout)

        self.setGeometry(200, 150, 500, 700)
        self.setContentsMargins(25, 0, 25, 25)

        with open('gui/styles/style_template.css', 'r', encoding='utf-8') as fh:
            src = Template(fh.read())
            src = src.substitute(COLOR_PALETTE)
            self.setStyleSheet(src)

        title_label = QtWidgets.QLabel('ABOUT')
        font = title_label.font()
        font.setPointSize(8)
        font.setFamily('Verdana')
        title_label.setFont(font)
        title_label.setContentsMargins(5, 0, 0, 25)
        title_label.setObjectName('title_label')


        title_layout = QtWidgets.QHBoxLayout()
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(title_layout)
        vbox.setContentsMargins(0, 1, 0, 0)
        vbox.addWidget(self.main_area)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.dismiss)

        self.channel_nr = 0

        vbox.addLayout(button_layout)
        vbox.setContentsMargins(20, 20, 20, 20)

        vbox_outer = QtWidgets.QVBoxLayout()
        vbox_outer.setContentsMargins(0, 0, 0, 0)
        vbox_outer.addLayout(vbox)
        vbox_outer.addWidget(QtWidgets.QSizeGrip(self.parent()), 0, QtCore.Qt.AlignBottom |QtCore.Qt.AlignRight)

        self.setContentsMargins(0, 0, 0, 0)
        self.setLayout(vbox_outer)

    def paintEvent(self, event):

        self.painter = QtGui.QPainter()
        self.painter.begin(self)

        self.painter.setBrush(QtCore.Qt.white)
        self.painter.setPen(QtCore.Qt.lightGray)

        # .. Draw a rectangle around the main window.
        self.painter.drawRect(0, 0, self.width()-1, self.height()-1)

        # self.painter.drawLine(300, 180, 300, self.height())
        # Top ribbon
        # rect = self.painter.drawRect(0, 0, self.width()-1, 30)
        self.painter.fillRect(QtCore.QRect(1, 1, self.width()-2, 40), QtGui.QColor(245, 245, 245))

        pen = QtGui.QPen()
        pen.setWidth(2)
        pen.setBrush(QtCore.Qt.gray)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setJoinStyle(QtCore.Qt.RoundJoin)
        self.painter.setPen(pen)
        # close cross
        self.painter.drawLine(self.width() - 30, 30, self.width() - 10, 10)
        self.painter.drawLine(self.width() - 30, 10, self.width() - 10, 30)

        self.painter.end()

    def mouseMoveEvent(self, event):
        if event.buttons() and QtCore.Qt.LeftButton:
            self.move(event.globalPos() - self.mouse_drag_position)
            event.accept()

    def mousePressEvent(self, event):

        add = 0

        if event.button() == QtCore.Qt.LeftButton:
            if (event.pos().x() < (self.width() - 10 - add)) and (event.pos().x() > (self.width()-30-add))\
                    and (event.pos().y() < (30+add)) and (event.pos().y() > (10+add)):
                self.close()

            self.mouse_drag_position = event.globalPos() - self.frameGeometry().topLeft()

class FramelesContainer(QtWidgets.QMainWindow):

    def __init__(self, desktop_widget):
        super().__init__()

        self.desktop_widget = desktop_widget

        # -- Calculate dimensions the main window should have.
        available_screen = self.desktop_widget.availableGeometry()
        screen_width = available_screen.width()
        screen_height = available_screen.height()
        if (screen_width / screen_height) < 1.51:
            self.app_dimensions = (available_screen.width()-50, available_screen.height()-50)
        else:
            self.app_dimensions = (available_screen.width()-200, available_screen.height()-100)

        #self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.resize(*self.app_dimensions)
        self.setWindowTitle('OpenModal')
        self.margins = True
        # self.setContentsMargins(50, 50,50, 50)
        self.setContentsMargins(0, 0,0, 0)
        self.main_app = MainApp(desktop_widget, self.frameGeometry, self)

        self.setCentralWidget(self.main_app)

        with open('gui/styles/style_template.css', 'r', encoding='utf-8') as fh:
            src = Template(fh.read())
            src = src.substitute(COLOR_PALETTE)
            self.setStyleSheet(src)

    def resizeEvent(self, event):
        if self.margins:
            pass
        else:
            # self.setContentsMargins(50, 50, 50, 50)
            self.setContentsMargins(0, 0, 0, 0)
            self.margins = True

    def mouseMoveEvent(self, event):
        if event.buttons() and QtCore.Qt.LeftButton:
            if not self.margins:
                self.resize(*self.app_dimensions)
            self.move(event.globalPos() - self.mouse_drag_position)
            # TODO: Think about this accept below!
            event.accept()

    def mousePressEvent(self, event):
        if self.margins:
            add = 50
            add = 0
        else:
            add = 0

        if event.button() == QtCore.Qt.LeftButton:
            if (event.pos().x() < (self.width() - 10 - add)) and (event.pos().x() > (self.width()-30-add))\
                    and (event.pos().y() < (30+add)) and (event.pos().y() > (10+add)):
                self.close()

            if (event.pos().x() < (self.width() - 40 - add)) and (event.pos().x() > (self.width()-60-add))\
                    and (event.pos().y() < (30+add)) and (event.pos().y() > (10+add)):
                if self.margins:
                    rect = self.desktop_widget.availableGeometry(self)
                    self.setContentsMargins(0, 0, 0, 0)
                    self.setGeometry(rect)
                    self.margins = False
                else:
                    self.resize(*self.app_dimensions)

                # self.showFullScreen()

            if (event.pos().x() < (self.width() - 70 - add)) and (event.pos().x() > (self.width()-90-add))\
                    and (event.pos().y() < (30+add)) and (event.pos().y() > (10+add)):
                # TODO: Window goes to sleep (or sth.) here. FIX!
                self.setWindowState(QtCore.Qt.WindowMinimized)
                self.activateWindow()

            self.mouse_drag_position = event.globalPos() - self.frameGeometry().topLeft()

    # def keyPressEvent(self, event):
    #     if event.key() == QtCore.Qt.Key_Escape:
    #         self.close()

    def closeEvent(self, event):
        child_response = self.main_app.main_window.closeEvent(event)

        if child_response:
            event.ignore()
        else:
            event.accept()

class MainApp(QtWidgets.QWidget):

    def __init__(self, desktop_widget, frameGeometry, main_window_handle):
        super().__init__()
        # self.size_grip = QtGui.QSizeGrip(self.parent())

        self.main_window = MainWindow(desktop_widget, frameGeometry, main_window_handle)
        self.setAutoFillBackground(True)
        self.box = QtWidgets.QHBoxLayout()
        self.box.setContentsMargins(0, 0, 0, 0)
        self.box.setSpacing(0)
        self.box.addWidget(self.main_window)
        self.main_window.setContentsMargins(0,0,0,0)
        # self.main_window.setContentsMargins(50,50,50,50)
        # self.box.addWidget(QtGui.QSizeGrip(self.parent()), 0, QtCore.Qt.AlignBottom |QtCore.Qt.AlignRight)

        # self.size_grip.move(100, 100)
        # self.size_grip.raise_()
        # self.size_grip.topLevelWidget()
        # self.size_grip.setStyleSheet('bakcground-color:red;')

        # self.setCentralWidget(self.main_window)
        self.setLayout(self.box)

        # TODO: WTF.
        # self.main_window.setContentsMargins(25, 25, 25, 25)


        # self.shadow = QtGui.QGraphicsDropShadowEffect()
        # self.shadow.setBlurRadius(50)
        # self.setGraphicsEffect(self.shadow)

        self.setContentsMargins(0, 0, 0, 0)

    def paintEvent(self, event):

        self.painter = QtGui.QPainter()
        self.painter.begin(self)

        self.painter.setBrush(QtCore.Qt.white)
        self.painter.setPen(QtCore.Qt.lightGray)

        # .. Draw a rectangle around the main window.
        self.painter.drawRect(0, 0, self.width()-1, self.height()-1)

        # self.painter.drawLine(300, 180, 300, self.height())
        # Top ribbon
        # rect = self.painter.drawRect(0, 0, self.width()-1, 30)
        self.painter.fillRect(QtCore.QRect(0, 0, self.width()-1, 40), QtGui.QColor(245, 245, 245))
        # self.painter.fillRect(QtCore.QRect(0, 0, self.width()-1, 40), QtGui.QColor(100, 100, 100))

        # pen = QtGui.QPen()
        # pen.setWidth(0)
        # pen.setBrush(QtGui.QColor(205, 201, 201))
        #
        # self.painter.setPen(pen)
        # self.painter.drawLine(0, 40, self.width()-1, 40)

        pen = QtGui.QPen()
        pen.setWidth(2)
        pen.setBrush(QtCore.Qt.gray)
        pen.setCapStyle(QtCore.Qt.RoundCap)
        pen.setJoinStyle(QtCore.Qt.RoundJoin)
        self.painter.setPen(pen)
        # close cross
        self.painter.drawLine(self.width() - 30, 30, self.width() - 10, 10)
        self.painter.drawLine(self.width() - 30, 10, self.width() - 10, 30)

        # maximize
        self.painter.drawLine(self.width() - 60, 10, self.width() - 40, 10)
        self.painter.drawLine(self.width() - 60, 30, self.width() - 40, 30)
        self.painter.drawLine(self.width() - 60, 10, self.width() - 60, 30)
        self.painter.drawLine(self.width() - 40, 10, self.width() - 40, 30)

        #minimize
        self.painter.drawLine(self.width() - 90, 30, self.width() - 70, 30)

        # self.size_grip.move(self.width()-1, self.height()-1)

        self.painter.end()


class MainMenuTabbed(QtWidgets.QTabBar):
    def __init__(self):
        super().__init__()

        h_icon = qta.icon('fa.home',scale_factor=1.5,active='fa.legal')
        h_tab = self.addTab(h_icon, 'HOME')
        self.addTab('GEOMETRY  ')
        self.addTab('MEASUREMENT  ')
        self.addTab('ANALYSIS  ')
        self.addTab('ANIMATION  ')
        self.setContentsMargins(0, 0, 0, 0)

class MainMenuDrop(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()

        self.button_go = QtWidgets.QToolButton()
        self.button_go.setIcon(qta.icon('fa.bars', color='white', scale_factor=1.0))
        self.button_go.setMaximumWidth(40)
        self.button_go.setMinimumWidth(40)
        self.button_go.setMinimumHeight(40)
        self.button_go.setMinimumHeight(40)

        self.q_menu = QtWidgets.QMenu()

        with open('gui/styles/style_template.css', 'r', encoding='utf-8') as fh:
            src = Template(fh.read())
            src = src.substitute(COLOR_PALETTE)
            # print (src)
            self.q_menu.setStyleSheet(src)
            # subwindow_menu.setStyleSheet(fh.read())

        self.q_menu.setMinimumWidth(140)
        self.q_menu.setMaximumWidth(140)
        self.button_go.setMenu(self.q_menu)
        self.button_go.setPopupMode(QtWidgets.QToolButton.InstantPopup)

        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.setContentsMargins(0, 0, 0, 0)
        self.hbox.addWidget(self.button_go)

        self.setContentsMargins(0, 0, 0, 0)

        self.setLayout(self.hbox)


class MainMenu(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.button_go = QtWidgets.QToolButton()
        self.button_go.setText('START')
        self.button_go.setMaximumWidth(140)
        self.button_go.setMinimumWidth(140)

        self.q_menu = QtWidgets.QMenu()

        with open('gui/styles/style_template.css', 'r', encoding='utf-8') as fh:
            src = Template(fh.read())
            src = src.substitute(COLOR_PALETTE)
            self.q_menu.setStyleSheet(src)

        self.q_menu.setMinimumWidth(140)
        self.q_menu.setMaximumWidth(140)
        self.button_go.setMenu(self.q_menu)
        self.button_go.setPopupMode(QtWidgets.QToolButton.InstantPopup)


        self.button_open = QtWidgets.QPushButton(qta.icon('fa.folder-open-o'), 'open')
        self.button_open.setObjectName('linkbutton')
        self.button_open.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.button_save = QtWidgets.QPushButton(qta.icon('fa.save'), 'save')
        self.button_save.setObjectName('linkbutton')
        self.button_save.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        # self.button_go.setView(QtGui.QListView())
        # self.button_go.setStyleSheet("QComboBox QAbstractItemView::item { min-height: 35px; min-width: 50px; }");
        self.button_settings = QtWidgets.QPushButton(qta.icon('fa.cogs'), 'settings')
        self.button_settings.setObjectName('linkbutton')
        self.button_settings.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))

        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.addWidget(self.button_go)
        self.hbox.addStretch()
        self.hbox.addWidget(self.button_open)
        self.hbox.addWidget(self.button_save)
        self.hbox.addWidget(self.button_settings)

        self.setLayout(self.hbox)

class MainWindow(QtWidgets.QFrame):
    """Main window of the application.
    """
    def __init__(self, desktop_widget, parent_geometry, main_window_handle):
        """Constructor, builds the GUI."""
        super(MainWindow, self).__init__()
        self.desktop_widget = desktop_widget
        self.parent_geometry = parent_geometry
        self.main_window_handle = main_window_handle

        self.about_window = AboutWindow()

        # -- Create the main, central widget. Inside
        #   are side-menu-bar and stacked widget.

        # search for operating system language and set it as program language
        # dodal miha
        self._lang = self.setLocale()

        self.preferences = DEFAULTS.copy()

        # -- Stacked widget is used to -- stack widgets. In the
        #   beginning the welcome widget is open.
        self.stacked_widget = QtWidgets.QStackedWidget()
        # self.stacked_widget.setContentsMargins(25, 25, 25, 25)
        self.stacked_widget.setContentsMargins(0, 0, 0, 0)

        # .. Opened widgets are put in here.
        self.open_stack = dict()

        # -- Side-menu-bar is made with a QListWidget.
        # thread_status_bar = QtCore.QThread()
        self.status_bar = StatusWidget()

        self.menu = MainMenuTabbed()

        font = self.menu.font()
        font.setPointSize(8)
        font.setFamily('Verdana')
        self.menu.setFont(font)

        self.menu.currentChanged.connect(lambda: self._on_item_clicked(self.menu.currentIndex))

        self.menu_basic = MainMenuDrop()
        self.menu_basic.q_menu.addAction(qta.icon('fa.folder-open', scale_factor=1.0, color='white'), 'Open project', self.Open)
        self.menu_basic.q_menu.addAction('Save as ...', self.SaveAs)
        self.menu_basic.q_menu.addAction(qta.icon('fa.floppy-o', scale_factor=1.0, color='white'), 'Save', self.Save)
        self.menu_basic.q_menu.addSeparator()
        self.menu_basic.q_menu.addAction('Import uff', self.ImportUff)
        # self.menu_basic.q_menu.addAction('Export uff', self.ExportUff)
        self.menu_basic.q_menu.addAction('Export data', self.export_data)
        self.menu_basic.q_menu.addSeparator()
        self.menu_basic.q_menu.addAction(qta.icon('fa.cog', scale_factor=1.0, color='white'), 'Preferences', self.OpenPreferences)
        self.menu_basic.q_menu.addSeparator()
        self.menu_basic.q_menu.addAction(qta.icon('fa.info-circle', scale_factor=1.0, color='white'), 'About', self.about_window.show)
        self.menu_basic.q_menu.addAction('Exit', self.main_window_handle.close)

        self.hmenubox = QtWidgets.QHBoxLayout()
        self.hmenubox.setContentsMargins(0, 0, 0, 0)
        self.hmenubox.setSpacing(0)
        self.hmenubox.addWidget(self.menu_basic)
        self.hmenubox.addStretch(1)
        self.hmenubox.addWidget(self.menu)
        self.hmenubox.addStretch(1)
        self.hmenubox.addWidget(self.status_bar)
        self.hmenubox.addStretch(1)
        self.vbox_gobal = QtWidgets.QVBoxLayout()
        self.vbox_gobal.setContentsMargins(0, 0, 0, 0)
        self.vbox_gobal.setSpacing(0)

        bg_widget = QtWidgets.QWidget()
        bg_widget.setLayout(self.hmenubox)

        bg_widget.setContentsMargins(0,0,0,0)

        self.vbox_gobal.addWidget(bg_widget)

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.vbox.setSpacing(0)
        self.vbox.addWidget(self.stacked_widget)

        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.setContentsMargins(0, 0, 0, 0)
        self.hbox.setSpacing(0)

        self.vbox_left = QtWidgets.QVBoxLayout()
        self.vbox_left.setContentsMargins(0, 0, 0, 0)
        self.vbox_left.setSpacing(0)

        self.hbox.addLayout(self.vbox_left)
        self.hbox.addLayout(self.vbox)

        self.vbox_gobal.addLayout(self.hbox)
        self.vbox_gobal.setContentsMargins(0, 0, 0, 0)
        self.vbox_gobal.setSpacing(0)
        self.setLayout(self.vbox_gobal)

        # -------------------------------------------------------------------------------------------------------Miha
        # self.setGeometry(50, 50, 500, 1200)

        # -- Initialize the data object.
        self.modaldata_object = modaldata.ModalData()

        # -- Save file default.
        self.savefileset = False
        self.savefile = None

        # --Export file default
        self.exportfileset = False
        self.exportfile = None

        self._load_all_widgets()

        # self.setStyleSheet('background-color: red;')
        # self.stacked_widget.setContentsMargins(-10, -10, -10, -10)

        self.overlayed = QtWidgets.QSizeGrip(self)
        # self.overlayed.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        # self.overlayed.setAutoFillBackground(True)
        self.overlayed.setStyleSheet('border-image: url(gui/icons/icon_size_grab_4.png) 0 0 0 0 stretch stretch; border-width: 0px;')
        # self.overlayed.setStyleSheet('background-color: red;')
        # self.overlayed.setMaximumSize(15, 15)
        self.overlayed.resize(15, 15)
        # self.overlayed.move(self.parent_geometry().width()-100, self.parent_geometry().height()-50)
        # self.overlayed.move(self.parent_geometry().width()-200, self.parent_geometry().height()-150)

        self.layout()

    def paintEvent(self, event):

        # self.overlayed.move(self.parent_geometry().width()-15, self.parent_geometry().height()-15)
        self.overlayed.move(self.parent_geometry().width()-15, self.parent_geometry().height()-15)

    def setLocale(self):
        '''
        Get default languge of the operating system

        ...dodal miha

        :return:
        '''
        #TODO: let user select language
        _env=locale.getdefaultlocale()

        if _env[0] in LANG_DICT:
            return _env[0]
        else:
            return 'en_GB'

    def _load_all_widgets(self, current=-1, loading=False):
        """Load all widgets in the background."""
        self.status_bar.setBusy('root')
        if current == -1:
            current = 0
        # Before all widgets and after possible outside data are loaded, check if any models exist.
        # self.modaldata_object.tables['info'].sort('model_id', inplace=True)

        if not loading:
            models = self.modaldata_object.tables['info'].model_name

            if models.size == 0:
                self.modaldata_object.new_model(entries=dict(model_name='NewModel'))

            self.measurement_configuration_window = cf.ExcitationConfig(self.desktop_widget, self.preferences)
            self.export_window = QtWidgets.QWidget()

        for key in widgets.keys():

            if not loading:
                self.open_stack[key] = widgets[key](self.modaldata_object, self.status_bar,
                                                    self._lang, preferences=self.preferences,
                                                    desktop_widget=self.desktop_widget,
                                                    preferences_window=self.measurement_configuration_window,
                                                    action_new=lambda: self.New(loading=True),
                                                    action_open=self.Open)

            else:
                self.open_stack[key].modaldata = self.modaldata_object
                self.open_stack[key].settings = self.preferences

            tic = time.time()
            self.open_stack[key].reload()
            toc = time.time()
            print('{0} update time: {1} seconds'.format(widgets_names[key], toc-tic))



        self.menu.setCurrentIndex(current)
        self._on_item_clicked(self.menu.currentIndex)

        self.status_bar.setNotBusy('root')

    def _on_item_clicked(self, func):
        """React to clicks - open new widgets and set them
        on the top of the stack.
        """
        key = func()
        self.stacked_widget.removeWidget(self.stacked_widget.currentWidget())
        self.stacked_widget.addWidget(self.open_stack[key])
        self.open_stack[key].refresh()
        # self.open_stack[key].wait()
        self.stacked_widget.setCurrentWidget(self.open_stack[key])

        # TODO: Software should automatically check for new version.

    def _warn_about_data_loss(self):
        msgBox = QtWidgets.QMessageBox()
        msgBox.setWindowTitle('Caution')
        msgBox.setIcon(QtWidgets.QMessageBox.Warning)
        msgBox.setText('This action will discard all non-saved data! Are you sure you want to proceed?')
        msgBox.setStandardButtons(QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
        msgBox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
        ret = msgBox.exec_()

        return ret

    def New(self, loading=False):
        """ Create new project."""
        ret = self._warn_about_data_loss()

        if ret == QtWidgets.QMessageBox.Cancel:
            pass
        elif ret == QtWidgets.QMessageBox.Discard:


            # -- Reload stack (__init__).

            # TODO: Widget initialization should be handled in one place! (check __init__)
            #welcome = widgets[0](self.modaldata_object, self.status_bar, self._lang, preferences=self.preferences)
            # welcome = widgets[-1]()
            # for key, widget in self.open_stack.items():
            #     widget.close()

            self.modaldata_object.create_empty()

            self.measurement_configuration_window = None
            self.export_window = None
            self.preferences = dict()

            if loading:
                pass
            else:
                for key, widget in self.open_stack:
                    widget.reload()
                # self._load_all_widgets()

            self.savefileset = False

    def Open(self):
        """File dialog for opening uff files. Updates data object, also updates status bar
        and window title appropriately."""


        ret = self._warn_about_data_loss()

        if ret == QtWidgets.QMessageBox.Cancel:
            pass
        elif ret == QtWidgets.QMessageBox.Discard:


            file_name = QtWidgets.QFileDialog.getOpenFileName(self, self.tr("Open File"), "/.",
                                                          self.tr("ModalData File (*.mdd)"))[0]
            #
            if isinstance(file_name, tuple):  # PySide returns a tuple (name, filtr), while PyQt5 returns only the name
                file_name = file_name[0]      # we only need the file_name

            self.status_bar.setBusy('root')

            class Worker(QtCore.QThread):
                finished = QtCore.pyqtSignal()
                dataout = QtCore.pyqtSignal(object)

                def __init__(self, filename):
                    super().__init__()
                    self.filename = filename

                def run(self):
                    f = open(file_name, 'rb')
                    data = pickle.load(f)

                    self.finished.emit()
                    self.dataout.emit(data)
                    self.exec_()

            self.another_thread = Worker(file_name)
            self.another_thread.start()

            # self.another_thread.finished.connect(lambda: self._load_all_widgets(self.menu.currentIndex(), False))
            self.another_thread.finished.connect(lambda: self.status_bar.setNotBusy('root'))
            self.another_thread.dataout.connect(self._load_data)

    def _load_data(self, data):
        # self.status_bar.setBusy('root')

        # file_name = QtGui.QFileDialog.getOpenFileName(self, self.tr("Open File"), "/.",
        #                                               self.tr("ModalData File (*.mdd)"))

        # if isinstance(file_name, tuple):  # PySide returns a tuple (name, filtr), while PyQt4 returns only the name
        #     file_name = file_name[0]      # we only need the file_name
        #
        # f = open(file_name, 'rb')

        current = self.menu.currentIndex()
        self.modaldata_object, self.preferences = data
        self._load_all_widgets(current, True)


    def SaveAs(self):
        """Save as ... dialog."""
        file_name = QtWidgets.QFileDialog.getSaveFileName(self, self.tr('Save file as'), '/.',
                                                         self.tr('ModalData File (*.mdd)'))[0]

        if isinstance(file_name, tuple):  # PySide returns a tuple (name, filtr), while PyQt5 returns only the name
            file_name = file_name[0]      # we only need the file_name

        self.savefile = file_name

        # TODO: Do special handling for when user exits using X button.
        try:
            self.status_bar.setBusy('root', 'saving ...')

            class IOThread(QtCore.QThread):

                def __init__(self, modaldata, file_name, preferences):
                    super().__init__()

                    self.modaldata_object = modaldata
                    self.file_name = file_name
                    self.preferences = preferences

                def run(self):
                    f = open(self.file_name, 'wb')
                    pickle.dump((self.modaldata_object, self.preferences), f)
                    f.close()

            self.thread = IOThread(self.modaldata_object, file_name, self.preferences)
            self.thread.finished.connect(lambda: self.status_bar.setNotBusy('root'))
            self.thread.start()

            self.savefileset = True
            self.setWindowTitle(self.tr("%s -- %s" % (MAIN_WINDOW_TITLE, self.savefile, )))
        except:
            self.savefileset = False
            # TODO: Popup?
            raise ValueError

    def Save(self):
        """File dialog for saving."""
        if self.savefileset:
            self.status_bar.setBusy('root', 'saving ...')

            class IOThread(QtCore.QThread):
                def __init__(self, modaldata, file_name, preferences):
                    super().__init__()

                    self.modaldata_object = modaldata
                    self.file_name = file_name
                    self.preferences = preferences

                def run(self):
                    f = open(self.file_name, 'wb')
                    pickle.dump((self.modaldata_object, self.preferences), f)
                    f.close()

            self.thread = IOThread(self.modaldata_object, self.savefile, self.preferences)
            self.thread.finished.connect(lambda: self.status_bar.setNotBusy('root'))
            self.thread.start()
            # self.status_bar.setBusy('root', 'saving')
            # f = open(self.savefile, 'wb')
            # pickle.dump((self.modaldata_object, self.preferences), f)
            # f.close()
            # self.status_bar.setNotBusy('root')
        else:
            self.SaveAs()

    # def _start_preferences_window(self):
    #     """Open preferences window."""
    #     # TODO: This should be initialized on application start, same as subwidget. If its called from elswhere, its done through menu? Possible i think.
    #     self.measurement_configuration_window = cf.ExcitationConfig(self.desktop_widget, self.preferences)

    def OpenPreferences(self):
        """Open preferences window."""
        self.measurement_configuration_window.setWindowModality(QtCore.Qt.ApplicationModal)
        self.measurement_configuration_window.setWindowTitle('Preferences')

        self.measurement_configuration_window.show()

        def update_all():
            """Call update on all widgets."""
            for key, widget in self.open_stack.items():
                widget.refresh()

        self.measurement_configuration_window.save.clicked.connect(update_all)


    def ImportUff(self):
        """File dialog for opening uff files. Updates data object, also updates status bar
        and window title appropriately."""
        # if variant == 'PySide':
        #     file_name, filtr = QtGui.QFileDialog.getOpenFileName(self, self.tr("Open File"), "/.",
        #                                     self.tr("Universal File Format (*.uff *.unv *.txt);;"))

        # elif variant == 'PyQt4':
        file_name = QtWidgets.QFileDialog.getOpenFileName(self, self.tr("Open File"), "/.",
                                        self.tr("Universal File Format (*.uff *.unv *.txt);;"))[0]

        if file_name:
            self.status_bar.setBusy('root', 'importing')

            def endimport():
                # -- Update all widgets.
                for key, widget in self.open_stack.items():
                    widget.reload()
                self.status_bar.setNotBusy('root')

            class IOThread(QtCore.QThread):

                def __init__(self, modaldata, file_name):
                    super().__init__()

                    self.modaldata_object = modaldata
                    self.file_name = file_name

                def run(self):
                    self.modaldata_object.import_uff(self.file_name)

            self.thread = IOThread(self.modaldata_object, file_name)
            self.thread.finished.connect(endimport)
            self.thread.start()

    # def ExportUff(self):
    #     """ File dialog for exporting uff files. """
    #     if variant == 'PySide':
    #         file_name, filtr = QtGui.QFileDialog.getSaveFileName(self, self.tr("Export File"), "/.",
    #                                                          self.tr("Universal File Format (*.uff);;"
    #                                                                  "Universal File Format (*.unv)"))
    #     elif variant == 'PyQt4':
    #         file_name = QtGui.QFileDialog.getSaveFileName(self, self.tr("Export File"), "/.",
    #                                                          self.tr("Universal File Format (*.uff);;"
    #                                                                  "Universal File Format (*.unv)"))
    #
    #     self.exportfile = file_name
    #
    #     self.status_bar.setBusy('root', 'exporting')
    #
    #     class IOThread(QtCore.QThread):
    #
    #         def __init__(self, modaldata, file_name):
    #             super().__init__()
    #
    #             self.modaldata_object = modaldata
    #             self.file_name = file_name
    #
    #         def run(self):
    #             self.modaldata_object.export_to_uff(self.file_name)
    #
    #     self.thread = IOThread(self.modaldata_object, file_name)
    #     self.thread.finished.connect(lambda: self.status_bar.setNotBusy('root'))
    #     self.thread.start()

    def export_data(self):
        """Open preferences window."""
        self.export_window = ew.ExportSelector(self.desktop_widget, self.status_bar, self.modaldata_object)

        self.export_window.setWindowModality(QtCore.Qt.ApplicationModal)
        self.export_window.setWindowTitle('Export data')
        self.export_window.show()

    def closeEvent(self, event):
        model_nr = self.modaldata_object.tables['info'].model_id.count()

        if model_nr > 0:
            msgBox = QtWidgets.QMessageBox()
            msgBox.setWindowTitle('Caution')
            msgBox.setIcon(QtWidgets.QMessageBox.Warning)
            msgBox.setText('This action will discard all non-saved data! Are you sure you want to proceed?')
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Close | QtWidgets.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Cancel)
            ret = msgBox.exec_()
        else:
            ret = QtWidgets.QMessageBox.Close

        if ret == QtWidgets.QMessageBox.Cancel:
            event.ignore()
            return True
        elif ret == QtWidgets.QMessageBox.Close:

            self.measurement_configuration_window.closeEvent(event)
            self.export_window.closeEvent(event)
            self.export_window = None

            for key, widget in self.open_stack.items():
                widget.closeEvent(event)

            event.accept()
            return False


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    main_window = FramelesContainer(app.desktop())
    main_window.show()


    sys.exit(app.exec_())
