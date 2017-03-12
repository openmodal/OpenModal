
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

import sys, subprocess, os

try:
    import DAQTask as dq
    import daqprocess as dp
except NotImplementedError as nie:
    dq = None
    dp = None
from string import Template

import qtawesome as qta

# import DAQTask as dq

from PyQt5 import QtCore, QtGui, QtWidgets

import pyqtgraph as pg

import numpy as np


from OpenModal.gui.templates import COLOR_PALETTE


MAX_WINDOW_LENGTH = 1e9

class ExportSelector(QtWidgets.QWidget):
    """Measurement configuration window.
    """
    def __init__(self, desktop_widget, status_bar, modaldata_object, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.status_bar = status_bar
        self.modaldata_object = modaldata_object
        self.desktop_widget = desktop_widget

        self.data_types_list = ['nodes', 'lines', 'elements', 'measurements', 'analyses']
        self.data_types_names = ['Nodes', 'Lines', 'Elements', 'Measurements', 'Analysis results']

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.white)
        self.setPalette(p)

        self.setAutoFillBackground(True)
        self.fields = dict()

        self.save = QtWidgets.QPushButton('Done')
        self.save.setObjectName('small')
        # self.save.setDisabled(True)

        self.dismiss = QtWidgets.QPushButton('Dismiss')
        self.dismiss.setObjectName('small')

        self.setGeometry(400, 50, 600, 800)
        self.setContentsMargins(25, 0, 25, 25)

        with open('gui/styles/style_template.css', 'r', encoding='utf-8') as fh:
            src = Template(fh.read())
            src = src.substitute(COLOR_PALETTE)
            self.setStyleSheet(src)

        hbox = QtWidgets.QHBoxLayout()
        # hbox.addWidget(self.left_menu)

        title_label = QtWidgets.QLabel('EXPORT DATA')
        font = title_label.font()
        font.setPointSize(8)
        font.setFamily('Verdana')
        title_label.setFont(font)
        title_label.setContentsMargins(5, 0, 0, 25)
        title_label.setObjectName('title_label')

        models_group = QtWidgets.QGroupBox('Models')
        models_group.setStyleSheet("QGroupBox {font-weight: bold;}")
        models_grid = QtWidgets.QGridLayout()
        models_grid.setContentsMargins(80, 20, 80, 20)
        models_grid.setColumnStretch(1, 0)
        models_grid.setColumnStretch(1, 2)

        self.model_db = self.modaldata_object.tables['info']

        models = ['{0} {1:.0f}'.format(model, model_id) for model, model_id in
                  zip(self.model_db.model_name, self.model_db.model_id)]

        # models = ['Nosilec', 'Transformator', 'Jedro', 'Pralni stroj', 'Letalo']

        self.model_checkbox_widgets = [QtWidgets.QCheckBox() for model in models]
        model_label_widgets = [QtWidgets.QLabel(model) for model in models]

        for i, (checkbox, label) in enumerate(zip(self.model_checkbox_widgets,model_label_widgets)):
            models_grid.addWidget(checkbox, i//2, 0 + (i%2)*2)
            models_grid.addWidget(label, i//2, 1 + (i%2)*2, alignment=QtCore.Qt.AlignLeft)
            checkbox.setChecked(True)

        models_group.setLayout(models_grid)

        data_type_group = QtWidgets.QGroupBox('Data')
        data_type_group.setStyleSheet("QGroupBox {font-weight: bold;}")
        data_type_grid = QtWidgets.QGridLayout()
        data_type_grid.setContentsMargins(80, 20, 80, 20)
        data_type_grid.setColumnStretch(1, 0)
        data_type_grid.setColumnStretch(1, 2)

        data_types_keys = ['geometry', 'lines', 'elements_index', 'measurement_index', 'analysis_index']
        data_types_populated = [True if self.modaldata_object.tables[key].size != 0 else False
                                for key in data_types_keys]

        self.data_type_checkbox_widgets = [QtWidgets.QCheckBox() for data_type in self.data_types_names]
        model_label_widgets = [QtWidgets.QLabel(data_type) for data_type in self.data_types_names]

        for i, (checkbox, label) in enumerate(zip(self.data_type_checkbox_widgets,model_label_widgets)):
            data_type_grid.addWidget(checkbox, i, 0)
            data_type_grid.addWidget(label, i, 1, alignment=QtCore.Qt.AlignLeft)
            if data_types_populated[i]:
                checkbox.setChecked(True)

        data_type_group.setLayout(data_type_grid)

        other_group = QtWidgets.QGroupBox('Separate Files for Data Types (UFF)')
        other_group.setStyleSheet("QGroupBox {font-weight: bold;}")

        one_file_radio = QtWidgets.QRadioButton()
        self.multiple_file_radio = QtWidgets.QRadioButton()
        one_file_radio_label = QtWidgets.QLabel('No')
        multiple_file_radio_label = QtWidgets.QLabel('Yes')
        one_file_radio.setChecked(True)

        h_files = QtWidgets.QGridLayout()
        h_files.setContentsMargins(80, 20, 80, 20)
        h_files.setColumnStretch(1, 0)
        h_files.setColumnStretch(1, 2)
        h_files.addWidget(self.multiple_file_radio, 0, 0)
        h_files.addWidget(multiple_file_radio_label, 0, 1)
        h_files.addWidget(one_file_radio, 0, 2)
        h_files.addWidget(one_file_radio_label, 0, 3)

        other_group.setLayout(h_files)

        button_export_xls = QtWidgets.QPushButton(qta.icon('fa.line-chart', color='white', scale_factor=1.2),
                                              ' Export CSV')
        button_export_xls.setObjectName('altpushbutton_')
        button_export_xls.clicked.connect(self.ExportCSV)
        button_export_xls_hbox = QtWidgets.QHBoxLayout()
        button_export_xls_hbox.addStretch()
        button_export_xls_hbox.addWidget(button_export_xls)
        button_export_xls_hbox.addStretch()

        button_export_unv = QtWidgets.QPushButton(qta.icon('fa.rocket', color='white', scale_factor=1.2),
                                              ' Export UFF')
        button_export_unv.setObjectName('altpushbutton_')
        button_export_unv.clicked.connect(self.ExportUff)
        button_export_unv_hbox = QtWidgets.QHBoxLayout()
        button_export_unv_hbox.addStretch()
        button_export_unv_hbox.addWidget(button_export_unv)
        button_export_unv_hbox.addStretch()

        title_layout = QtWidgets.QHBoxLayout()
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addLayout(title_layout)
        vbox.setContentsMargins(0, 1, 0, 0)
        vbox.addLayout(hbox)
        vbox.addWidget(models_group)
        vbox.addWidget(data_type_group)
        vbox.addWidget(other_group)
        vbox.addStretch()
        vbox.addLayout(button_export_xls_hbox)
        vbox.addLayout(button_export_unv_hbox)
        vbox.addStretch()
        # button_layout = QtGui.QHBoxLayout()
        # button_layout.addStretch()
        # button_layout.addWidget(self.save)
        # button_layout.addWidget(self.dismiss)

        # vbox.addStretch()
        # vbox.addLayout(button_layout)
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

    def ExportUff(self):
        """ File dialog for exporting uff files. """
        # if variant == 'PySide':
        #     file_name, filtr = QtGui.QFileDialog.getSaveFileName(self, self.tr("Choose Folder"), "/.",
        #                                                      QtGui.QFileDialog.Directory)
        # elif variant == 'PyQt4':

        file_name = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Directory')

        # file_name = QtGui.QFileDialog.getSaveFileName(self, self.tr("Chose Folder"), "/.",
        #                                                  QtGui.QFileDialog.Directory)

        self.exportfile = file_name

        model_ids = [model_id for model_id, check_box_field in zip(self.model_db.model_id, self.model_checkbox_widgets)
                     if check_box_field.isChecked()]

        data_types = [data_type for data_type, check_box_field in
                      zip(self.data_types_list, self.data_type_checkbox_widgets) if check_box_field.isChecked()]

        separate_files_flag = self.multiple_file_radio.isChecked()

        print(model_ids)

        self.status_bar.setBusy('root', 'exporting')

        class IOThread(QtCore.QThread):

            def __init__(self, modaldata, file_name, model_ids=[], data_types=[], separate_files_flag=False):
                super().__init__()

                self.modaldata_object = modaldata
                self.file_name = file_name
                self.model_ids = model_ids
                self.data_types = data_types
                self.separate_files_flag = separate_files_flag

            def run(self):
                self.modaldata_object.export_to_uff(self.file_name, self.model_ids, self.data_types, self.separate_files_flag)

        self.thread = IOThread(self.modaldata_object, file_name, model_ids, data_types, separate_files_flag)
        self.thread.finished.connect(lambda: self.status_bar.setNotBusy('root'))
        self.thread.start()
        self.hide()

    def ExportCSV(self):
        """ File dialog for exporting uff files. """
        # if variant == 'PySide':
        #     file_name, filtr = QtGui.QFileDialog.getSaveFileName(self, self.tr("Select Directory"), "/.",
        #                                                      QtGui.QFileDialog.Directory)
        # elif variant == 'PyQt4':

        file_name = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Directory')

        # file_name = QtGui.QFileDialog.getSaveFileName(self, self.tr("Chose Folder"), "/.",
        #                                                  QtGui.QFileDialog.Directory)

        self.exportfile = file_name

        model_ids = [model_id for model_id, check_box_field in zip(self.model_db.model_id, self.model_checkbox_widgets)
                     if check_box_field.isChecked()]

        data_types = [data_type for data_type, check_box_field in
                      zip(self.data_types_list, self.data_type_checkbox_widgets) if check_box_field.isChecked()]

        print(model_ids)

        self.status_bar.setBusy('root', 'exporting')


        class IOThread(QtCore.QThread):

            def __init__(self, modaldata, file_name, model_ids=[], data_types=[]):
                super().__init__()

                self.modaldata_object = modaldata
                self.file_name = file_name
                self.model_ids = model_ids
                self.data_types = data_types

            def run(self):
                self.modaldata_object.export_to_csv(self.file_name, self.model_ids, self.data_types)

        self.thread = IOThread(self.modaldata_object, file_name, model_ids, data_types)
        self.thread.finished.connect(lambda: self.status_bar.setNotBusy('root'))
        self.thread.start()
        self.hide()
