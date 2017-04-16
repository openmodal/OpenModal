
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


from preferences import DEFAULTS, EXCITATION_DEFAULTS

from frf import _WINDOWS, _EXC_TYPES, _RESP_TYPES, _WGH_TYPES

from OpenModal.gui.templates import COLOR_PALETTE

import OpenModal.gui.tooltips as tt

MAX_WINDOW_LENGTH = 1e9

# TODO: Do a short measurement and then check sampling_rate again (does not work for me --Matjaz).
# TODO: Initialize impulse/random in the begining if it is set already.
# TODO: Disable delay for excitation channel in GUI!


def set_combo_box_index(combo_box, key):
    """Sets dropdown to an index that corresponds with
    the given key."""
    # -- Get all items.
    all_items = [combo_box.itemText(i) for i in range(combo_box.count())]

    # -- Set to index, where key=key.
    return combo_box.setCurrentIndex([i for i, option in enumerate(all_items) if option in key][0])


class ExcitationConfig(QtWidgets.QWidget):
    """Measurement configuration window.
    """
    def __init__(self, desktop_widget, settings=dict()):
        super(ExcitationConfig, self).__init__()

        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.white)
        self.setPalette(p)

        self.setAutoFillBackground(True)
        self.settings = settings
        self.fields = dict()

        self.save = QtWidgets.QPushButton('Done')
        self.save.setObjectName('small')
        self.save.setDisabled(True)
        self.save.clicked.connect(self._save_and_close)

        self.dismiss = QtWidgets.QPushButton('Dismiss')
        self.dismiss.setObjectName('small')
        self.dismiss.clicked.connect(self.close)

        # self.left_menu = self.create_left_menu()
        self.channel_table, self.channel_settings, self.preview_area = self.channels_widget()

        # TODO: Define these in a relative way!
        self.settings_area = QtWidgets.QStackedWidget()
        self.settings_area.setMinimumWidth(450)
        self.settings_area.setMaximumWidth(450)
        self.settings_area.setMinimumHeight(550)
        # self.settings_area.setMaximumHeight(550)
        self.settings_area.addWidget(self.channel_settings)
        self.settings_area.setCurrentWidget(self.channel_settings)

        self.setGeometry(100, 50, 1300, 850)
        self.setContentsMargins(25, 0, 25, 25)

        with open('gui/styles/style_template.css', 'r', encoding='utf-8') as fh:
            src = Template(fh.read())
            src = src.substitute(COLOR_PALETTE)
            self.setStyleSheet(src)


        self.timer = None
        self.fft = False
        self.measure_test_run_process_start()

        hbox = QtWidgets.QHBoxLayout()
        # hbox.addWidget(self.left_menu)
        hbox.addWidget(self.settings_area)
        hbox.addWidget(self.preview_area)

        title_label = QtWidgets.QLabel('PREFERENCES')
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
        vbox.addLayout(hbox)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save)
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

    measurement_type_change = QtCore.pyqtSignal()

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

    def _save(self):
        """Save configuration."""
        # Save channel settings.
        row_nr = self.channel_table.rowCount()

        self.settings['task_name'] = self.device_task.currentText().encode()

        # self.settings['channel_sensitivities'] = []
        self.settings['resp_channels'] = []
        self.settings['exc_channel'] = -1
        self.settings['channel_types'] = []
        self.settings['trigger_level'] = []
        # self.settings['channel_windows'] = []
        self.settings['channel_delay'] = []
        # TODO: Do this different way.
        self.settings['channel_names'] = []
        for i in range(row_nr):
            self.settings['channel_names'].append(self.channel_table.item(i, 0).text())
            if 'Response' in self.channel_table.cellWidget(i, 1).currentText():
                self.settings['resp_channels'].append(i)
            else:
                self.settings['exc_channel'] = i
            self.settings['channel_types'].append(self.channel_table.cellWidget(i, 2).currentText())
            self.settings['trigger_level'] = 500
            # self.settings['channel_windows'].append(self.channel_table.cellWidget(i, 3).currentText())
            self.settings['channel_delay'].append(self.channel_table.cellWidget(i, 3).value()/1000.0)

        # Save general stuff (Acq. settings at the moment) ADD AN ENTRY HERE FOR EACH PROPERTY
        for key in self.fields.keys():
            self.settings[key] = self.fields[key]()
        # self.settings['samples_per_channel'] = int(self.samples_channel_edit.text())
        # self.settings['pre_trigger_samples'] = int(self.pre_trigger_edit.text())

    def _save_and_close(self):
        """Save configuration data and close the window."""
        self._save()
        self.close()

    def show(self):
        super(ExcitationConfig, self).show()

        if self.device_task.currentIndex() != 0:
            self.measure_test_run_process_start()

    def _refresh_tasks_list(self, drop_popup=True):
        # Get tasks
        self.device_task.blockSignals(True)
        tasks_tmp = map(bytes.decode, dq.get_daq_tasks())
        tasks = list(tasks_tmp).copy()

        self.device_task.clear()
        self.device_task.addItem('- Choose task -')
        for item in tasks:
            self.device_task.addItem(item)

        self.device_task.addItem(qta.icon('fa.refresh', scale_factor=0.65, color=COLOR_PALETTE['primaryhex']), 'refresh  ')
        if drop_popup:
            self.device_task.showPopup()

        self.device_task.blockSignals(False)

    def channels_widget(self):
        """Setup device an channels."""
        channel_widget = QtWidgets.QWidget()

        font = QtGui.QFont()
        font.setPointSize(13)

        # Select excitation
        group = QtWidgets.QGroupBox('Excitation Type')
        group.setStyleSheet("QGroupBox {font-weight: bold;}")
        self.radio_impulse = QtWidgets.QRadioButton('Impulse')
        self.radio_impulse.setToolTip(tt.tooltips['impulse_excitation'])

        self.radio_impulse.toggled.connect(self.set_impulse_type)
        # self.settings['excitation_type'] = 'impulse' # TODO: It would be better if just set_impulse_type is called here.

        self.radio_random = QtWidgets.QRadioButton('Random')
        self.radio_random.setToolTip(tt.tooltips['random_excitation'])
        self.radio_random.toggled.connect(self.set_random_type)

        self.radio_oma = QtWidgets.QRadioButton('OMA')
        self.radio_oma.setToolTip(tt.tooltips['OMA_excitation'])
        self.radio_oma.toggled.connect(self.set_oma_type)
        # radio_random.setDisabled(True)
        radio_sweep = QtWidgets.QRadioButton('Sine Sweep')
        self.fields['excitation_type'] = 'impulse'
        # radio_sweep.setDisabled(True)

        group_layout = QtWidgets.QHBoxLayout()
        group_layout.addWidget(self.radio_impulse)
        group_layout.addWidget(self.radio_random)
        group_layout.addWidget(self.radio_oma)
        # group_layout.addWidget(radio_sweep)
        # group_layout.addStretch()

        group.setLayout(group_layout)

        # Get tasks
        # tasks_tmp = map(bytes.decode, dq.get_daq_tasks())
        # tasks = list(tasks_tmp).copy()
        self.device_task = QtWidgets.QComboBox()
        self.device_task.setToolTip(tt.tooltips['signal_selection'])
        self.device_task.setObjectName('small')
        task_status = QtWidgets.QLabel('')

        if (dp is None) or (dq is None):
            warning_label = QtWidgets.QPushButton(qta.icon('fa.warning', scale_factor=0.8,
                                                       color='red'),
                                                      'Install DAQmx, then restart OpenModal!')
            warning_label.setObjectName('linkbutton')
            warning_label.setStyleSheet('font-size: x-small; color: red; text-decoration: none; width:375px;')
            warning_label.setContentsMargins(0, 0, 0, 0)

            signal_hbox = QtWidgets.QHBoxLayout()
            signal_hbox.addStretch()
            signal_hbox.addWidget(warning_label)
            signal_hbox.addStretch()
        else:
            open_ni_max = QtWidgets.QPushButton('NIMax')
            open_ni_max.setToolTip(tt.tooltips['nimax'])
            open_ni_max.setObjectName('small')
            open_ni_max.clicked.connect(lambda:
                                        subprocess.Popen([r'{0}\National Instruments\MAX\NIMax.exe'.format(
                                            os.environ['ProgramFiles(x86)'])]))


            # device_task.setFont(font)
            # select_task = True
            self._refresh_tasks_list(drop_popup=False)
            # self.device_task.addItem('- Choose task -')
            # for item in tasks:
            #     self.device_task.addItem(item)
            # self.fields['task_name'] = self.device_task.currentText().encode

            signal_hbox = QtWidgets.QHBoxLayout()
            # device_hbox.addWidget(label)
            signal_hbox.addWidget(self.device_task)
            signal_hbox.addStretch()
            signal_hbox.addWidget(open_ni_max)
            # signal_hbox.addStretch()
            # signal_hbox.addWidget(task_status)
            signal_hbox.addStretch()

        signal_vbox = QtWidgets.QVBoxLayout()


        # Signal setttings.
        signal_grid = QtWidgets.QGridLayout()

        # Window length.
        self.win_length = QtWidgets.QSpinBox()
        self.win_length.setToolTip(tt.tooltips['window_length'])
        self.win_length.setRange(1, MAX_WINDOW_LENGTH)
        self.win_length.setValue(DEFAULTS['samples_per_channel'])
        win_length_label = QtWidgets.QLabel('Window length')
        signal_grid.addWidget(win_length_label, 0, 0)
        signal_grid.addWidget(self.win_length, 0, 2)
        self.fields['samples_per_channel'] = self.win_length.value
        # signal_grid.addRow(self.tr('Window length'), win_length)

        # Zero padding.
        zero_padding = QtWidgets.QSpinBox()
        zero_padding.setToolTip(tt.tooltips['zero_padding'])
        zero_padding.setRange(0, MAX_WINDOW_LENGTH)
        zero_padding.setValue(DEFAULTS['zero_padding'])
        zero_padding_label = QtWidgets.QLabel('Zero padding')
        signal_grid.addWidget(zero_padding_label, 1, 0)
        signal_grid.addWidget(zero_padding, 1, 2)
        self.fields['zero_padding'] = zero_padding.value

        # Excitation window.
        self.exc_win = QtWidgets.QComboBox()
        self.exc_win.setToolTip(tt.tooltips['excitation_window'])
        for window in _WINDOWS:
            self.exc_win.addItem(window)
        self.exc_win.setCurrentIndex([i for i, window in enumerate(_WINDOWS) if window in DEFAULTS['exc_window']][0])
        exc_win_label = QtWidgets.QLabel('Excitation window')
        exc_win_percent = QtWidgets.QDoubleSpinBox()
        exc_win_percent.setToolTip(tt.tooltips['excitation_window_percent'])
        exc_win_percent.setRange(0.01, 100)
        exc_win_percent.setValue(1)
        exc_win_percent_unit = QtWidgets.QLabel('%')
        signal_grid.addWidget(exc_win_label, 2, 0)
        signal_grid.addWidget(self.exc_win, 2, 2)
        signal_grid.addWidget(exc_win_percent, 2, 3)
        signal_grid.addWidget(exc_win_percent_unit, 2, 4)
        self.fields['exc_window'] = lambda: '{0}:{1:.4f}'.format(self.exc_win.currentText(), exc_win_percent.value()/100)
        # self.fields['exc_window_percent'] = exc_win_percent
        # signal_grid.addRow(self.tr('Excitation window'), exc_win)

        # Response window.
        self.resp_win = QtWidgets.QComboBox()
        self.resp_win.setToolTip(tt.tooltips['response_window'])
        for window in _WINDOWS:
            self.resp_win.addItem(window)
        self.resp_win.setCurrentIndex([i for i, window in enumerate(_WINDOWS) if window in DEFAULTS['resp_window']][0])
        resp_win_label = QtWidgets.QLabel('Response window')
        resp_win_percent = QtWidgets.QDoubleSpinBox()
        resp_win_percent.setToolTip(tt.tooltips['response_window_percent'])
        resp_win_percent.setRange(0.01, 100)
        resp_win_percent.setValue(1)
        resp_win_percent_unit = QtWidgets.QLabel('%')
        signal_grid.addWidget(resp_win_label, 3, 0)
        signal_grid.addWidget(self.resp_win, 3, 2)
        signal_grid.addWidget(resp_win_percent, 3, 3)
        signal_grid.addWidget(resp_win_percent_unit, 3, 4)
        self.fields['resp_window'] = lambda: '{0}:{1:.4f}'.format(self.resp_win.currentText(), resp_win_percent.value()/100)
        # self.fields['resp_window_percent'] = resp_win_percent
        # signal_grid.addRow(self.tr('Response window'), resp_win)

        # Averaging.
        self.avg_type = QtWidgets.QComboBox()
        self.avg_type.setToolTip(tt.tooltips['averaging_type'])
        for weighting in _WGH_TYPES:
            self.avg_type.addItem(weighting)
        self.avg_type.setCurrentIndex([i for i, window in enumerate(_WGH_TYPES) if window in DEFAULTS['weighting']][0])
        avg_type_label = QtWidgets.QLabel('Averaging')
        avg_sample_number = QtWidgets.QSpinBox()
        avg_sample_number.setToolTip(tt.tooltips['averaging_number'])
        avg_sample_number.setRange(2, 50)
        avg_sample_number.setValue(DEFAULTS['n_averages'])
        avg_sample_number_unit = QtWidgets.QLabel('samples')
        signal_grid.addWidget(avg_type_label, 4, 0)
        signal_grid.addWidget(self.avg_type, 4, 2)
        signal_grid.addWidget(avg_sample_number, 4, 3)
        signal_grid.addWidget(avg_sample_number_unit, 4, 4)
        self.fields['weighting'] = self.avg_type.currentText
        self.fields['n_averages'] = avg_sample_number.value

        # Save time history.
        save_time_history = QtWidgets.QCheckBox()
        save_time_history.setToolTip(tt.tooltips['save_time_history'])
        save_time_history_label = QtWidgets.QLabel('Save time-history')
        save_time_history.setChecked(DEFAULTS['save_time_history'])
        signal_grid.addWidget(save_time_history_label, 5, 0)
        signal_grid.addWidget(save_time_history, 5, 2)
        self.fields['save_time_history'] = save_time_history.isChecked

        # Trigger level
        self.trigger_level = QtWidgets.QDoubleSpinBox()
        self.trigger_level.setToolTip(tt.tooltips['trigger_level'])
        self.trigger_level.setRange(0.0001, 1000000)
        self.trigger_level.setValue(DEFAULTS['trigger_level'])
        trigger_level_label = QtWidgets.QLabel('Trigger level (excitation)')
        signal_grid.addWidget(trigger_level_label, 6, 0)
        signal_grid.addWidget(self.trigger_level, 6, 2)
        self.fields['trigger_level'] = self.trigger_level.value

        # Pre trigger samples.
        self.pre_trigger = QtWidgets.QSpinBox()
        self.pre_trigger.setToolTip(tt.tooltips['pre_trigger_samples'])
        self.pre_trigger.setRange(0, self.win_length.value())
        self.pre_trigger.setValue(DEFAULTS['pre_trigger_samples'])
        # self.win_length.valueChanged.connect(lambda: self.pre_trigger.setRange(0, self.win_length.value()))
        pre_trigger_label = QtWidgets.QLabel('Pre-trigger samples')
        pre_trigger_unit = QtWidgets.QLabel('S')
        signal_grid.addWidget(pre_trigger_label, 7, 0)
        signal_grid.addWidget(self.pre_trigger, 7, 2)
        signal_grid.addWidget(pre_trigger_unit, 7, 3)
        self.fields['pre_trigger_samples'] = self.pre_trigger.value

        # Check if task is already set and if it is, fill saved values.
        if 'task_name' in self.settings:
            self.win_length.setValue(self.settings['samples_per_channel'])
            self.exc_win.setCurrentIndex([i for i, win in enumerate(_WINDOWS) if win in self.settings['exc_window']][0])
            exc_win_percent.setValue(float(self.settings['exc_window'].split(':')[1])*100)
            self.resp_win.setCurrentIndex([i for i, win in enumerate(_WINDOWS) if win in self.settings['resp_window']][0])
            resp_win_percent.setValue(float(self.settings['resp_window'].split(':')[1])*100)
            self.avg_type.setCurrentIndex([i for i, avgt in enumerate(_WGH_TYPES) if avgt in self.settings['weighting']][0])
            avg_sample_number.setValue(self.settings['n_averages'])
            self.trigger_level.setValue(self.settings['trigger_level'])
            self.pre_trigger.setValue(self.settings['pre_trigger_samples'])
            zero_padding.setValue(self.settings['zero_padding'])
            save_time_history.setChecked(self.settings['save_time_history'])


        if 'excitation_type' in self.settings:
            if self.settings['excitation_type'] == 'impulse':
                self.radio_impulse.setChecked(True)
            elif self.settings['excitation_type'] == 'random':
                self.radio_random.setChecked(True)
            elif self.settings['excitation_type'] == 'oma':
                self.radio_oma.setChecked(True)
        else:
            self.radio_impulse.setChecked(True)

        signal_grid.setColumnStretch(1, 5)
        signal_grid.setColumnStretch(4, 15)

        groupb_box = QtWidgets.QGroupBox()
        groupb_box.setTitle('Signal ')
        # groupb_box.setStyleSheet("QGroupBox {font-size: 16px;}")
        groupb_box.setStyleSheet("QGroupBox {font-weight: bold;}")

        signal_vbox.addLayout(signal_hbox)
        signal_vbox.addWidget(task_status)
        signal_vbox.addLayout(signal_grid)

        groupb_box.setLayout(signal_vbox)

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(group)
        vbox.addWidget(groupb_box)

        table = QtWidgets.QTableWidget(3, 5)
        table.setShowGrid(False)

        horizontal_header = table.horizontalHeader()

        table.setHorizontalHeaderLabels(['Name', 'Type', 'Units', 'Delay [ms]', ''])
        table.setVerticalHeaderLabels(['Channel {0}'.format(i+1) for i in range(3)])
        table.resizeColumnsToContents()
        header_view = table.horizontalHeader()
        header_view.setSectionResizeMode(0, header_view.Stretch)
        # cw = QtGui.QPushButton('Bu')
        # header_view.setCornerWidget(cw)
        table.setDisabled(True)

        excitation_warning = QtWidgets.QLabel('')

        def refresh_table(names):
            """Populate table with channels for the chosen task."""
            table.setEnabled(True)
            # self.channel_table.setEnabled(True)
            i = len(names)
            table.setRowCount(i)
            table.setVerticalHeaderLabels(['Channel {0}'.format(i+1) for i in range(i)])
            # self.channel_table.ch

            if not ('task_name' in self.settings):
                for key in DEFAULTS.keys():
                    self.settings[key] = DEFAULTS[key]
            elif not(self.device_task.currentText() in self.settings['task_name'].decode()):
                for key in DEFAULTS.keys():
                    self.settings[key] = DEFAULTS[key]

            for i, name in enumerate(names):
                # First cell
                channel_name = QtWidgets.QTableWidgetItem(name)
                channel_name.setFlags(channel_name.flags() & ~QtCore.Qt.ItemIsEditable)
                table.setItem(i, 0, channel_name)

                # Type
                type = QtWidgets.QComboBox()
                type.addItem(self.tr('Response'))
                type.addItem(self.tr('Excitation'))
                # type.addItem(self.tr('Disabled'))
                if 'resp_channels' in self.settings and 'exc_channel' in self.settings:
                    if i in self.settings['resp_channels']:
                        type.setCurrentIndex(0)
                    elif i == self.settings['exc_channel']:
                        type.setCurrentIndex(1)

                # type.currentIndexChanged()
                table.setCellWidget(i, 1, type)

                # Units
                units = QtWidgets.QComboBox()
                if 'Excitation' in type.currentText():
                    # units.setEnabled(True)
                    if self.fields['excitation_type']() == 'oma':
                        units.addItems(_RESP_TYPES)
                    else:
                        units.addItems(_EXC_TYPES)
                elif 'Response' in type.currentText():
                    # units.setEnabled(True)
                    units.addItems(_RESP_TYPES)
                # elif 'Disabled' in type.currentText():
                #     units.setDisabled(True)
                # print(i, name)
                # print(self.settings['channel_types'])
                # print(self.fields['excitation_type']())
                if self.fields['excitation_type']() == 'oma':
                    try:
                        units.setCurrentIndex([num for num, letter in enumerate(_RESP_TYPES) if
                        self.settings['channel_types'][i] in letter][0])
                    except:
                        units.setCurrentIndex(0)
                elif 'channel_types' in self.settings and 'Excitation' in type.currentText():
                    units.setCurrentIndex([num for num, letter in enumerate(_EXC_TYPES) if
                    self.settings['channel_types'][i] in letter][0])
                elif 'channel_types' in self.settings and 'Response' in type.currentText():
                    try:
                        units.setCurrentIndex([num for num, letter in enumerate(_RESP_TYPES) if
                        self.settings['channel_types'][i] in letter][0])
                    except:
                        units.setCurrentIndex(0)
                table.setCellWidget(i, 2, units)

                # Delay.
                delay = QtWidgets.QDoubleSpinBox()
                delay.setRange(-5000, 5000)
                delay.setDecimals(3)
                # print (self.settings['channel_delay'])
                if 'channel_delay' in self.settings:
                    delay.setValue(self.settings['channel_delay'][i]*1000)
                table.setCellWidget(i, 3, delay)
            # Implement Excitation channel number checking. Also updating units field appropriately.
            def excitation_check(nr):

                for u in range(nr):
                    if 'Excitation' in table.cellWidget(u, 1).currentText():
                        # table.cellWidget(u, 2).setEnabled(True)
                        table.cellWidget(u, 2).clear()
                        table.cellWidget(u, 2).addItems(_EXC_TYPES)
                    elif 'Response' in table.cellWidget(u, 1).currentText():
                        # table.cellWidget(u, 2).setEnabled(True)
                        table.cellWidget(u, 2).clear()
                        table.cellWidget(u, 2).addItems(_RESP_TYPES)
                    # elif 'Disabled' in table.cellWidget(u, 1).currentText():
                    #     table.cellWidget(u, 2).setDisabled(True)


                excitation_channels = [i for i in range(nr) if 'Excitation' in table.cellWidget(i, 1).currentText()]
                if len(excitation_channels) > 1:
                    excitation_warning.setText('''<span style="font-weight: bold; color: red;">There should be exactly one'''
                                               ''' excitation channel!</span>''')
                    self.save.setDisabled(True)
                elif len(excitation_channels) < 1:
                    excitation_warning.setText('''<span style="font-weight: bold; color: red;">There should be exactly one'''
                                               ''' excitation channel!</span>''')
                else:
                    excitation_warning.setText('')
                    self.save.setEnabled(True)

            nr = len(names)
            for i in range(nr):
                table.cellWidget(i, 1).currentIndexChanged.connect(lambda: excitation_check(nr))


            table.resizeColumnsToContents()
            horizontal_header.setStretchLastSection(True)

        table.setAlternatingRowColors(True)





        table_title = QtWidgets.QLabel('Channels')
        table_title.setStyleSheet("QLabel {font-weight: bold;}")

        table_title_layout = QtWidgets.QHBoxLayout()
        table_title_layout.addWidget(table_title)
        table_title_layout.addWidget(excitation_warning)

        vbox.addLayout(table_title_layout)
        vbox.addWidget(table)

        # Preview window.
        preview_window = pg.GraphicsView()
        preview_window.setMinimumHeight(300)
        v_graphic_layout = QtWidgets.QVBoxLayout()
        h_button_layout = QtWidgets.QHBoxLayout()
        self.fig = pg.PlotWidget(name='Signal preview')
        self.fig.setLabel('bottom', 'time', units='s')
        self.fig.setLabel('left', 'amplitude')

        self.fig_plotitem = self.fig.getPlotItem()

        self.button_testrun = QtWidgets.QPushButton('Test Run')
        self.button_testrun.setToolTip(tt.tooltips['test_run'])
        self.button_testrun.setObjectName('small')
        self.button_testrun.setCheckable(True)
        self.button_testrun.setDisabled(True)
        def testrun_start_agent(pressed):
            if pressed:
                self.measure_test_run_data()
            else:
                self.stop_measurement_button_trigger()
        self.button_testrun.clicked[bool].connect(testrun_start_agent)

        self.button_fft = QtWidgets.QPushButton('PSD Toggle')
        self.button_fft.setToolTip(tt.tooltips['toggle_PSD'])
        self.button_fft.setObjectName('small')
        self.button_fft.setCheckable(True)
        self.button_fft.clicked[bool].connect(self.fft_toggle)

        h_button_layout.addStretch()
        h_button_layout.addWidget(self.button_testrun)
        h_button_layout.addWidget(self.button_fft)
        h_button_layout.addStretch()

        # splitter = QtGui.QSplitter(QtCore.Qt.Vertical)

        # v_graphic_layout.addWidget(splitter)

        v_graphic_layout.addLayout(h_button_layout)
        # splitter.addLayout(h_button_layout)
        # v_graphic_layout.addWidget(splitter)
        v_graphic_layout.addWidget(self.fig)
        # splitter.addWidget(self.fig)
        preview_window.setLayout(v_graphic_layout)
        # preview_window.setLayout(splitter)

        # vbox.addWidget(preview_window)

        channel_widget.setLayout(vbox)

        vbox.setContentsMargins(0, 0, 0, 0)

        def load_task(reset=False):
            if 'refresh  ' in self.device_task.currentText():
                self._refresh_tasks_list()
            else:
                try:
                    # TODO: Check for required buffer size and availible buffer.
                # i = dq.DAQTask(self.device_task.currentText().encode())
                    i = dq.DAQTask(self.device_task.currentText().encode())

                    channel_list = list(map(bytes.decode, i.channel_list))

                    i.clear_task(wait_until_done=False)

                    # if i.sample_rate < 2000:
                    #     task_status.setText('<span style="color: orange;"><b>Sampling rate should be at least 2 kHz.</b></span>')
                    #     table.setDisabled(True)
                    #     self.save.setDisabled(True)
                    # else:

                    combos = [QtWidgets.QComboBox() for channel in channel_list]
                    labels = [QtWidgets.QLabel(channel) for channel in channel_list]

                    # task_status.setText("""<span style="color: green;">Sampling rate: <b>{0:.0f} S/s</b>, """
                    #                     """Samples to read: <b>{1:.0f} S</b><br />"""
                    #                     """Nr. of channels: <b>{2:.0f}</b></span>""".format(i.sample_rate,
                    #                                                                 i.samples_per_ch, len(channel_list)))

                    task_status.setText("""<span style="color: green;">Sampling rate: <b>{0:.0f} S/s</b>, """
                                        """Nr. of channels: <b>{1:.0f}</b></span>""".format(i.sample_rate,
                                                                                    len(channel_list)))


                    # Reset settings on task change except when opening up saved state.
                    if 'task_name' in self.settings:
                        if self.settings['task_name'] == self.device_task.currentText().encode():
                            pass
                        else:
                            self.win_length.setValue(i.samples_per_ch)
                    else:
                        self.win_length.setValue(i.samples_per_ch)

                    self.channel_nr = len(channel_list)
                    refresh_table(channel_list)
                    self.save.setEnabled(True)
                    self.button_testrun.setEnabled(True)

                    # Run measurement thread.
                    # self.measure_test_run_process_start()

                    # table.setEnabled(True)

                except dq.DAQError:
                    task_status.setText('<span style="color: orange;"><b>Device malfunction.</b></span>')
                    table.setDisabled(True)
                    # table.setDisabled(True)
                    self.save.setDisabled(True)

        # Check if task is already set, then select it.
        self.device_task.currentIndexChanged.connect(load_task)
        self.measurement_type_change.connect(load_task)
        if 'task_name' in self.settings:
            tasks = map(bytes.decode, dq.get_daq_tasks())
            arglist = [n for n, task in enumerate(tasks) if self.settings['task_name'].decode() in task]
            if len(arglist) > 0:
                self.device_task.setCurrentIndex(arglist[0]+1)

        return table, channel_widget, preview_window

    def set_impulse_type(self, enabled):

        if enabled:
            # Enable impulse only options.
            self.trigger_level.setEnabled(True)
            self.pre_trigger.setEnabled(True)

            # Disable random only options.
            # ... ?


            # Set recommended values.
            if self.settings['excitation_type'] != 'impulse':
                set_combo_box_index(self.avg_type, EXCITATION_DEFAULTS['impulse']['weighting'])
                set_combo_box_index(self.exc_win, EXCITATION_DEFAULTS['impulse']['exc_window'])
                set_combo_box_index(self.resp_win, EXCITATION_DEFAULTS['impulse']['resp_window'])
            else:
                # If random is already setup in memory,
                # populate with preset values.
                set_combo_box_index(self.avg_type, self.settings['weighting'])
                set_combo_box_index(self.exc_win, self.settings['exc_window'])
                set_combo_box_index(self.resp_win, self.settings['resp_window'])

            self.fields['excitation_type'] = lambda: 'impulse'

        if self.device_task.currentIndex() != 0:
            self.measurement_type_change.emit()

    def set_random_type(self, enabled):

        if enabled:
            # Enable random only options.
            # ...

            # Disable impulse only options.
            self.trigger_level.setDisabled(True)
            self.pre_trigger.setDisabled(True)

            # Set recommended values.
            if self.settings['excitation_type'] != 'random':
                set_combo_box_index(self.avg_type, EXCITATION_DEFAULTS['random']['weighting'])
                set_combo_box_index(self.exc_win, EXCITATION_DEFAULTS['random']['exc_window'])
                set_combo_box_index(self.resp_win, EXCITATION_DEFAULTS['random']['resp_window'])
            else:
                # If random is already setup in memory,
                # populate with preset values.
                set_combo_box_index(self.avg_type, self.settings['weighting'])
                set_combo_box_index(self.exc_win, self.settings['exc_window'])
                set_combo_box_index(self.resp_win, self.settings['resp_window'])

            self.fields['excitation_type'] = lambda: 'random'

        if self.device_task.currentIndex() != 0:
            self.measurement_type_change.emit()

    def set_oma_type(self, enabled):

        if enabled:
            # Enable random only options.
            # ...

            # Disable impulse only options.
            self.trigger_level.setDisabled(True)
            self.pre_trigger.setDisabled(True)

            # Set recommended values.
            if self.settings['excitation_type'] != 'oma':
                set_combo_box_index(self.avg_type, EXCITATION_DEFAULTS['oma']['weighting'])
                set_combo_box_index(self.exc_win, EXCITATION_DEFAULTS['oma']['exc_window'])
                set_combo_box_index(self.resp_win, EXCITATION_DEFAULTS['oma']['resp_window'])
            else:
                # If oma is already setup in memory,
                # populate with preset values.
                set_combo_box_index(self.avg_type, self.settings['weighting'])
                set_combo_box_index(self.exc_win, self.settings['exc_window'])
                set_combo_box_index(self.resp_win, self.settings['resp_window'])

            self.fields['excitation_type'] = lambda: 'oma'

        if self.device_task.currentIndex() != 0:
            self.measurement_type_change.emit()

    def measure_test_run_process_start(self):
        """Start measurement process. This happens every time a new task is selected in dropdown."""
        if dp is None:
            class Empty(object):
                def stop_process(self):
                    pass
            self.process = Empty()

            return False
        self.process = dp.MeasurementProcess()
        self.process.start_process()

        self.save.clicked.connect(self.stop_process_button_trigger)
        self.dismiss.clicked.connect(self.stop_process_button_trigger)

    def stop_process_button_trigger(self):
        try:
            self.process.stop_measurement()
            self.timer.stop()
        except:
            pass
        self.process.stop_process()

    def stop_measurement_button_trigger(self):
        self.process.stop_measurement()
        self.timer.stop()

    def measure_test_run_data(self):
        """Start measurement."""
        self._save()


        # Pretty colors.
        self.colors = ['#f39c12', '#d35400', '#c0392b', '#16a085', '#27ae60', '#2980b9', '#8e44ad']

        # print(self.settings['channel_names'])
        # print(self.settings['resp_channels'])
        self.fig.clear()

        try:
            self.legend.scene().removeItem(self.legend)
        except:
            pass

        self.legend = self.fig.addLegend()

        nr_ch = len(self.settings['resp_channels']) + 1
        resp_curves = [self.fig.plot(
            pen=pg.mkPen({'color': self.colors[i]}),
            name='Ch {0} - {1}'.format(i, self.settings['channel_names'][i]))
            for i in range(nr_ch)]

        # resp_curve = self.fig_resp.plot(pen='y')
        self.fig.enableAutoRange('x', True)
        self.fig.enableAutoRange('y', True)



        def plot_triggered(triggered, resp_curve, pipe):
            plotdata = pipe.recv()
            # TODO: This should be faster.
            for i in range(plotdata.shape[0]):
                resp_curve[i].setData(self.x_axis, plotdata[i, :])
            if triggered.value:
                # Stop measurement.
                triggered.value = False
                self.stop_measurement_button_trigger()
                self.button_testrun.setChecked(False)

        def plot_random(triggered, resp_curve, pipe_1, pipe, text):
            plotdata = pipe_1.recv()
            # # TODO: This should be faster.
            # for i in range(plotdata.shape[0]):
            #     resp_curve[i].setData(self.x_axis, plotdata[i, :])
            if triggered.value:
                self.n_averages_done += 1
                triggered.value = False
                chunk_data = pipe.recv()
                text.setText('Pass {0} of {1}'.format(self.n_averages_done, self.settings['n_averages']))
                for i in range(chunk_data.shape[0]):
                    resp_curve[i].setData(self.x_axis, chunk_data[i, :])
                # text.setText('Pass {0} of {1}'.format(self.n_averages_done, self.settings['n_averages']))
                # # text.setPos(self.x_axis.max(), chunk_data.max())
                # text.setPos(1, 5)
                if self.n_averages_done >= self.settings['n_averages']:
                    self.n_averages_done = 0
                    self.stop_measurement_button_trigger()
                    self.button_testrun.setChecked(False)

        # Send over the settings, could be different, could be the same.
        self.process.setup_measurement_parameters(self.settings)
        # for key in self.settings:
        #     self.process.__dict__[key] = self.settings[key]
        self.process.run_measurement()

        sampling_fr = self.process.task_info_out.recv()
        self.x_axis = np.arange(0, self.settings['samples_per_channel']/sampling_fr, 1/sampling_fr)
        # self.sampling_fr = sampling_fr

        # Set up and start timed refresh. It must be a child of self (self.timer, not timer) otherwise it is
        # unreferenced instantly.
        self.n_averages_done = 0
        self.timer = QtCore.QTimer()

        if self.settings['excitation_type'] == 'impulse':
            self.timer.timeout.connect(lambda triggered=self.process.triggered, resp_curve=resp_curves,
                                              pipe=self.process.process_measured_data_out:
                                              plot_triggered(triggered, resp_curve, pipe))

        else: # random OR oma
            self.button_fft.click()
            text = pg.TextItem()
            self.fig.addItem(text)


            self.timer.timeout.connect(lambda triggered=self.process.triggered, resp_curve=resp_curves,
                                              pipe_1=self.process.process_measured_data_out,
                                              pipe=self.process.process_random_chunk_out, text=text:
                                              plot_random(triggered, resp_curve, pipe_1, pipe, text))

        self.timer.start(100)

        # self.button_stop.setEnabled(True)

        self.fig_plotitem = self.fig.getPlotItem()

    def fft_toggle(self, pressed):
        #print(self.fig_plotitem.spectrumMode)
        if pressed:
            # self.fft = True
            # self.fig_plotitem.spectrumMode = True
            self.fig.setLabel('bottom', 'frequency', units='Hz')
            self.fig.setLabel('left', 'amplitude')
            self.fig_plotitem.updateSpectrumMode(True)
        else:
            # self.fft = False
            self.fig.setLabel('bottom', 'time', units='s')
            self.fig.setLabel('left', 'amplitude')
            self.fig_plotitem.updateSpectrumMode(False)


    def closeEvent(self, *args, **kwargs):
        self.stop_process_button_trigger()



if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    main_window = ExcitationConfig()
    main_window.setGeometry(100, 100, 800, 480)
    main_window.show()

    sys.exit(app.exec_())
