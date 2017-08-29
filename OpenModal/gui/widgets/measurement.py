
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

import time

from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd
import pyqtgraph as pg
import pyqtgraph.dockarea as da
from pyqtgraph.dockarea.Dock import DockLabel
import qtawesome as qta
import numpy as np


#import modal_testing as mt
import OpenModal.gui.widgets.prototype as prototype
import OpenModal.keys as kkeys


try:
    import OpenModal.DAQTask as dq
    import daqprocess as dp
except NotImplementedError as nie:
    dp = None
    dq = None
import OpenModal.frf as frf
import OpenModal.gui.templates as temp
from OpenModal.meas_check import overload_check, double_hit_check

FONT_TABLE_FAMILY = 'Consolas'
FONT_TABLE_SIZE = 13
ACTIVE_FIELDS = ['rsp_node', 'rsp_dir', 'ref_node', 'ref_dir']


from OpenModal.preferences import DEFAULTS


# Monkey patch for accessing dock tab label css.

def updateStylePatched(self):
    r = '3px'
    if self.dim:
        # fg = '#b0b0b0'
        # fg = temp.COLOR_PALETTE['primary']
        fg = 'black'
        # fg = 'gray'
        # bg = '#94f5bb'
        # bg = temp.COLOR_PALETTE['hover']
        bg = 'lightgray'
        # border = temp.COLOR_PALETTE['hover']
        border = 'lightgray'
        # border = '#7cf3ac'
    else:
        fg = '#fff'
        # fg = temp.COLOR_PALETTE['primary']
        # bg = '#10b151'
        bg =  temp.COLOR_PALETTE['primary']
        border =  temp.COLOR_PALETTE['primary']

    if self.orientation == 'vertical':
        self.vStyle = """DockLabel {
            background-color : %s;
            color : %s;
            border-top-right-radius: 0px;
            border-top-left-radius: %s;
            border-bottom-right-radius: 0px;
            border-bottom-left-radius: %s;
            border-width: 0px;
            border-right: 2px solid %s;
            padding-top: 3px;
            padding-bottom: 3px;
            font-size: 18px;
        }""" % (bg, fg, r, r, border)
        self.setStyleSheet(self.vStyle)
    else:
        self.hStyle = """DockLabel {
            background-color : %s;
            color : %s;
            border-top-right-radius: %s;
            border-top-left-radius: %s;
            border-bottom-right-radius: 0px;
            border-bottom-left-radius: 0px;
            border-width: 0px;
            border-bottom: 2px solid %s;
            padding-left: 13px;
            padding-right: 13px;
            font-size: 18px
        }""" % (bg, fg, r, r, border)
        self.setStyleSheet(self.hStyle)


DockLabel.updateStyle = updateStylePatched

class ClockWidget(QtWidgets.QLabel):
    """Digital clock widget."""
    def __init__(self, format='hms'):
        super().__init__()

        # self.setNumDigits(8)
        # self.setSegmentStyle(QtGui.QLCDNumber.Filled)


        self.setStyleSheet('font-size: 20px;')

        self.setText('00:00')

        self.time = QtCore.QTime()
        self.time.start()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.show_time)
        self.timer.start(1000)

        self.show()

    def show_time(self):
        elapsed_time = self.time.elapsed()
        elapsed_time = elapsed_time / 1000
        h = np.floor(elapsed_time/3600)
        m = np.floor(elapsed_time/60) - h*60
        s = np.round(elapsed_time - h*3600 - m*60)
        # text = '{h:02d}:{m:02d}:{s:02d}'.format(h=int(h), m=int(m), s=int(s))
        text = '''{m:02d}:{s:02d}'''.format(h=int(h), m=int(m), s=int(s))

        # self.display(text)
        self.setText(text)

    def reset(self):
        """Reset timer to 0."""
        self.time.restart()


class MeasurementWidget(prototype.SubWidget):
    """Measurement Widget stub."""
    def __init__(self, *args, **kwargs):
        super(MeasurementWidget, self).__init__(*args, **kwargs)

        self.frf_container = None

        self.excitation_type_old = None

        # Set the counter for generating new measurement_ids.
        if self.modaldata.tables['measurement_index'].shape[0] == 0:
            self.measurement_id = 0
        else:
            self.measurement_id = self.modaldata.tables['measurement_index'].measurement_id.max() + 1

        # TODO: Make this into a function. Create in in templates or somewhere
        self.colors = ['#f39c12', '#d35400', '#c0392b', '#16a085', '#27ae60',
                       '#2980b9', '#8e44ad', '#f39c12', '#d35400', '#c0392b',
                       '#16a085', '#27ae60', '#2980b9', '#8e44ad']


        self.stop_routine = lambda: None

        # TODO: IZKLOPI SORTIRANJE TABELE. Pozabil zakaj to ni dobro ...
        # PyQtGraph - dockarea
        # First dock - measureent.
        self.dock_area = da.DockArea()
        self.dock_area.setStyleSheet('background: white;')
        self.dock_measurement = da.Dock('Measurement')
        graphics_view_measurement = pg.GraphicsView()
        self.fig_exc = pg.PlotWidget(name='Measurement - Excitation')
        self.fig_resp = pg.PlotWidget(name='Measurement - Response')
        self.fig_exc_zoom = pg.PlotWidget(name='Measurement - Respsadonse')
        self.fig_exc_frq = pg.PlotWidget(name='Measurement - Resasdponse')
        layout_measurement = QtWidgets.QGridLayout()
        layout_measurement.addWidget(self.fig_exc, 0, 0)
        layout_measurement.addWidget(self.fig_resp, 0, 1)
        layout_measurement.addWidget(self.fig_exc_zoom, 1, 0)
        layout_measurement.addWidget(self.fig_exc_frq, 1, 1)
        graphics_view_measurement.setLayout(layout_measurement)
        self.dock_measurement.addWidget(graphics_view_measurement)

        # Second dock - estimators.
        self.dock_estimators = da.Dock('Estimators (Frequency-domain)')
        graphics_view_measurement = pg.GraphicsView()
        # TODO: Pass just the curve object? Otherwise - problems ahead.
        # TODO: Give info on the graph, such as zero-padding ...
        self.fig_h_mag = pg.PlotWidget(name='Estimator H1 - Magnitude')
        self.fig_h_mag.setLogMode(x=None, y=True)
        self.fig_h_phi = pg.PlotWidget(name='Estimator H1 - Phase')
        self.fig_h_mag.setXLink(self.fig_h_phi)
        layout_estimators = QtWidgets.QGridLayout()
        layout_estimators.addWidget(self.fig_h_mag, 0, 0)
        layout_estimators.addWidget(self.fig_h_phi, 1, 0)
        graphics_view_measurement.setLayout(layout_estimators)
        self.dock_estimators.addWidget(graphics_view_measurement)

        # Third dock - time domain data.
        self.dock_area.addDock(self.dock_measurement, 'left')
        self.dock_area.addDock(self.dock_estimators, 'right')
        # self.dock_area.show()
        # self.dock_area.addDock(self.dock_estimators, 'below', self.dock_measurement)
        #, self.dock_estimators)

        # self.dock_area.moveDock(self.dock_measurement, 'top', self.dock_estimators)
        # self.dock_area_state = self.dock_area.saveState()
        self.legend = self.fig_resp.addLegend()

        # buttons
        # Check if any models exist.
        self.modaldata.tables['info'].sort_values('model_id', inplace=True)
        models = self.modaldata.tables['info'].model_name

        ICON_SIZE = 24

        self.button_model = QtWidgets.QComboBox()
        self.button_model.setObjectName('small')
        self.button_model.addItems(models.values)
        self.button_model.currentIndexChanged.connect(self.update_table_model_id)
        self.button_model.currentIndexChanged.connect(lambda: self.settings.update({'selected_model_id': self.button_model.currentIndex()}))
        # self.button_model.setFixedHeight(ICON_SIZE + 6)

        self.button_roving = QtWidgets.QComboBox()
        self.button_roving.setObjectName('small')
        self.button_roving.addItems(['Ref. node', 'Resp. node'])
        # self.button_roving.setDisabled(True)
        self.button_roving.currentIndexChanged.connect(lambda: self.settings.update({'roving_type':self.button_roving.currentText()}))

        if 'Ref. node' in self.settings['roving_type']:
            self.button_roving.setCurrentIndex(0)
        else:
            self.button_roving.setCurrentIndex(1)

        # -- Override and force roving response! (for now)
        # self.button_roving.setCurrentIndex(2)

        roving_label = QtWidgets.QLabel('Roving:')

        self.button_remove_line = QtWidgets.QPushButton('Remove selected')
        self.button_remove_line.setObjectName('small_wide')
        self.button_remove_line.clicked.connect(self.remove_selected)

        self.button_accept_measurement = QtWidgets.QPushButton(qta.icon('fa.check', color='white'), 'Accept')
        self.button_accept_measurement.setObjectName('small')
        self.button_repeat_measurement = QtWidgets.QPushButton(qta.icon('fa.repeat', color='white'), 'Repeat')
        self.button_repeat_measurement.setObjectName('small')

        self.button_accept_measurement.setDisabled(True)
        self.button_repeat_measurement.setDisabled(True)

        main_button_layout = QtWidgets.QVBoxLayout()



        run_icon = qta.icon('fa.play', scale_factor=1.6, color='white')#, active='fa.stop')
        self.button_run = QtWidgets.QPushButton(run_icon, ' Measure')
        self.button_run.setObjectName('altpushbutton_measurement')
        self.button_run.setCheckable(True)
        self.button_run.toggled.connect(self._handle_measurement_button_toggle)
        self.button_repeat_measurement.clicked.connect(self.button_run.toggle)

        if dp is None:
            button_preferences_link = QtWidgets.QPushButton(qta.icon('fa.warning', scale_factor=0.8,
                                                                 color='red'),
                                                                'Install DAQmx!')
            button_preferences_link.setObjectName('linkbutton')
            button_preferences_link.setStyleSheet('font-size: xx-small; color: red; text-decoration: none;')
            button_preferences_link.setContentsMargins(0, 0, 0, 0)

        else:
            button_preferences_link = QtWidgets.QPushButton(qta.icon('fa.cogs', scale_factor=0.8,
                                                                 color=temp.COLOR_PALETTE['primaryhex']),
                                                                'configure ...')
            button_preferences_link.setObjectName('linkbutton')
            button_preferences_link.setContentsMargins(0, 0, 0, 0)
            button_preferences_link.clicked.connect(self.open_configuration_window)

        run_button_pair = QtWidgets.QVBoxLayout()
        run_button_pair.setContentsMargins(0, 0, 0, 0)
        run_button_pair.addWidget(self.button_run)
        run_button_pair.addWidget(button_preferences_link)

        node_number_layout = QtWidgets.QGridLayout()
        node_number_layout.setContentsMargins(40, 50, 40, 25)

        idx_m = self.modaldata.tables['measurement_index']
        idx_m = idx_m[idx_m.model_id == self.button_model.currentIndex()]
        val_m = self.modaldata.tables['measurement_values']

        # TODO: Do some smart(er) node (ref/resp) numbering. Connect with geometry.
        if idx_m.shape[0] == 0:
            ref_node = 1
            rsp_node = 1
        else:
            last_line = idx_m.tail(1)

            if 'Ref. node' in self.button_roving.currentText():
                ref_node = last_line.ref_node.values[0] + 1
                rsp_node = last_line.rsp_node.values[0]
            else:
                ref_node = last_line.ref_node.values[0]
                rsp_node = last_line.rsp_node.values[0] + 1


        self.ref_node_spin = QtWidgets.QSpinBox()
        self.ref_node_spin.setValue(ref_node)
        self.ref_node_spin.setMaximumWidth(60)
        self.ref_node_spin.setMaximum(10000)
        self.ref_node_spin.setMinimum(1)
        self.ref_node_check = QtWidgets.QCheckBox()
        ref_node_label = QtWidgets.QLabel('Reference node:')
        self.ref_node_increment = QtWidgets.QComboBox()
        self.ref_node_increment.setObjectName('small')
        self.ref_node_increment.addItems(['increment', 'fixed'])


        node_number_layout.addWidget(roving_label, 0, 0)
        node_number_layout.addWidget(self.button_roving, 0, 2)
        node_number_layout.addWidget(ref_node_label, 1, 0)
        node_number_layout.addWidget(self.ref_node_spin, 1, 2)

        self.resp_node_spin = QtWidgets.QSpinBox()
        self.resp_node_spin.setValue(rsp_node)
        self.resp_node_spin.setMaximumWidth(60)
        self.resp_node_spin.setMaximum(10000)
        self.resp_node_spin.setMinimum(1)
        resp_node_label = QtWidgets.QLabel('Response node:')


        accept_repeat_layout = QtWidgets.QHBoxLayout()
        accept_repeat_layout.addWidget(self.button_accept_measurement)
        accept_repeat_layout.addWidget(self.button_repeat_measurement)
        accept_repeat_layout.setContentsMargins(100, 0, 80, 0)


        node_number_layout.addWidget(resp_node_label, 2, 0)
        node_number_layout.addWidget(self.resp_node_spin, 2, 2)
        # node_number_layout.addLayout(accept_repeat_layout, 2, 1)

        # model_button_layout = QtGui.QHBoxLayout()
        # model_button_layout.setContentsMargins(0, 50, 0, 0)
        model_label = QtWidgets.QLabel('Use model:')
        self.button_model_new = QtWidgets.QPushButton(qta.icon('fa.plus-square', color='white'), '')
        self.button_model_new.setObjectName('small_icon')
        self.button_model_new.clicked.connect(self._add_new_model)
        model_h_layout = QtWidgets.QHBoxLayout()
        model_h_layout.addWidget(self.button_model)
        model_h_layout.addWidget(self.button_model_new)
        node_number_layout.addWidget(model_label, 3, 0)
        # node_number_layout.addWidget(self.button_model, 3, 1)
        # node_number_layout.addWidget(self.button_model_new, 3, 2)
        node_number_layout.addLayout(model_h_layout, 3, 2)

        follow_geometry_label = QtWidgets.QLabel('Follow geometry:')
        self.follow_geometry_check = QtWidgets.QCheckBox()
        node_number_layout.addWidget(follow_geometry_label, 4, 0)
        node_number_layout.addWidget(self.follow_geometry_check, 4, 2, QtCore.Qt.AlignCenter)


        # model_button_layout.addWidget(model_label)
        # model_button_layout.addWidget(self.button_model)
        # model_button_layout.addWidget(self.button_model_new)
        # model_button_layout.addWidget(follow_geometry_label)
        # model_button_layout.setContentsMargins(75, 0, 75, 0)

        # follow_geometry_layout = QtGui.QHBoxLayout()
        # follow_geometry_layout.addWidget(follow_geometry_label)
        # follow_geometry_layout.addWidget(self.follow_geometry_check)
        # follow_geometry_layout.setContentsMargins(150, 0, 150, 0)

        # run_button_layout.addStretch()
        run_button_layout = QtWidgets.QHBoxLayout()
        run_button_layout.setContentsMargins(40, 0, 30, 0)
        run_button_layout.addLayout(run_button_pair)
        main_button_layout.addLayout(run_button_layout)
        main_button_layout.addLayout(node_number_layout)
        main_button_layout.addLayout(accept_repeat_layout)
        main_button_layout.setContentsMargins(10, 10, 10, 30)
        # main_button_layout.addLayout(model_button_layout)
        # main_button_layout.addLayout(follow_geometry_layout)

        # self.failsafe_print_checkbox = QtGui.QCheckBox()
        # self.average_counter = QtGui.QLabel('Pass 0 of 0.')
        self.average_counter = QtWidgets.QLabel('')
        self.average_counter.setStyleSheet('color: black; font-weight: bold;')
        self.average_counter.setMaximumHeight(35)

        self.button_overload = QtWidgets.QLabel("<b>Overload!</b>")
        # self.button_overload.setStyleSheet('color: red')
        self.button_overload.setStyleSheet('color: lightgray')
        self.button_overload.setMaximumHeight(35)

        self.button_doublehit = QtWidgets.QLabel("<b>Double hit!</b>")
        # self.button_doublehit.setStyleSheet('color: red')
        self.button_doublehit.setStyleSheet('color: lightgray')
        self.button_doublehit.setMaximumHeight(35)

        button_layout = QtWidgets.QHBoxLayout()

        button_layout.addWidget(self.average_counter)
        button_layout.addStretch()
        button_layout.addWidget(self.button_overload)
        button_layout.addWidget(self.button_doublehit)


        self.button_accept_measurement.clicked.connect(self.confirm_add_to_model)

        self.setup_measurement_thread()

        # Table
        cdf = pd.DataFrame(columns=['None'])
        self.table_model = TableModel(self)
        self.table_model.update(self.modaldata.tables['measurement_index'], self.button_model.currentIndex())
        self.table_view = QtWidgets.QTableView()
        self.table_view.setShowGrid(False)
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        hh = self.table_view.horizontalHeader()
        hh.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        selection = self.table_view.selectionModel()
        selection.selectionChanged.connect(self.view_measurement_frf)

        # self.table_view.clicked.connect(self.view_measurement_frf)

        # table_view.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
        font = QtGui.QFont(FONT_TABLE_FAMILY, FONT_TABLE_SIZE)
        font1 = QtGui.QFont(FONT_TABLE_FAMILY, FONT_TABLE_SIZE, QtGui.QFont.Bold)
        self.table_view.horizontalHeader().setFont(font1)
        self.table_view.setFont(font)
        self.table_view.setAlternatingRowColors(True)
        self.table_view.setSortingEnabled(True)

        self.table_view.setMinimumHeight(150)
        self.table_view.setMinimumWidth(420)
        self.table_view.setMaximumWidth(500)

        h_global_layout = QtWidgets.QHBoxLayout()
        v_global_layout = QtWidgets.QVBoxLayout()
        v_global_layout.addLayout(button_layout)
        v_global_layout.addWidget(self.dock_area)
        h_global_layout.addLayout(v_global_layout)

        dock = QtWidgets.QDockWidget()

        h_table_button_layout = QtWidgets.QHBoxLayout()



        # h_table_button_layout.addLayout(model_button_layout)
        h_table_button_layout.addWidget(self.button_remove_line)

        v_table_layout = QtWidgets.QVBoxLayout()
        v_table_layout.addLayout(main_button_layout)
        v_table_layout.addWidget(self.table_view)
        v_table_layout.addLayout(h_table_button_layout)

        h_global_layout.addLayout(v_table_layout)
        self.setLayout(h_global_layout)

        self.reload()

        self.setContentsMargins(20, 20, 20, 20)

    def view_measurement_frf(self):
        """View measurement results in view_mode."""
        # print(self.table_view.selectedIndexes())
        # row = self.table_view.selectedIndexes()[0].row()
        rows = self.table_view.selectedIndexes()
        df_idx = self.modaldata.tables['measurement_index']

        df = self.modaldata.tables['measurement_values']

        self.fig_h_mag.clear()
        self.fig_h_phi.clear()

        if hasattr(self, 'view_legend_mag'):
            self.view_legend_mag.scene().removeItem(self.view_legend_mag)
        self.view_legend_mag = self.fig_h_mag.addLegend()

        for i, row_ in enumerate(rows):
            row = row_.row()

            # iloc beacuse we are selecting a row, not by index.
            measurement_id = df_idx[df_idx.model_id==self.button_model.currentIndex()].measurement_id.iloc[row]
            legend_entry_values = df_idx[df_idx.model_id==self.button_model.currentIndex()][ACTIVE_FIELDS].iloc[row]
            legend_entry = ' '.join(['{0:.0f}'.format(val) for val in legend_entry_values])
            # self.table_model


            data = df[df.measurement_id == measurement_id].amp.values
            frq = df[df.measurement_id == measurement_id].frq.values
            mag = np.abs(data)
            phi = np.angle(data)

            if i > (len(self.colors)-1):
                i_color = i - len(self.colors)
            else:
                i_color = i

            self.fig_h_mag.plot(frq, mag, pen=pg.mkPen({'color': self.colors[i_color]}),
                                name='{0}'.format(legend_entry))
            self.fig_h_phi.plot(frq, phi, pen=pg.mkPen({'color': self.colors[i_color]}))


    def _handle_measurement_button_toggle(self):

        if dp is None:
            msgBox = QtWidgets.QMessageBox()
            msgBox.setWindowTitle('DAQmx not found')
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
            msgBox.setText('Looks like DAQmx is not installed on your system. Plese install the'
                           ' DAQmx drivers and restart OpenModal.')
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.exec_()

            self.button_run.blockSignals(True)
            self.button_run.toggle()
            self.button_run.blockSignals(False)
        elif not ('task_name' in self.settings):
            msgBox = QtWidgets.QMessageBox()
            msgBox.setWindowTitle('Missing data')
            msgBox.setIcon(QtWidgets.QMessageBox.Information)
            msgBox.setText('Looks like there are no hardware interfaces configured. Plese do so using the'
                           ' preferences menu.')
            connectButton = msgBox.addButton(self.tr('Take me to preferences'), QtWidgets.QMessageBox.ActionRole)
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Cancel)
            ret = msgBox.exec_()

            if msgBox.clickedButton() == connectButton:
                self.open_configuration_window()

            self.button_run.blockSignals(True)
            self.button_run.toggle()
            self.button_run.blockSignals(False)

            return False
        else:
            if self.button_run.isChecked():
                # Start measurement.
                print ('Started measurement.')
                print ('checked state:', self.button_run.isChecked())
                self.start_measurement()
                self.button_run.setIcon(qta.icon('fa.stop', color='white', scale_factor=1.6))
                self.button_run.setText(' Stop')
            else:
                # Stop measurement.
                print('Stopping measurement.')
                print ('checked state:', self.button_run.isChecked())
                self.stop_routine()
                self.button_run.setIcon(qta.icon('fa.play', color='white', scale_factor=1.6))
                self.button_run.setText(' Measure')

    def _add_new_model(self):
        # pop dialog window.
        dialog = QtWidgets.QDialog()
        dialog.setWindowTitle('New Model')

        input_layout = QtWidgets.QHBoxLayout()
        model_name_edit = QtWidgets.QLineEdit()
        rxval = QtGui.QRegExpValidator(QtCore.QRegExp('[A-Za-z_-][A-Za-z0-9_- ]{2,20}'))
        model_name_edit.setValidator(rxval)
        model_name_label = QtWidgets.QLabel('Model name')
        input_layout.addWidget(model_name_label)
        input_layout.addWidget(model_name_edit)

        button_layout = QtWidgets.QHBoxLayout()
        button_ok = QtWidgets.QPushButton('Accept')
        button_ok.setDefault(True)
        button_ok.setDisabled(True)
        button_ok.clicked.connect(dialog.accept)
        button_cancel = QtWidgets.QPushButton('Dismiss')
        button_cancel.clicked.connect(dialog.reject)
        button_layout.addWidget(button_cancel)
        button_layout.addWidget(button_ok)

        def check():
            if model_name_edit.hasAcceptableInput():
                button_ok.setEnabled(True)
            else:
                button_ok.setDisabled(True)

        model_name_edit.textEdited.connect(check)


        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(input_layout)
        layout.addLayout(button_layout)
        dialog.setLayout(layout)
        accepted = dialog.exec_()

        if accepted:
            self.modaldata.new_model(entries=dict(model_name=model_name_edit.text()))
            self.reload()
            self.button_model.setCurrentIndex(self.button_model.count()-1)
        else:
            self.button_model.setCurrentIndex(self.button_model.currentIndex())



    def update_table_model_id(self):
        try:
            model_id = self.modaldata.tables['info'].model_id.values[self.button_model.currentIndex()]
        except IndexError:
            model_id = self.modaldata.tables['info'].model_id.min()
        self.table_model.update(self.modaldata.tables['measurement_index'], model_id)

        idx_m = self.modaldata.tables['measurement_index']
        idx_m = idx_m[idx_m.model_id == self.button_model.currentIndex()]
        val_m = self.modaldata.tables['measurement_values']

        # TODO: Do some smart(er) node (ref/resp) numbering. Connect with geometry.
        if idx_m.shape[0] == 0:
            ref_node = 1
            rsp_node = 1
        else:
            last_line = idx_m.tail(1)

            if self.button_roving.currentIndex() == 0:
                ref_node = last_line.ref_node.values[0] + 1
                rsp_node = last_line.rsp_node.values[0]
            else:
                ref_node = last_line.ref_node.values[0]
                rsp_node = last_line.rsp_node.values[0] + 1

        self.ref_node_spin.setValue(ref_node)
        self.resp_node_spin.setValue(rsp_node)

    def reload(self, *args, **kwargs):
        """Called when data is loaded/imported."""
        selected_model_id = self.settings['selected_model_id']

        if 'task_name' in self.settings:
            try:
                i = dq.DAQTask(self.settings['task_name'])
            except dq.DAQError:
                del self.settings['task_name']

        # Update models list.
        self.modaldata.tables['info'].sort_values('model_id', inplace=True)
        models = self.modaldata.tables['info'].model_name
        # old_model_index = self.button_model.currentIndex()
        self.button_model.clear()
        self.button_model.addItems(models.values)
        self.button_model.setCurrentIndex(selected_model_id)
        # self.button_model.setCurrentIndex(old_model_index)

        self.button_overload.setStyleSheet('color: lightgray')
        self.button_doublehit.setStyleSheet('color: lightgray')

        try:
            model_id = self.modaldata.tables['info'].model_id.values[self.button_model.currentIndex()]
        except IndexError:
            model_id = self.modaldata.tables['info'].model_id.min()
        self.table_model.update(self.modaldata.tables['measurement_index'], model_id)

        # Update with preferences also.
        # TODO: Check which channel is the excitation channel.
        # TODO: Pull correct units!
        units_glossary = dict(a=['Acceleration','g', 'Acceleration PSD', 'g^2/Hz'],
                              v=['Velocity','m/s', 'Velocity PSD', '(m/s)^2/Hz'],
                              d=['Displacement', 'mm', 'Displacement PSD', 'mm^2/Hz'],
                              e=['Strain', '/', 'Strain PSD', '(/)^2/Hz'],
                              f=['Force', 'N', 'Force PSD', 'N^2/Hz'],
                              mixed=['Mixed', 'mixed', 'Mixed PSD', 'mixed^2/Hz'])

        exc_idx = self.settings['exc_channel']
        units_exc_idx = self.settings['channel_types'][exc_idx]
        self.fig_exc.setLabel('left', units_glossary[units_exc_idx][0], units=units_glossary[units_exc_idx][1])
        self.fig_exc.setLabel('bottom', 'Time', units='s')

        # -- Check units consistency.
        response_indices = self.settings['resp_channels']
        channel_types = [self.settings['channel_types'][idx] for idx in response_indices]
        if channel_types[1:] == channel_types[:-1]:
            # units are consistent
            units_resp_idx = channel_types[0]
        else:
            units_resp_idx = 'mixed'

        # resp_idx = self.settings['resp_channels'][0]
        # units_resp_idx = self.settings['channel_types'][resp_idx]
        self.fig_resp.setLabel('left', units_glossary[units_resp_idx][0], units=units_glossary[units_resp_idx][1])
        self.fig_resp.setLabel('bottom', 'Time', units='s')

        if self.settings['excitation_type'] != self.excitation_type_old:
            print('Exc type changed')
            # -- Only do this if excitation type was changed. See self.open_configuration_window(...)
            if self.settings['excitation_type'] == 'impulse':
                # Prepare for impulse measurement.
                self.dock_area.moveDock(self.dock_measurement, 'top', self.dock_estimators)#, self.dock_estimators)
                self.dock_area.moveDock(self.dock_estimators, 'bottom', self.dock_measurement)#, self.dock_estimators)
                self.excitation_type_old = 'impulse'
                self.average_counter.setText('')
            elif self.settings['excitation_type'] == 'random' or self.settings['excitation_type'] == 'oma':
                # Prepare for random measurement.
                self.dock_area.moveDock(self.dock_estimators, 'above', self.dock_measurement)
                self.excitation_type_old = self.settings['excitation_type']
                self.average_counter.setText('Pass 0 of {0}'.format(self.settings['n_averages']))
                # self.clock.show()
            else:
                raise ValueError('Wrong excitation type.')

        # -- Set axes labels and units.
        self.fig_h_mag.setXLink(self.fig_h_phi)

        self.fig_exc_zoom.setLabel('left', units_glossary[units_exc_idx][0], units=units_glossary[units_exc_idx][1])
        self.fig_exc_zoom.setLabel('bottom', 'Time - Zoom', units='s')

        self.fig_exc_frq.setLabel('left', units_glossary[units_exc_idx][2], units=units_glossary[units_exc_idx][3])
        self.fig_exc_frq.setLabel('bottom', 'Frequency', units='Hz')

        self.fig_h_mag.setLabel('bottom', 'Frequency', units='Hz')
        self.fig_h_mag.setLabel('left', units_glossary[units_resp_idx][2], units=units_glossary[units_resp_idx][3])
        self.fig_h_phi.setLabel('bottom', 'Frequency', units='Hz')
        self.fig_h_phi.setLabel('left', 'Phase', units='rad')

        # TODO: What about coherence? lejterzzz
        # self.fig_h_mag.showAxis('right')

        if 'Ref. node' in self.settings['roving_type']:
            self.button_roving.setCurrentIndex(0)
        else:
            self.button_roving.setCurrentIndex(1)

    def refresh(self, *args, **kwargs):
        self.reload(*args, **kwargs)

    def remove_selected(self):
        """Remove selected rows."""
        # First, get measurement IDs (unique for that table) for the selected rows.
        # measurement_ids = [self.modaldata.tables['measurement_index'].iloc[model.row()].measurement_id
        #                    for model in self.table_view.selectedIndexes()]

        current_index = self.button_model.currentIndex()
        model_id = self.modaldata.tables['info'].model_id.values[current_index]
        active_data = self.modaldata.tables['measurement_index'][self.modaldata.tables['measurement_index'].model_id == model_id]
        measurement_ids = [active_data.iloc[model.row()].measurement_id
                           for model in self.table_view.selectedIndexes()]

        # Then remove from measurement_index and measurement_values at that same measurement_id.
        self.modaldata.tables['measurement_index'] = self.modaldata.tables['measurement_index'][~self.modaldata.tables['measurement_index'].measurement_id.isin(measurement_ids)]
        self.modaldata.tables['measurement_values'] = self.modaldata.tables['measurement_values'][~self.modaldata.tables['measurement_values'].measurement_id.isin(measurement_ids)]
        self.modaldata.tables['measurement_values_td'] = self.modaldata.tables['measurement_values_td'][~self.modaldata.tables['measurement_values_td'].measurement_id.isin(measurement_ids)]

        self.reload()

        self.button_model.setCurrentIndex(current_index)


    def setup_measurement_thread(self):
        """Prepare for measurement."""
        # self.process = mt.Impact()
        if dp is None:
            class Empty(object):
                def stop_process(self):
                    pass
            self.process = Empty()

            return False
        self.process = dp.MeasurementProcess()
        self.process.start_process()
        def stop_measurement_button_routine():
            # self.process.run_flag.value = False
            self.process.stop_measurement()
            self.timer.stop()
            # self.button_save_raw.setEnabled(True)

        self.stop_routine = stop_measurement_button_routine

    def start_measurement(self):
        """Start measuring."""
        self.button_accept_measurement.setDisabled(True)
        self.button_repeat_measurement.setDisabled(True)

        self.button_doublehit.setStyleSheet('color: lightgray')
        self.button_overload.setStyleSheet('color: lightgray')

        # -- Initialize plots.
        self.fig_exc.clear()
        self.fig_resp.clear()
        self.fig_exc_zoom.clear()
        self.fig_exc_frq.clear()

        self.fig_h_mag.clear()
        self.fig_h_phi.clear()
        if hasattr(self, 'view_legend_mag'):
            self.view_legend_mag.scene().removeItem(self.view_legend_mag)
        self.view_legend_mag = self.fig_h_mag.addLegend()

        exc_curve = self.fig_exc.plot(pen=pg.mkPen({'color':'#bdc3c7'}))
        self.fig_exc.enableAutoRange('x', True)
        self.fig_exc.enableAutoRange('y', True)

        if self.settings['excitation_type'] == 'oma':
            self.fig_h_mag_pen = [self.fig_h_mag.plot(pen=pg.mkPen({'color': self.colors[i]})) for i in range(len(self.settings['resp_channels'])+1)]
            self.fig_h_phi_pen = [self.fig_h_phi.plot(pen=pg.mkPen({'color': self.colors[i]})) for i in range(len(self.settings['resp_channels'])+1)]
        else:
            self.fig_h_mag_pen = [self.fig_h_mag.plot(pen=pg.mkPen({'color': self.colors[i]})) for i in range(len(self.settings['resp_channels']))]
            self.fig_h_phi_pen = [self.fig_h_phi.plot(pen=pg.mkPen({'color': self.colors[i]})) for i in range(len(self.settings['resp_channels']))]
        self.fig_exc_zoom_pen = self.fig_exc_zoom.plot()
        self.fig_exc_frq_pen = self.fig_exc_frq.plot()

        self.legend.scene().removeItem(self.legend)
        self.legend = self.fig_resp.addLegend()

        # TODO: Before running the measurement check if everything is set. Make a funkction check_run and put it in __init__.
        nr_ch = len(self.settings['resp_channels'])
        resp_curves = [self.fig_resp.plot(
            pen=pg.mkPen({'color': self.colors[i]}),
            name='Ch {0} - {1}'.format(i, self.settings['channel_names'][self.settings['resp_channels'][i]]))
            for i in range(nr_ch)]

        # resp_curve = self.fig_resp.plot(pen='y')
        self.fig_resp.enableAutoRange('x', True)
        self.fig_resp.enableAutoRange('y', True)

        self.n_averages_done = 0

        # TODO: This must be made into an object. Too much mess using it this way.
        # Plot update function - impulse measurement.
        def plot_impulse(triggered, exc_curve, resp_curve, pipe,
                 exc_channel, resp_channels):
            # mstimehere = time.time()
            plotdata = pipe.recv()
            # mstime, plotdata = pipe.recv()
            resp = plotdata[resp_channels, :]
            exc = plotdata[exc_channel, :]
            exc_curve.setData(self.x_axis, exc)

            # if double_hit_check(exc, self.x_axis[1]-self.x_axis[0]):
            #     self.button_doublehit.setStyleSheet('color: red')
            # else:
            #     self.button_overload.setStyleSheet('color: lightgray')

            if overload_check(exc):
                self.button_overload.setStyleSheet('color: red')
            else:
                self.button_overload.setStyleSheet('color: lightgray')
            # TODO: This should be faster.
            overload_list = []
            for i in range(resp.shape[0]):
                overload_list.append(overload_check(resp[i, :]))
                resp_curve[i].setData(self.x_axis, resp[i, :])
            if True in overload_list:
                self.button_overload.setStyleSheet('color: red')
            else:
                self.button_overload.setStyleSheet('color: lightgray')
            if triggered.value:
                # Stop measurement.
                triggered.value = False
                self.button_run.toggle()

                # Sometimes measurement gives zeros. We have to retry the measurement.
                if exc.sum() == 0.0:
                    self.button_run.toggle()
                else:
                    # Show detailed data for impact type of measurement.
                    self.add_measurement_data(exc, resp)


        def plot_random(triggered, exc_curve, resp_curve, pipe,
                 exc_channel, resp_channels, random_chunk):
            # mstimehere = time.time()
            plotdata = pipe.recv()
            # mstime, plotdata = pipe.recv()
            resp = plotdata[resp_channels, :]
            exc = plotdata[exc_channel, :]
            exc_curve.setData(self.x_axis, exc)
            if overload_check(exc):
                self.button_overload.setStyleSheet('color: red')
            else:
                self.button_overload.setStyleSheet('color: lightgray')
            # TODO: This should be faster.
            # print('Now drawing')
            overload_list = []
            for i in range(resp.shape[0]):
                overload_list.append(overload_check(resp[i, :]))
                resp_curve[i].setData(self.x_axis, resp[i, :])
            if True in overload_list:
                self.button_overload.setStyleSheet('color: red')
            else:
                self.button_overload.setStyleSheet('color: lightgray')
            if triggered.value:
                # print('Now Triggered')
                triggered.value = False
                chunk_data = random_chunk.recv()
                resp = chunk_data[resp_channels, :]
                exc = chunk_data[exc_channel, :]
                self.add_measurement_data(exc, resp)
                self.average_counter.setText('Pass {0} of {1}'.format(self.n_averages_done, self.settings['n_averages']))
                if self.n_averages_done >= self.settings['n_averages']:
                    # TODO: Problems when stopping mid-measurement or for short windows!
                    # print(random_chunk.recv())
                    self.button_run.toggle()

        def plot_oma(triggered, exc_curve, resp_curve, pipe,
                 exc_channel, resp_channels, random_chunk):
            # mstimehere = time.time()
            plotdata = pipe.recv()
            # mstime, plotdata = pipe.recv()
            resp = plotdata[resp_channels, :]
            exc = plotdata[exc_channel, :]
            if overload_check(exc):
                self.button_overload.setStyleSheet('color: red')
            else:
                self.button_overload.setStyleSheet('color: lightgray')
            exc_curve.setData(self.x_axis, exc)
            # TODO: This should be faster.
            # print('Now drawing')
            overload_list = []
            for i in range(resp.shape[0]):
                overload_list.append(overload_check(resp[i, :]))
                resp_curve[i].setData(self.x_axis, resp[i, :])
            if True in overload_list:
                self.button_overload.setStyleSheet('color: red')
            else:
                self.button_overload.setStyleSheet('color: lightgray')
            if triggered.value:
                # print('Now Triggered')
                triggered.value = False
                chunk_data = random_chunk.recv()
                resp = chunk_data[:, :]
                exc = chunk_data[exc_channel, :]
                self.add_measurement_data(exc, resp)
                self.average_counter.setText('Pass {0} of {1}'.format(self.n_averages_done, self.settings['n_averages']))
                if self.n_averages_done >= self.settings['n_averages']:
                    # TODO: Problems when stopping mid-measurement or for short windows!
                    # print(random_chunk.recv())
                    self.button_run.toggle()

        # Send over the settings, could be different, could be the same.
        self.process.setup_measurement_parameters(self.settings)
        for key in self.settings:
            self.process.__dict__[key] = self.settings[key]
        self.process.run_measurement()

        sampling_fr = self.process.task_info_out.recv()
        self.x_axis = np.arange(0, self.settings['samples_per_channel']/sampling_fr, 1/sampling_fr)
        self.sampling_fr = sampling_fr

        # Set up and start timed refresh. It must be a child of self (self.timer, not timer) otherwise it is
        # unreferenced instantly.
        self.timer = QtCore.QTimer()

        print(self.settings['channel_delay'])



        if self.settings['excitation_type'] == 'impulse':

            # -- Initialize frf objects. For each channel.
            self.frf_container = [frf.FRF(self.sampling_fr,
                                exc_type=self.settings['channel_types'][self.settings['exc_channel']],
                                resp_type=self.settings['channel_types'][self.settings['resp_channels'][i]],
                                exc_window=self.settings['exc_window'], resp_window=self.settings['resp_window'],
                                resp_delay=self.settings['channel_delay'][self.settings['resp_channels'][i]],
                                fft_len=self.settings['samples_per_channel']+self.settings['zero_padding'],
                                archive_time_data=self.settings['save_time_history']) for
                                i in range(len(self.settings['resp_channels']))]

            # aa = [(self.settings['channel_types'][self.settings['resp_channels'][i]],
            #  self.settings['channel_delay'][self.settings['resp_channels'][i]])
            #  for i in range(len(self.settings['resp_channels']))]
            # print(aa)

            self.timer.timeout.connect(lambda triggered=self.process.triggered, exc_curve=exc_curve, resp_curve=resp_curves,
                                              pipe=self.process.process_measured_data_out,
                                              exc_channel=self.settings['exc_channel'],
                                              resp_channels=self.settings['resp_channels']:
                                              plot_impulse(triggered, exc_curve, resp_curve, pipe, exc_channel, resp_channels))

            self.timer.start(100)

        elif self.settings['excitation_type'] == 'random':

            self.frf_container = [frf.FRF(self.sampling_fr,
                                exc_type=self.settings['channel_types'][self.settings['exc_channel']],
                                resp_type=self.settings['channel_types'][self.settings['resp_channels'][i]],
                                exc_window=self.settings['exc_window'], resp_window=self.settings['resp_window'],
                                resp_delay=self.settings['channel_delay'][self.settings['resp_channels'][i]],
                                weighting=self.settings['weighting'], n_averages=self.settings['n_averages'],
                                fft_len=self.settings['samples_per_channel']+self.settings['zero_padding'],
                                archive_time_data=self.settings['save_time_history']) for
                                i in range(len(self.settings['resp_channels']))]

            self.timer.timeout.connect(lambda triggered=self.process.triggered, exc_curve=exc_curve, resp_curve=resp_curves,
                                              pipe=self.process.process_measured_data_out,
                                              exc_channel=self.settings['exc_channel'],
                                              resp_channels=self.settings['resp_channels'],
                                              random_chunk=self.process.process_random_chunk_out:
                                              plot_random(triggered, exc_curve, resp_curve, pipe, exc_channel, resp_channels,
                                                          random_chunk))



            self.timer.start(1000)

        elif self.settings['excitation_type'] == 'oma':

            self.frf_container = [frf.FRF(self.sampling_fr,
                                exc_type=self.settings['channel_types'][self.settings['exc_channel']],
                                resp_type=self.settings['channel_types'][i],
                                exc_window=self.settings['exc_window'], resp_window=self.settings['resp_window'],
                                resp_delay=self.settings['channel_delay'][i],
                                weighting=self.settings['weighting'], n_averages=self.settings['n_averages'],
                                fft_len=self.settings['samples_per_channel']+self.settings['zero_padding'],
                                archive_time_data=self.settings['save_time_history']) for
                                i in range(len(self.settings['resp_channels'])+1)]

            self.timer.timeout.connect(lambda triggered=self.process.triggered, exc_curve=exc_curve, resp_curve=resp_curves,
                                              pipe=self.process.process_measured_data_out,
                                              exc_channel=self.settings['exc_channel'],
                                              resp_channels=self.settings['resp_channels'],
                                              random_chunk=self.process.process_random_chunk_out:
                                              plot_oma(triggered, exc_curve, resp_curve, pipe, exc_channel, resp_channels,
                                                          random_chunk))



            self.timer.start(1000)

    def add_measurement_data(self, excitation, response):
        """Show appropriate data when the trigger is tripped and add it to database."""
        # Do calculations.
        # print(self.settings['exc_window'], self.settings['resp_window'])
        # TODO: Different response types not implemented (all must me of same type now).
        # Show data.
        # self.h_container = []
        # self.excitation_container = []
        # self.response_container = []
        if self.settings['excitation_type'] == 'oma':
            print('drawing oma')
            for i in range(len(self.settings['resp_channels'])+1):
                resp_1 = self.frf_container[i]

                resp_1.add_data(excitation, response[i, :])
                f = resp_1.get_f_axis()
                self.fig_h_mag_pen[i].setData(f, np.abs(resp_1.get_ods_frf()))
                self.fig_h_phi_pen[i].setData(f, np.angle(resp_1.get_ods_frf()))
        else:
            if double_hit_check(excitation, self.x_axis[1]-self.x_axis[0], limit=1e-2):
                self.button_doublehit.setStyleSheet('color: red')
            else:
                self.button_doublehit.setStyleSheet('color: lightgray')
            for i in range(len(self.settings['resp_channels'])):
                resp_1 = self.frf_container[i]

                resp_1.add_data(excitation.copy(), response[i, :].copy())
                f = resp_1.get_f_axis()
                self.fig_h_mag_pen[i].setData(f, np.abs(resp_1.get_H1()))
                self.fig_h_phi_pen[i].setData(f, np.angle(resp_1.get_H1()))


            #self.coherence = pg.ViewBox() # TODO: add coherence plot (when avereging/repetition is done)
            #self.coherence.setRange(rect=None, xRange=None, yRange=(0,1), padding=None, update=True, disableAutoRange=True)
            #self.fig_h_mag.scene().addItem(self.coherence)
            #self.fig_h_mag.getAxis('right').linkToView(self.coherence)
            #def updateViews():
            #    self.coherence.setGeometry(self.fig_h_mag.plotItem.vb.sceneBoundingRect())
            #    self.coherence.linkedViewChanged(self.fig_h_mag.plotItem.vb, self.coherence.XAxis)
            #updateViews()
            #self.fig_h_mag.plotItem.vb.sigResized.connect(updateViews)
            #self.coherence.setXLink(self.fig_h_mag)
            #self.fig_h_mag.getAxis('right').setLabel('Coherence')
            #self.coherence.addItem(pg.PlotWidget().plot(f, resp_1.get_coherence()))

            # self.h_container.append(resp_1.get_H1())

            # if self.button_save_raw.isChecked():
            # self.excitation_container.append(excitation)
            # self.response_container.append(response[i, :])
        self.n_averages_done += 1
        self.frq_axis = f

        zoom = int(np.floor(self.settings['samples_per_channel']*0.1))
        self.fig_exc_zoom_pen.setData(self.x_axis[:zoom], excitation[:zoom])
        # impulse_fft = np.fft.fft(excitation)
        # f_impulse = np.fft.fftfreq(self.x_axis.size)
        # TODO: Below is impulse frequency transform. Is it correct?
        self.fig_exc_frq_pen.setData(f, 2 * np.abs(resp_1.Exc * resp_1.Exc.conj()))

        if self.settings['weighting'] == 'None':
            self.button_accept_measurement.setEnabled(True)
            self.button_repeat_measurement.setEnabled(True)
        elif self.settings['n_averages'] == self.n_averages_done:
            self.button_accept_measurement.setEnabled(True)
            self.button_repeat_measurement.setEnabled(True)

    def confirm_add_to_model(self):
        """If the measurement is ok (user/machine decides), it is added to
        the modeldata object. The measurement then continues."""
        # self.modaldata.tables['measurement_index'][ACTIVE_FIELDS] = self.table_model.datatable
        # TODO: Not perfect.
        model_id = self.modaldata.tables['info'].model_id.values[self.button_model.currentIndex()]

        idx_m = self.modaldata.tables['measurement_index']
        idx_m = idx_m[idx_m.model_id == model_id]
        val_m = self.modaldata.tables['measurement_values']

        # TODO: Do some smart(er) node (ref/resp) numbering. Connect with geometry.
        if idx_m.shape[0] == 0:
            ref_dir = 1
            rsp_dir = 1
        else:
            last_line = idx_m.tail(1)

            # If there is a multiaxial measurement, consider all the dofs being measured simultaneously.
            if len(self.settings['resp_channels']) > 1:
                rsp_dir = 1
            else:
                rsp_dir = last_line.rsp_dir.values[0]
            ref_dir = last_line.ref_dir.values[0]

        ref_node = self.ref_node_spin.value()
        rsp_node = self.resp_node_spin.value()

        if 'Ref. node' in self.button_roving.currentText():
            self.ref_node_spin.setValue(self.ref_node_spin.value()+1)
        else:
            self.resp_node_spin.setValue(self.resp_node_spin.value()+1)



        if self.settings['save_time_history']:
            self.button_run.setDisabled(True)
            self.button_accept_measurement.setDisabled(True)
            self.button_repeat_measurement.setDisabled(True)

            self.status_bar.setBusy('time_save')

            def endimport():
            # Put everything in its place and update table.
                self.button_run.setEnabled(True)
                model_id = self.modaldata.tables['info'].model_id.values[self.button_model.currentIndex()]
                self.table_model.update(self.modaldata.tables['measurement_index'], model_id)
                self.button_run.toggle()

                self.status_bar.setNotBusy('time_save')
                # self.status_bar.setProgressBarBusy(False)
                # self.status_bar.hideProgressBar()
                # self.status_bar.showMessage('<b>Ready.</b>')

            class IOThread(QtCore.QThread):

                def __init__(self, modaldata, model_id, frq_axis, x_axis, rsp_node, rsp_dir, ref_node, ref_dir, frf_container, exc_type, zero_padding):
                    super().__init__()

                    self.modaldata_object = modaldata

                    self.model_id = model_id
                    self.frq_axis = frq_axis
                    self.x_axis = x_axis
                    self.rsp_node = rsp_node
                    self.rsp_dir = rsp_dir
                    self.ref_node = ref_node
                    self.ref_dir = ref_dir
                    self.frf_container = frf_container
                    self.excitation_type = exc_type
                    self.zero_padding = zero_padding

                def run(self):
                    for frf in self.frf_container:
                        # TODO: Optimize saving in modaldata.
                        if self.excitation_type == 'oma':
                            self.modaldata_object.new_measurement(self.model_id, self.excitation_type, self.frq_axis, frf.get_ods_frf(), reference=[self.ref_node, self.ref_dir],
                                                               response=[self.rsp_node, self.rsp_dir], function_type='Frequency Response Function',
                                                               abscissa='frequency', ordinate='acceleration',
                                                               denominator='excitation force', zero_padding=self.zero_padding, td_x_axis=self.x_axis,
                                                               td_excitation=frf.exc_archive,
                                                               td_response=frf.resp_archive)
                        else:
                            self.modaldata_object.new_measurement(self.model_id, self.excitation_type, self.frq_axis, frf.get_H1(), reference=[self.ref_node, self.ref_dir],
                                                               response=[self.rsp_node, self.rsp_dir], function_type='Frequency Response Function',
                                                               abscissa='frequency', ordinate='acceleration',
                                                               denominator='excitation force', zero_padding=self.zero_padding, td_x_axis=self.x_axis,
                                                               td_excitation=frf.exc_archive,
                                                               td_response=frf.resp_archive)
                        if self.rsp_dir == 3:
                            self.rsp_dir = 1
                            self.rsp_node += 1
                        else:
                            self.rsp_dir += 1

            self.thread = IOThread(self.modaldata, model_id, self.frq_axis, self.x_axis, rsp_node, rsp_dir, ref_node,
                                   ref_dir, self.frf_container, self.settings['excitation_type'], self.settings['zero_padding'])
            self.thread.finished.connect(endimport)
            self.thread.start()


        else:
            if self.settings['excitation_type'] == 'oma':
                print('adding oma')
                for frf in self.frf_container:
                    self.modaldata.new_measurement(model_id, self.settings['excitation_type'], self.frq_axis, frf.get_ods_frf(), reference=[ref_node, ref_dir],
                                                   response=[rsp_node, rsp_dir], function_type='Frequency Response Function',
                                                   abscissa='frequency', ordinate='acceleration',
                                                   denominator='excitation force', zero_padding=self.settings['zero_padding'])

                    if rsp_dir == 3:
                        rsp_dir = 1
                        rsp_node += 1
                    else:
                        rsp_dir += 1
            else:
                for frf in self.frf_container:
                    self.modaldata.new_measurement(model_id, self.settings['excitation_type'], self.frq_axis, frf.get_H1(), reference=[ref_node, ref_dir],
                                                   response=[rsp_node, rsp_dir], function_type='Frequency Response Function',
                                                   abscissa='frequency', ordinate='acceleration',
                                                   denominator='excitation force', zero_padding=self.settings['zero_padding'])

                    if rsp_dir == 3:
                        rsp_dir = 1
                        rsp_node += 1
                    else:
                        rsp_dir += 1


            # Put everything in its place and update table.
            model_id = self.modaldata.tables['info'].model_id.values[self.button_model.currentIndex()]
            self.table_model.update(self.modaldata.tables['measurement_index'], model_id)
            self.button_run.toggle()


    def open_configuration_window(self):
        """Configure excitation method."""
        self.preferences_window.setWindowModality(QtCore.Qt.ApplicationModal)
        self.preferences_window.setWindowTitle('Configure Measurement')

        self.preferences_window.show()

        self.preferences_window.save.clicked.connect(self.reload)

    def closeEvent(self, *args, **kwargs):
        self.process.stop_process()


# A quick and dirty dictionary, thats needed to show the user
# x for 1, y for 2 and z for 3. On the other hand, the x/y/z
# need to be converted before they are input into table.

axes_dict = {1:'x', 2:'y', 3:'z'}
axes_dict_oposite = {'x': 1, 'X': 1,
                     'y': 2, 'Y': 2,
                     'z': 3, 'Z': 3}

class TableModel(QtCore.QAbstractTableModel):
    '''Table model that suits all tables (for now). It specifies
    access to data and some other stuff.'''
    # TODO: x -> 1 ...

    def __init__(self, parent, *args):
        super(TableModel, self).__init__(parent, *args)
        self.datatable = None

    def update(self, dataIn, model_id):
        self.layoutAboutToBeChanged.emit()
        self.dataIn = dataIn
        # self.datatable = dataIn[dataIn.model_id == model_id]
        self.datatable = self.dataIn[dataIn.model_id == model_id][ACTIVE_FIELDS]
        # self.datatable = self.datatable
        # print(self.dataIn[dataIn.model_id == model_id])
        # print('buu')
        # print(self.dataIn[dataIn.model_id == model_id][ACTIVE_FIELDS])
        # self.dataChanged.emit(0,0)
        self.layoutChanged.emit()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.datatable.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.datatable.columns.values)

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return kkeys.keys[self.datatable.columns[col]]['15']
        return None

    def setData(self, index, value, role):
        row = self.datatable.index[index.row()]
        col = self.datatable.columns[index.column()]
        if hasattr(value, 'toPyObject'):
            # Only for PyQt4? (QVariant)
            value = value.toPyObject()
        # else:
        #     # Only for PyQt4? (Unicode)
        #     dtype = self.datatable[col].dtype
        #     if dtype != object:
        #         value = None if value == '' else dtype.type(value)

        try:
            col_ = index.column()
            if (col_ == 1) or (col_ == 3):
                value = axes_dict_oposite[value]
            try:
                value = int(value)
                self.datatable.set_value(row, col, int(value))
                self.dataIn.update(self.datatable)
            except ValueError:
                pass
        # self.maintable[ACTIVE_FIELDS] = self.datatable

        # self.emit(QtCore.pyqtSignal("dataChanged()"))

        except (TypeError, KeyError) as e:
            # Wrong data type.
            pass

        # self.dataChanged.emit(0, 0)
        return True

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if role == QtCore.Qt.TextAlignmentRole:
            return QtCore.Qt.AlignCenter
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None

        i = index.row()
        j = index.column()
        if (j == 1) or (j == 3):
            idx = self.datatable.iat[i, j]
            return axes_dict[idx]
        else:
            return '{:.0f}'.format(self.datatable.iat[i, j])

    def sort(self, col, order):
        """sort table by given column number col"""
        self.layoutAboutToBeChanged.emit()
        if order == QtCore.Qt.DescendingOrder:
            self.datatable = self.datatable.sort_values(self.datatable.columns[col], ascending=0)
        else:
            self.datatable = self.datatable.sort_values(self.datatable.columns[col])
        self.layoutChanged.emit()

    def flags(self, index):
        return QtCore.QAbstractTableModel.flags(self, index) | QtCore.Qt.ItemIsEditable


class PicButton(QtWidgets.QAbstractButton):
    def __init__(self, pixmap, parent=None):
        super(PicButton, self).__init__(parent)
        self.pixmap = pixmap

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(event.rect(), self.pixmap)

    def sizeHint(self):
        return self.pixmap.size()

if __name__ == '__main__':
    import sys
    import modaldata
    app = QtWidgets.QApplication(sys.argv)

    main_window = MeasurementWidget(modaldata, status_bar=None)
    main_window.setGeometry(100, 100, 640, 480)
    main_window.show()

    sys.exit(app.exec_())
