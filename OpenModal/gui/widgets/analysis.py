# -*- coding: utf-8 -*-
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


from PyQt5 import QtCore, QtGui, QtWidgets
import pandas as pd
from OpenModal.analysis.stabilisation import *
from OpenModal.analysis import lsce, lscf, lsfd
from OpenModal.keys import keys as kkeys

from OpenModal.analysis.add_reconstruction_to_mdd import add_reconstruction_to_mdd
from OpenModal.analysis.add_reconstruction_to_mdd import save_analysis_settings
from OpenModal.analysis.add_reconstruction_to_mdd import save_stabilisation_spots
from OpenModal.analysis.utility_functions import complex_freq_to_freq_and_damp
from OpenModal.analysis.utility_functions import prime_factors
from OpenModal.analysis.utility_functions import get_analysis_id
from OpenModal.fft_tools import convert_frf
from OpenModal.utils import get_frf_from_mdd
from OpenModal.utils import get_frf_type

from OpenModal.gui.templates import COLOR_PALETTE

from string import Template

import pyqtgraph as pg
import numpy as np
import qtawesome as qta

import OpenModal.gui.widgets.prototype as prot

QVariant = lambda value=None: value

MEASUREMENT_INDEX_SELECT = ['ref_node', 'rsp_node']
MAX_FREQUENCY = 10E15
MAX_FFT_PRIME_FACTOR = 20
ALLOWED_ERROR = 1e-10


class IdentificationWidget(prot.SubWidget):
    """
    Identification widget containing the graphical user interface for the
    experimental modal analysis methods.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.v_global_layout = QtWidgets.QVBoxLayout()
        self.v_global_layout.setContentsMargins(0, 0, 0, 0)

        self.stackedWidget = QtWidgets.QStackedWidget()
        self.lscf_method = LSCFDialog()
        self.lsce_method = LSCEDialog()

        self.v_global_layout.addWidget(self.stackedWidget)
        self.setLayout(self.v_global_layout)

    def reload(self):
        """ Function to update the widgets when new data is loaded/imported. """
        # Create the corresponding stacked Widget
        self.stackedWidget.addWidget(self.lscf_method)
        self.stackedWidget.addWidget(self.lsce_method)

        method_lscf = self.lscf_method.lscf_widget.method_selection
        method_lsce = self.lsce_method.lsce_widget.method_selection

        method_lscf.activated[int].connect(method_lsce.setCurrentIndex)
        method_lscf.activated[int].connect(self.stackedWidget.setCurrentIndex)
        method_lsce.activated[int].connect(method_lscf.setCurrentIndex)
        method_lsce.activated[int].connect(self.stackedWidget.setCurrentIndex)

        self.lscf_method.lscf_widget.update(self.modaldata)
        self.lsce_method.lsce_widget.update(self.modaldata)

        # print('RELOAD')
        #
    # def refresh(self):
    #     """
    #     Function to update the widgets within the program, e. g. when the tabs
    #     are changed or when a new model is selected.
    #     """
    #     print('This is refreshing :)!!!')
    #     self.reload()





# class CEDialog(QtGui.QWidget):
#     def __init__(self, modaldata_object, method_selection):
#         super().__init__()
#
#         self.ce_widget = PropertiesTab(modaldata_object, method_selection)
#         main_layout = QtGui.QVBoxLayout()
#         main_layout.addWidget(self.ce_widget)
#         self.setLayout(main_layout)
#
#         self.ce_widget.stabilization_button_properties.clicked.connect(self.stab_diag)
#
#     def stab_diag(self):
#         f = self.ce_widget.draw_selection.xy[:, 0].real
#         frf = self.ce_widget.draw_selection.xy[:, 1]
#         f = f[f <= self.ce_widget.box_f_max.value()]
#         frf = frf[f <= self.ce_widget.box_f_max.value()]
#         temp = f >= self.ce_widget.box_f_min.value()
#         f = f[temp]
#         frf = frf[temp]
#         try:
#             self.ce_widget.draw_selection.spots_plot.sigClicked.disconnect()  # if stabilisation button is clicked
#             # more than once, delete the last signal
#         except:
#             pass
#         self.ce_widget.stabilisation_diagrams(f, frf, method='ce')


class LSCEDialog(QtWidgets.QWidget):
    """
    Class that deals with Least-squares Complex Exponential method (LSCE) GUI internals.
    """

    def __init__(self):
        """
        Initializing the LSCE dialog.
        :param modaldata_object: mdd file
        :return: an updated GUI according to data
        """
        super().__init__()

        self.lsce_widget = PropertiesTab()
        self.lsce_widget.spots_plot.method = 'lsce'

        main_layout = QtWidgets.QGridLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.lsce_widget)
        self.setLayout(main_layout)

        # Stabilisation button clicked
        self.lsce_widget.stabilization_button_properties.clicked.connect(self.stab_diag)

    def stab_diag(self):
        """
        When analysis button is clicked the  LSCE Experimental modal analysis is done.
        :return: stabilization chart with selectable poles for reconstruction
        """
        f = self.lsce_widget.spots_plot.draw_selection.xy[:, 0].real

        selected_model = self.lsce_widget.modaldata.tables['measurement_values'].loc[:, 'model_id'] \
                         == self.lsce_widget.spots_plot.model_id

        selected_model_index = self.lsce_widget.modaldata.tables['measurement_index'].loc[:, 'model_id'] \
                               == self.lsce_widget.spots_plot.model_id

        data = self.lsce_widget.modaldata.tables['measurement_values'][selected_model]
        data_index = self.lsce_widget.modaldata.tables['measurement_index'][selected_model_index]

        # TODO: LSCE method only works there is one reference. If not an exception should occur (popout!)
        # Create a 3D FRF array from mdd file
        frf, _ = get_frf_from_mdd(data, data_index)

        f_limits = (f <= self.lsce_widget.box_f_max.value() + ALLOWED_ERROR)

        # Apply upper limit to freqeuncy vector and FRF's
        f = f[f_limits]
        frf = frf[:, :, f_limits]

        # Get lower limit index
        low_lim = np.argmax(f >= self.lsce_widget.box_f_min.value())

        nf = (2 * (len(f) - low_lim - 1))  # number of DFT frequencies (nf >> n)

        # this is done to avoid high computation times due to the properties of the fft
        if max(prime_factors(nf)) > MAX_FFT_PRIME_FACTOR:
            temp_f = f[low_lim:]
            self.fft_popout = FFTLengthPopout(temp_f)
            self.fft_popout.exec_()
            upper_limit = low_lim + self.fft_popout.max_freq_index.value()
            f = f[:upper_limit]
            frf = frf[:, :, :upper_limit]
            low_lim += self.fft_popout.min_freq_index.value()

            self.lsce_widget.box_f_min.setValue(self.fft_popout.f_min)
            self.lsce_widget.box_f_max.setValue(self.fft_popout.f_max)

        self.lsce_widget.spots_plot.fstab = f
        self.lsce_widget.spots_plot.frfstab = frf

        try:
            self.lsce_widget.spots_plot.sigClicked.disconnect()  # if stabilisation button is clicked
            # more than once, delete the last signal
        except:
            pass
        self.lsce_widget.stabilisation_diagrams(self.lsce_widget.spots_plot.fstab,
                                                self.lsce_widget.spots_plot.frfstab,
                                                method='lsce', low_lim=low_lim)


class LSCFDialog(QtWidgets.QWidget):
    """
    Class that deals with Least-squares Complex Frequency Domain method (LSCF) GUI internals.
    """

    def __init__(self):
        """
        Initializing the LSCF dialog.
        :param modaldata_object: mdd file
        :return: an updated GUI according to data
        """
        super().__init__()

        self.lscf_widget = PropertiesTab()
        self.lscf_widget.spots_plot.method = 'lscf'

        main_layout = QtWidgets.QGridLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.lscf_widget)
        self.setLayout(main_layout)

        # Stabilisation button clicked
        self.lscf_widget.stabilization_button_properties.clicked.connect(self.stab_diag)

    def stab_diag(self):
        """
        When analysis button is clicked the  LSCF Experimental modal analysis is done.
        :return: stabilization chart with selectable poles for reconstruction
        """
        f = self.lscf_widget.spots_plot.draw_selection.xy[:, 0].real

        selected_model = self.lscf_widget.modaldata.tables['measurement_values'].loc[:, 'model_id'] \
                         == self.lscf_widget.spots_plot.model_id
        selected_model_index = self.lscf_widget.modaldata.tables['measurement_index'].loc[:, 'model_id'] \
                               == self.lscf_widget.spots_plot.model_id

        data = self.lscf_widget.modaldata.tables['measurement_values'][selected_model]
        data_index = self.lscf_widget.modaldata.tables['measurement_index'][selected_model_index]

        # Create a 3D FRF array from mdd file
        frf, _ = get_frf_from_mdd(data, data_index)

        f_limits = (f <= self.lscf_widget.box_f_max.value() + ALLOWED_ERROR)

        # Apply upper limit to freqeuncy vector and FRF's
        f = f[f_limits]
        frf = frf[:, :, f_limits]

        # Get lower limit index
        low_lim = np.argmax(f >= self.lscf_widget.box_f_min.value())

        nf = (2 * (len(f) - low_lim - 1))  # number of DFT frequencies (nf >> n)

        # this is done to avoid high computation times due to the properties of the fft
        if max(prime_factors(nf)) > MAX_FFT_PRIME_FACTOR:
            temp_f = f[low_lim:]
            self.fft_popout = FFTLengthPopout(temp_f)
            self.fft_popout.exec_()
            upper_limit = low_lim + self.fft_popout.max_freq_index.value()
            f = f[:upper_limit]
            frf = frf[:, :, :upper_limit]
            low_lim += self.fft_popout.min_freq_index.value()

            self.lscf_widget.box_f_min.setValue(self.fft_popout.f_min)
            self.lscf_widget.box_f_max.setValue(self.fft_popout.f_max)

        self.lscf_widget.spots_plot.fstab = f
        self.lscf_widget.spots_plot.frfstab = frf

        # try:
        #     self.lscf_widget.spots_plot.sigClicked.disconnect()  # if stabilisation button is clicked
        #     # more than once, delete the last signal
        # except:
        #     pass
        self.lscf_widget.stabilisation_diagrams(self.lscf_widget.spots_plot.fstab,
                                                self.lscf_widget.spots_plot.frfstab,
                                                method='lscf', low_lim=low_lim)


class FFTLengthPopout(QtWidgets.QDialog):
    """
    A warning popout window, which appears when the FFT length max prime factor
    is under the MAX_FFT_PRIME_FACTOR limit
    """

    def __init__(self, f):
        super().__init__()
        self.setWindowTitle('Computation efficeincy warning!')
        # set style
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        p = self.palette()
        p.setColor(self.backgroundRole(), QtCore.Qt.white)
        self.setPalette(p)
        # self.setAutoFillBackground(True)

        self.setContentsMargins(0, 0, 0, 0)

        with open('gui/styles/style_template.css', 'r', encoding='utf-8') as fh:
            src = Template(fh.read())
            src = src.substitute(COLOR_PALETTE)
            self.setStyleSheet(src)

        # set data and GUI
        self.f = f
        self.f_orig = f
        self.f_len = len(f)
        self.max_prime_value = MAX_FFT_PRIME_FACTOR

        text1 = (" For best performance of FFT slightly change the frequency range!")
        text1 = QtWidgets.QLabel(text1)

        layout_text = QtWidgets.QVBoxLayout()
        layout_text.addWidget(text1)
        layout_text.setAlignment(QtCore.Qt.AlignJustify)

        autoselect = QtWidgets.QPushButton('Autoselect')
        autoselect.setObjectName('medium')
        self.reset = QtWidgets.QPushButton('Reset')
        self.reset.setObjectName('small')
        self.reset.setDisabled(True)
        autoselect_layout = QtWidgets.QHBoxLayout()
        autoselect_layout.addWidget(autoselect)
        autoselect_layout.setAlignment(QtCore.Qt.AlignCenter)

        def autoselect_fft_len():
            """
            Function computing the new FFT length when the autoselect button
            is clicked.
            """
            # self.f = self.f_orig
            # self.fft_len_index = len(self.f)
            self.fft_len_index = self.f_max_index - self.f_min_index
            nf = 2 * (self.fft_len_index - 1)  # two sided FFT length
            i = 1
            j = 1
            while max(prime_factors(nf)) > MAX_FFT_PRIME_FACTOR:
                if cutoff_high_freq.isChecked():
                    self.f = self.f[:-1]
                    self.f_max_index = self.f_len - i
                    i += 1
                elif cutoff_low_freq.isChecked():
                    self.f = self.f[1:]
                    self.f_min_index = j
                    j += 1

                self.fft_len_index = self.f_max_index - self.f_min_index

                self.min_freq_index.setValue(self.f_min_index)
                self.max_freq_index.setValue(self.f_max_index)
                nf = 2 * (self.fft_len_index - 1)
                self.reset.setEnabled(True)

        def reset_data():
            """
            Fucntion that resets the FFT length data when the reset button
            is clicked.
            """
            self.f = self.f_orig
            self.f_min = self.f[0]
            self.f_max = self.f[-1]

            self.f_min_index = 0
            self.f_max_index = len(self.f)

            self.min_freq_index.setValue(self.f_min_index)
            self.max_freq_index.setValue(self.f_max_index)
            self.reset.setDisabled(True)


        autoselect.clicked.connect(autoselect_fft_len)
        self.reset.clicked.connect(reset_data)

        cutoff_high_freq = QtWidgets.QRadioButton('Cutoff higher frequencies, index:')
        cutoff_low_freq = QtWidgets.QRadioButton('Cutoff lower frequencies, index:')

        cutoff_high_freq.setChecked(True)
        cutoff_low_freq.setChecked(False)

        def radio_button_cutoff_high_freq():
            """
            When one radio button is selected the other should be turned off.
            """
            cutoff_low_freq.setChecked(False)

        def radio_button_cutoff_low_freq():
            """
            When one radio button is selected the other should be turned off.
            """
            cutoff_high_freq.setChecked(False)

        cutoff_high_freq.toggled.connect(radio_button_cutoff_high_freq)
        cutoff_low_freq.toggled.connect(radio_button_cutoff_low_freq)

        width = 70
        self.f_min_index = 0
        self.f_max_index = len(self.f)

        self.min_freq_index = QtWidgets.QSpinBox()
        self.min_freq_index.setMaximum(len(f))
        self.min_freq_index.setValue(self.f_min_index)
        self.min_freq_index.setFixedWidth(width)

        self.max_freq_index = QtWidgets.QSpinBox()
        self.max_freq_index.setMaximum(len(f))
        self.max_freq_index.setValue(self.f_max_index)
        self.max_freq_index.setFixedWidth(width)

        self.f_min = self.f[0]
        self.f_max = self.f[-1]

        self.text_max_freq = QtWidgets.QLabel('(' + str(self.f_max) + ' Hz)')
        self.text_min_freq = QtWidgets.QLabel('(' + str(self.f_min) + ' Hz)')

        grid_layout = QtWidgets.QGridLayout()
        grid_layout.addWidget(cutoff_high_freq, 0, 0, 1, 1)
        grid_layout.addWidget(self.max_freq_index, 0, 1, 1, 1)

        grid_layout.addWidget(self.text_max_freq, 0, 2, 1, 1)
        grid_layout.addWidget(cutoff_low_freq, 1, 0, 1, 1)
        grid_layout.addWidget(self.min_freq_index, 1, 1, 1, 1)
        grid_layout.addWidget(self.text_min_freq, 1, 2, 1, 1)
        grid_layout.setAlignment(QtCore.Qt.AlignLeft)

        self.text_slow = QtWidgets.QLabel('<b>Slow</b>')
        self.text_slow.setStyleSheet('color: red')

        self.text_fast = QtWidgets.QLabel('<b>Fast</b>')
        self.text_fast.setStyleSheet('color: lightgray')

        grid_layout_status = QtWidgets.QGridLayout()
        grid_layout_status.addWidget(QtWidgets.QLabel('Status:'), 0, 0, 1, 1)
        grid_layout_status.addWidget(self.text_slow, 0, 1, 1, 1)
        grid_layout_status.addWidget(self.text_fast, 0, 2, 1, 1)
        grid_layout_status.setAlignment(QtCore.Qt.AlignLeft)

        def min_value_changed():
            """
            Update the data when FFT minimum index is changed.
            """
            self.f_min_index = self.min_freq_index.value()
            self.f_min = self.f_orig[self.f_min_index]
            self.text_min_freq.setText('(' + str(self.f_min) + ' Hz)')

            self.fft_len_index = self.f_max_index - self.f_min_index
            nf = 2 * (self.fft_len_index - 1)
            if max(prime_factors(nf)) > MAX_FFT_PRIME_FACTOR:
                self.text_slow.setStyleSheet('color: red')
                self.text_fast.setStyleSheet('color: lightgray')

            else:
                self.text_slow.setStyleSheet('color: lightgray')
                self.text_fast.setStyleSheet('color: green')

            self.reset.setEnabled(True)

        def max_value_changed():
            """
            Update the data when FFT maximum index is changed.
            """
            self.f_max_index = self.max_freq_index.value()
            self.f_max = self.f_orig[self.f_max_index-1]
            self.text_max_freq.setText('(' + str(self.f_max) + ' Hz)')

            self.fft_len_index = self.f_max_index - self.f_min_index
            nf = 2 * (self.fft_len_index - 1)
            if max(prime_factors(nf)) > MAX_FFT_PRIME_FACTOR:
                self.text_slow.setStyleSheet('color: red')
                self.text_fast.setStyleSheet('color: lightgray')

            else:
                self.text_slow.setStyleSheet('color: lightgray')
                self.text_fast.setStyleSheet('color: green')

            self.reset.setEnabled(True)

        # Signals and slots
        self.min_freq_index.valueChanged.connect(min_value_changed)
        self.max_freq_index.valueChanged.connect(max_value_changed)

        done = QtWidgets.QPushButton('Done')
        done.setObjectName('small')

        local_layout_buttons = QtWidgets.QHBoxLayout()
        local_layout_buttons.addWidget(done)
        local_layout_buttons.addWidget(self.reset)
        local_layout_buttons.setAlignment(QtCore.Qt.AlignLeft)

        layout = QtWidgets.QVBoxLayout()
        layout.addLayout(layout_text)
        layout.addLayout(autoselect_layout)
        layout.addLayout(grid_layout)
        layout.addLayout(grid_layout_status)
        layout.addLayout(local_layout_buttons)
        layout.setAlignment(QtCore.Qt.AlignTop)

        self.setLayout(layout)
        self.show()

        done.clicked.connect(self.accept)


class DataFrameModel(QtCore.QAbstractTableModel):
    """ data model for a DataFrame class """

    def __init__(self):
        """
        Initialize an empty pandas Dataframe
        :return: an empty pandas dataframe
        """
        super(DataFrameModel, self).__init__()
        self.df = pd.DataFrame()

    def signal_update(self, data_in):
        """
        Update the dataframe with new data
        :param data_in: data
        :return: updated dataframe
        """
        self.df = data_in
        self.layoutChanged.emit()

    # -------------  table display functions  -----------------
    def headerData(self, section, orientation, role=QtCore.Qt.DisplayRole):
        """
        Header data display.
        """
        if role != QtCore.Qt.DisplayRole:
            return QVariant()

        if orientation == QtCore.Qt.Horizontal:
            try:
                return self.df.columns.tolist()[section]
            except (IndexError,):
                return QVariant()
        elif orientation == QtCore.Qt.Vertical:
            try:
                # return self.df.index.tolist()
                return self.df.index.tolist()[section]
            except (IndexError,):
                return QVariant()

    def data(self, index, role=QtCore.Qt.DisplayRole):
        """
        Data display.
        """
        if role != QtCore.Qt.DisplayRole:
            return QVariant()

        if not index.isValid():
            return QVariant()
        return QVariant(str(self.df.ix[index.row(), index.column()]))

    def rowCount(self, index=QtCore.QModelIndex()):
        """
        Dataframe row count.
        :return: number of rows
        """
        return self.df.shape[0]

    def columnCount(self, index=QtCore.QModelIndex()):
        """
        Dataframe column count
        :return: number of columns
        """
        return self.df.shape[1]


class DrawSelection(QtWidgets.QWidget):
    """Class for data visualization. It draws selected data (rows) - FRFs """

    def __init__(self):
        """ Initialize the plot area. """

        super().__init__()

        self.fig = pg.PlotWidget(name='Measurement')
        self.plot_area = self.fig.plotItem
        self.plot_area.setLogMode(x=None, y=True)
        self.plot_area.setLabel('bottom', 'Frequency [Hz]')
        self.plot_area.setLabel('left', 'Amplitude [(m/s²)/N]')

        self.stabilisation_spots = pg.ViewBox()

        self.stabilisation_spots.setXLink(self.fig)
        self.fig.getAxis('right').setLabel('Model Order')
        self.fig.getAxis('right').setLogMode(False)
        self.fig.showAxis('right')

        self.xy = None
        self.singlefrf = self.plot_area

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.fig)
        self.setLayout(layout)

    def drawing_rows(self, measurement_index, measurement_values, data_table):
        """
        Draws rows according to the selection in the table.
        :param modaldata_object: mdd file
        :param data_table: data table
        :return: drawn FRFs
        """
        self.dataTable = data_table
        self.measurement_index = measurement_index
        self.measurement_values = measurement_values

        self.selection = self.dataTable.selectionModel()

        if self.measurement_index.size > 0:
            self.selection.selectionChanged.connect(self.handle_selection_changed)

    def handle_selection_changed(self, selected, deselected):
        """
        Handles selection/reselection of rows and its connection to data.
        """

        for self.index in self.dataTable.selectionModel().selectedRows():
            measurement_id = self.measurement_index.iloc[self.index.row()].loc['measurement_id']

            self.xy = (self.measurement_values[['frq', 'amp']]
            [self.measurement_values['measurement_id'] == measurement_id].values.astype(
                'complex'))

            y = np.abs(self.xy[:, 1])
            x = self.xy[:, 0].real
            self.n_len = x.shape[0]  # frequency vector length

            try:
                self.singlefrf.clear()  # delete the older frf's
            except:
                pass  # if no previous single frf plot
            self.singlefrf = self.plot_area.plot(x, y)
            self.singlefrf.setPen(color=(125, 30, 125))

    def clear_single_frf(self):
        """ Clears the FRF plots. """
        self.singlefrf.clear()
        try:
            self.selection.selectionChanged.disconnect(self.handle_selection_changed)
        except:
            pass

    def frf_sum(self):
        """ Computes and plots the FRF sum (if checkbox is selected). """

        n = self.measurement_values['measurement_id'].shape[0] // self.n_len  # number of FRFs

        f = self.measurement_values['frq'].values[:self.n_len]
        frf_sum = np.sum(
            np.abs(self.measurement_values['amp'].values)[i * self.n_len:(i + 1) * self.n_len] for i in
            range(n)) / n
        self.frfsum = self.plot_area.plot(f, frf_sum)
        self.frfsum.setPen(color=(255, 0, 0))

    def cmif(self):
        """ Computes and plots the Complex mode indicator function (if checkbox is selected) """
        n = self.measurement_values['measurement_id'].shape[0] // self.n_len  # number of FRFs
        f = self.measurement_values['frq'].values[:self.n_len]

        h = np.zeros([1, n, self.n_len], dtype='complex')
        s = np.zeros(self.n_len)
        for i in range(n):
            h[0, i, :] = self.measurement_values['amp'].values[i * self.n_len:(i + 1) * self.n_len]

        for i in range(self.n_len):
            u, s[i], v = np.linalg.svd(np.imag(h[:, :, i]))

        cmif = s
        self.cmif_plot = self.plot_area.plot(f, cmif)
        self.cmif_plot.setPen(color=(0, 255, 0))

    def clear_frf_sum(self):
        """ Clears the FRF sum from the plot area. """
        self.frfsum.clear()

    def clear_cmif(self):
        """ Clears the CMIF from the plot area. """
        self.cmif_plot.clear()


class PropertiesTab(QtWidgets.QTabWidget):
    """
    Main class for the GUI of the Analysis tab.
    """

    def __init__(self):
        """
        Initializes the main GUI structure and connects it with data
        :param modaldata_object: mdd file
        :return: GUI
        """
        super().__init__()

        grid_layout = QtWidgets.QGridLayout()

        # table
        # self.data = modaldata_object

        # left table with reference and response nodes
        self.LeftDataModel = DataFrameModel()
        self.LeftDataTable = QtWidgets.QTableView()

        self.LeftDataTable.resizeColumnsToContents()
        self.LeftDataTable.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.LeftDataTable.setAlternatingRowColors(True)
        self.LeftDataTable.setSortingEnabled(True)

        self.LeftDataTable.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.LeftDataTable.setModel(self.LeftDataModel)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.LeftDataTable)

        # add the scatter plot for stabilisation, stable and unstable poles
        self.spots_plot = pg.ScatterPlotItem(pxMode=True)

        self.spots_plot.draw_selection = DrawSelection()

        # tables of selected natural frquencies and corresponding damping ratios
        self.spots_plot.dataModel = DataFrameModel()
        self.spots_plot.dataTable = QtWidgets.QTableView()
        self.spots_plot.dataTable.installEventFilter(self)

        self.spots_plot.dataTable.setModel(self.spots_plot.dataModel)
        self.spots_plot.dataTable.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Checkbox for FRF plot
        self.check_box_frf = QtWidgets.QCheckBox(kkeys['frf']['3'])

        self.check_box_frf.setChecked(False)

        # Connect frf checkbox with plot area
        self.check_box_frf.stateChanged.connect(self.plot_frfs)

        # Checkbox for sum of FRFs plot
        self.check_box_frf_sum = QtWidgets.QCheckBox(kkeys['sum']['3'])

        # Connect frf sum checkbox with plot area
        self.check_box_frf_sum.stateChanged.connect(self.plot_frf_sum)

        # Checkbox for CMIF plot
        self.check_box_cmif = QtWidgets.QCheckBox(kkeys['cmif']['15'])

        # Connect cmif checkbox with plot area
        self.check_box_cmif.stateChanged.connect(self.plot_cmif)

        # Label for selecting minimal freq. - f_min
        self.label_f_min = QtWidgets.QLabel(kkeys['freq_min']['15'])
        self.box_f_min = QtWidgets.QDoubleSpinBox()
        self.box_f_min.setMaximum(MAX_FREQUENCY)
        self.box_f_min.setMinimum(1)

        # Label for selecting maximal freq. - f_max
        self.label_f_max = QtWidgets.QLabel(kkeys['freq_max']['15'])
        self.box_f_max = QtWidgets.QDoubleSpinBox()
        self.box_f_max.setMaximum(MAX_FREQUENCY)

        # - (self.box_f_max.value() - self.box_f_min.value())/5
        # + (self.box_f_max.value() - self.box_f_min.value())/3.8)
        self.box_f_min.valueChanged.connect(
            lambda: self.spots_plot.draw_selection.plot_area.setXRange(self.box_f_min.value(), self.box_f_max.value()))

        self.box_f_max.valueChanged.connect(
            lambda: self.spots_plot.draw_selection.plot_area.setXRange(self.box_f_min.value(), self.box_f_max.value()))

        # Max order Button
        maxorder_label = QtWidgets.QLabel(kkeys['max_order']['15'])
        self.maxorder_spinbox = QtWidgets.QSpinBox()
        self.nmax = 30
        self.maxorder_spinbox.setValue(self.nmax)
        self.maxorder_spinbox.setMaximum(999)

        # Frequency error button
        err_freq_label = QtWidgets.QLabel(kkeys['freq_err']['15'])
        self.err_fn_button = QtWidgets.QDoubleSpinBox()
        self.err_fn_button.setRange(0, 1)
        self.err_fn_button.setDecimals(3)
        self.err_fn = 0.01
        self.err_fn_button.setValue(self.err_fn)

        # Damping error button
        err_damp_label = QtWidgets.QLabel(kkeys['damp_err']['15'])
        self.err_xi_button = QtWidgets.QDoubleSpinBox()
        self.err_xi_button.setRange(0, 1)
        self.err_xi_button.setDecimals(3)
        self.err_xi = 0.05
        self.err_xi_button.setValue(self.err_xi)

        # change model order
        self.maxorder_spinbox.valueChanged.connect(self.change_nmax)

        # change natrual frequency error
        self.err_fn_button.valueChanged.connect(self.change_err_fn)

        # change damping ratio error
        self.err_xi_button.valueChanged.connect(self.change_err_xi)

        # Define new child layout
        child_layout = QtWidgets.QHBoxLayout()
        child_layout.setContentsMargins(100, 20, 100, 100)

        # method selection combobox
        self.method_selection = QtWidgets.QComboBox()
        self.method_selection.addItem("LSCF")
        self.method_selection.addItem("LSCE")

        # model selection combobox
        self.button_model = QtWidgets.QComboBox()
        self.button_model.setObjectName('small')

        # update the analysis GUI, when another model is selected
        self.button_model.currentIndexChanged.connect(self.update_model)

        # Stabilization button
        run_icon = qta.icon('fa.play', scale_factor=1.6, color='white')
        self.stabilization_button_properties = QtWidgets.QPushButton(run_icon, ' Analyse')
        self.stabilization_button_properties.setObjectName('altpushbutton_measurement')
        self.stabilization_button_properties.setCheckable(False)

        # analysis_id selection
        self.analysis_id_label = QtWidgets.QLabel('Analysis id:')
        self.analysis_id_model = QtWidgets.QComboBox()

        # update the analysis GUI, when another analysis_id is selected
        self.analysis_id_model.currentIndexChanged.connect(self.update_analysis_id)

        # layout at the right
        self.right_child_layout = QtWidgets.QGridLayout()
        self.right_child_layout.addWidget(self.button_model, 0, 0, 1, 3)
        self.right_child_layout.addWidget(self.check_box_frf, 1, 0, 1, 1)
        self.right_child_layout.addWidget(self.check_box_frf_sum, 1, 1, 1, 1)
        self.right_child_layout.addWidget(self.check_box_cmif, 1, 2, 1, 1)
        self.right_child_layout.addWidget(self.method_selection, 2, 0, 1, 3)

        self.right_child_layout.addWidget(self.label_f_min, 3, 0, 1, 1)
        self.right_child_layout.addWidget(self.box_f_min, 3, 1, 1, 2)
        self.right_child_layout.addWidget(self.label_f_max, 4, 0, 1, 1)
        self.right_child_layout.addWidget(self.box_f_max, 4, 1, 1, 2)

        self.right_child_layout.addWidget(maxorder_label, 5, 0, 1, 1)
        self.right_child_layout.addWidget(self.maxorder_spinbox, 5, 1, 1, 2)
        self.right_child_layout.addWidget(err_freq_label, 6, 0, 1, 1)
        self.right_child_layout.addWidget(self.err_fn_button, 6, 1, 1, 2)
        self.right_child_layout.addWidget(err_damp_label, 7, 0, 1, 1)
        self.right_child_layout.addWidget(self.err_xi_button, 7, 1, 1, 2)

        self.right_child_layout.addWidget(self.stabilization_button_properties, 8, 0, 1, 3)
        self.right_child_layout.addWidget(self.analysis_id_label, 9, 0, 1, 1)
        self.right_child_layout.addWidget(self.analysis_id_model, 9, 1, 1, 2)
        self.right_child_layout.addWidget(self.spots_plot.dataTable, 10, 0, 1, 3)

        child_layout.addWidget(self.LeftDataTable)
        child_layout.setAlignment(self.LeftDataTable, QtCore.Qt.AlignTop)

        child_layout.addLayout(self.right_child_layout)
        child_layout.setAlignment(self.right_child_layout, QtCore.Qt.AlignRight|QtCore.Qt.AlignTop)

        grid_layout.addWidget(self.spots_plot.draw_selection, 0, 0, 100, 100)
        grid_layout.addLayout(child_layout, 5, 5)

        self.setLayout(grid_layout)

    # def ce_stabilisation(self, f, frf):
    #     n = np.zeros(self.Nmax, dtype='int')
    #
    #     self.draw_selection.spots_plot.fn_temp = np.zeros((2 * self.Nmax - 2, self.Nmax - 1), dtype='double')
    #     self.draw_selection.spots_plot.xi_temp = np.zeros((2 * self.Nmax - 2, self.Nmax - 1), dtype='double')
    #     test_fn = np.zeros((2 * self.Nmax - 2, self.Nmax - 1), dtype='int')
    #     test_xi = np.zeros((2 * self.Nmax - 2, self.Nmax - 1), dtype='int')
    #
    #     for i in range(1, self.Nmax):
    #         n[i] = i
    #         fn, xi, sr, vr, irf = ce.ce(frf, f, n[i], inputFRFtype='d')
    #         fn_temp, xi_temp, test_fn, test_xi = \
    #             stabilisation(fn, xi, n[i], self.draw_selection.spots_plot.fn_temp,
    #                           self.draw_selection.spots_plot.xi_temp, test_fn, test_xi, self.err_fn, self.err_xi)
    #
    #     return fn_temp, xi_temp, test_fn, test_xi

    def lsce_stabilisation(self, f, frf, low_lim):
        """
        Uses the LSCE method to get the eigenfrequencies and dampin ratios.

        :param f: frequency vector
        :param frf: frequency response function
        :param low_lim: lower limit of the frequency vector and the frequency
                        response function if the lower frequencies are not of
                        interest.
        :return fn_temp: updated eigenfrequencies matrix
        :return xi_temp: updated damping matrix
        :return test_fn: updated eigenfrequencies stabilisation test matrix
        :return test_xi: updated damping stabilisation test matrix
        """
        # this is done to avoid high computation times due to the properties of the fft
        nf = (2 * (len(f) - low_lim - 1))  # number of DFT frequencies (nf >> n)

        df = (f[1] - f[0])  # sampling frequency
        dt = 1 / (nf * df)  # sampling period

        frf = frf[0]  # LSCE method takes only one reference
        sr = lsce.lsce(frf, f[low_lim], low_lim, self.nmax, dt, reconstruction='LSFD')

        fn_temp, xi_temp, test_fn, test_xi = stabilisation(sr, self.nmax, self.err_fn, self.err_xi)

        return fn_temp, xi_temp, test_fn, test_xi


    def lscf_stabilisation(self, f, frf, low_lim):
        """
        Uses the LSCF method to get the eigenfrequencies and dampin ratios.

        :param f: frequency vector
        :param frf: frequency response function
        :param low_lim: lower limit of the frequency vector and the frequency
                        response function if the lower frequencies are not of
                        interest.
        :return fn_temp: updated eigenfrequencies matrix
        :return xi_temp: updated damping matrix
        :return test_fn: updated eigenfrequencies stabilisation test matrix
        :return test_xi: updated damping stabilisation test matrix
        """
        nf = 2 * (len(f) - 1)  # number of DFT frequencies (nf >> n)

        df = (f[1] - f[0])  # sampling frequency
        dt = 1 / (nf * df)  # sampling period

        # reshape the frf array to 2D
        frf = frf.reshape(frf.shape[0] * frf.shape[1], frf.shape[2])  # TODO: check if this holds for LSCF

        sr = lscf.lscf(frf, low_lim, self.nmax, dt, weighing_type='Unity', reconstruction='LSFD')

        fn_temp, xi_temp, test_fn, test_xi = stabilisation(sr, self.nmax, self.err_fn, self.err_xi)

        return fn_temp, xi_temp, test_fn, test_xi


    def stabilisation_diagrams(self, f, frf, method, low_lim=None):
        """
        Computes and displays the stabilisation charts.
        :param f: frequency vector
        :param frf: frequency response function
        :param method:  Identification method: 'LSCE' or 'LSCF'
        :param low_lim: lower limit of the frequency vector and the frequency
                        response function if the lower frequencies are not of
                        interest.
        :return: displayed stabilisation charts with selectable poles
        """

        select_model_id = (self.modaldata.tables['analysis_index'].loc[:, 'model_id'] ==
                           self.spots_plot.model_id)

        select_analysis_id = (self.modaldata.tables['analysis_index'].loc[:, 'analysis_id'] ==
                              self.spots_plot.analysis_id)

        select_model = select_model_id & select_analysis_id

        # complex nat. freq.
        lambdak = self.modaldata.tables['analysis_index'].loc[select_model, 'eig']
        nat_freq, dmp = complex_freq_to_freq_and_damp(lambdak)

        # Array to store natural frequencies and damping ratios
        self.spots_plot.nat_freq_dmp = np.zeros((0, 2))

        self.spots_plot.clear()  # clear the stabilisation plot
        # if method == 'ce':
        #     self.spots_plot.fn_temp, self.spots_plot.xi_temp, test_fn, test_xi = \
        #         self.ce_stabilisation(f, frf)

        self.spots_plot.method = method
        self.spots_plot.analysis_id = get_analysis_id(self.modaldata.tables['analysis_index'].loc[:, 'analysis_id'])

        # add analysis_id to GUI
        analysis_items = [self.analysis_id_model.itemText(i) for i in range(self.analysis_id_model.count())]
        if str(self.spots_plot.analysis_id) not in analysis_items:
            self.analysis_id_model.addItem(str(self.spots_plot.analysis_id))

            self.analysis_id_model.setCurrentIndex(self.analysis_id_model.count()-1)

        if self.spots_plot.method == 'lsce':
            self.spots_plot.fn_temp, self.spots_plot.xi_temp, self.test_fn, self.test_xi = \
                self.lsce_stabilisation(f, frf, low_lim)

        elif self.spots_plot.method == 'lscf':
            self.spots_plot.fn_temp, self.spots_plot.xi_temp, self.test_fn, self.test_xi = \
                self.lscf_stabilisation(f, frf, low_lim)

        f = f[low_lim:]
        frf = frf[:, :, low_lim:]
        spots, damp = stabilisation_plot_pyqtgraph(self.test_fn, self.test_xi, self.spots_plot.fn_temp,
                                             self.spots_plot.xi_temp)

        # updates the mdd with stabilisation spots positions
        save_stabilisation = np.array([[self.spots_plot.model_id, self.spots_plot.analysis_id, self.spots_plot.method,
                               i['pos'][0] + 1j*i['pos'][1], i['size'], i['pen']['color'], i['pen']['width'],
                               i['symbol'], i['brush'], damp[j]] for j, i in enumerate(spots)])

        self.modaldata.tables['analysis_stabilisation'] = save_stabilisation_spots(
            self.modaldata.tables['analysis_stabilisation'], save_stabilisation)

        self.spots_plot.stabilisation = save_stabilisation[:, [3, 9]].astype(complex)

        # adds stabilisation plots to GUI
        self.spots_plot.clear()
        self.spots_plot.draw_selection.fig.scene().removeItem(self.spots_plot.draw_selection.stabilisation_spots)

        self.spots_plot.addPoints(spots)

        # sets y-range on stabilisation spots
        self.spots_plot.draw_selection.stabilisation_spots.setRange(rect=None, xRange=None, yRange=(0, self.nmax),
                                                                    padding=None, update=True, disableAutoRange=True)

        # adds frf plots to GUI
        self.spots_plot.draw_selection.fig.scene().addItem(self.spots_plot.draw_selection.stabilisation_spots)

        # Connects stabilisation plots and frf plot views
        self.spots_plot.draw_selection.fig.getAxis('right').linkToView(
            self.spots_plot.draw_selection.stabilisation_spots)

        def update_views():
            """ Updates the stabilisation plot and links it to the x-axis of the FRF plot. """
            self.spots_plot.draw_selection.stabilisation_spots.setGeometry(
                self.spots_plot.draw_selection.fig.plotItem.vb.sceneBoundingRect())
            self.spots_plot.draw_selection.stabilisation_spots.linkedViewChanged(
                self.spots_plot.draw_selection.fig.plotItem.vb,
                self.spots_plot.draw_selection.stabilisation_spots.XAxis)

        update_views()

        self.spots_plot.draw_selection.fig.plotItem.vb.sigResized.connect(update_views)
        self.spots_plot.draw_selection.stabilisation_spots.addItem(self.spots_plot)

        self.spots_plot.fstab = f
        self.spots_plot.frfstab = frf

        self.spots_plot.save_points = np.zeros((0), dtype=complex)

        select_model_id = (self.modaldata.tables['analysis_index'].loc[:, 'model_id'] ==
                           self.spots_plot.model_id)

        select_analysis_id = (self.modaldata.tables['analysis_index'].loc[:, 'analysis_id'] ==
                              self.spots_plot.analysis_id)

        select_model = select_model_id & select_analysis_id

        self.spots_plot.spots = self.modaldata.tables['analysis_index'].loc[select_model, 'spots']

        # # Connect stabilisation plot selection to signals
        # self.spots_plot.sigClicked.connect(self.clicked)
        # self.spots_plot.sigClicked.connect(self.update_mdd)
        # self.spots_plot.sigClicked.connect(self.update_spots)
        # self.spots_plot.sigClicked.connect(self.set_table_height)

        selection = self.spots_plot.draw_selection.dataTable.selectionModel()
        # selection.selectionChanged.disconnect()
        selection.selectionChanged.connect(self.update_reconstruction)

    def clicked(self, points):
        """ Function dealing with clicked stabilisation poles. It computes
        and displays the reconstructed FRFs according to the elected poles
        and selected FRF (in the table).
        """

        p = points.ptsClicked[0]
        p.setPen('r', width=2)
        position = p.viewPos()

        if self.spots_plot.spots.shape[0] > 0:
            spot_in_data = np.isclose(self.spots_plot.spots.values.astype(complex),
                                      position.x() + 1j * position.y())
        else:
            spot_in_data = np.array(False)

        if spot_in_data.any():
            # if a point is double clicked deselect it
            p.resetPen()
            self.spots_plot.nat_freq_dmp = np.delete(self.spots_plot.nat_freq_dmp,
                                                     np.argwhere(spot_in_data), axis=0)
            self.spots_plot.save_points = np.delete(self.spots_plot.save_points,
                                                    np.argwhere(spot_in_data))

        else:
            stabilisation = self.spots_plot.stabilisation[
                int(np.argwhere(np.isclose(self.spots_plot.stabilisation[:, 0].astype(complex),
                                       position.x() + 1j * position.y()))), 1].real
            self.spots_plot.nat_freq_dmp = np.append(self.spots_plot.nat_freq_dmp,
                 np.array([[position.x(), stabilisation]], dtype=float), axis=0)
            self.spots_plot.save_points = np.append(self.spots_plot.save_points,
                                                    p._data[0] + 1j * p._data[1])

        # Update the dataframe
        self.spots_plot.dataModel.signal_update(
            pd.DataFrame(self.spots_plot.nat_freq_dmp, columns=['f [Hz]', 'ξ [/]']))

        # Reconstruction
        frq = self.spots_plot.dataModel.df.loc[:, 'f [Hz]'].values
        dmp = self.spots_plot.dataModel.df.loc[:, 'ξ [/]'].values
        ome = 2 * np.pi * frq
        self.spots_plot.lambdak = -dmp * ome - 1j * ome * np.sqrt(1 - dmp ** 2)  # complex frequency

        self.spots_plot.h, self.spots_plot.a, lr, ur = \
            lsfd.lsfd(self.spots_plot.lambdak, self.spots_plot.fstab, self.spots_plot.frfstab)

        # plot the reconstructed FRFs
        try:
            self.spots_plot.h_rec.clear()  # delete the older frf's
        except:
            pass  # if no previous single frf plot

        try:  # get the selected row
            row = self.spots_plot.draw_selection.index.row()
        except:  # no row is selected
            row = 0

        self.spots_plot.h_rec = self.spots_plot.draw_selection.plot_area.plot(
            self.spots_plot.fstab, np.abs(self.spots_plot.h[0, row, :].T))
        self.spots_plot.h_rec.setPen(color=(0, 0, 255))

    def update_spots(self):
        """
        Updates the analysis_index according to the selected spots
        """
        select_model_id = (self.modaldata.tables['analysis_index'].loc[:, 'model_id'] ==
                           self.spots_plot.model_id)

        select_method = (self.modaldata.tables['analysis_index'].loc[:, 'analysis_method'] ==
                              self.spots_plot.method)

        select_analysis_id = (self.modaldata.tables['analysis_index'].loc[:, 'analysis_id'] ==
                              self.spots_plot.analysis_id)

        select_model = select_model_id & select_method & select_analysis_id

        self.spots_plot.spots = self.modaldata.tables['analysis_index'].loc[
            select_model, 'spots']

    def update_reconstruction(self):
        """
        Plots the reconstructed FRFs according to the selected poles aon
        the stabilisation chart.
        """
        try:
            self.spots_plot.h_rec.clear()  # delete the older frf's
        except:
            pass  # if no previous single frf plot
        row = self.spots_plot.draw_selection.index.row()
        self.spots_plot.h_rec = self.spots_plot.draw_selection.plot_area.plot(self.spots_plot.fstab, np.abs(
            self.spots_plot.h[0, row, :].T))  # TODO: check this
        self.spots_plot.h_rec.setPen(color=(0, 0, 255))

    def update_mdd(self):
        """
        Updates the MDD file according to the selected identification points
        """
        self.modaldata = add_reconstruction_to_mdd(self.modaldata, self.spots_plot.model_id, self.spots_plot.lambdak,
                                                   self.spots_plot.a, self.spots_plot.method,
                                                   self.spots_plot.analysis_id, self.spots_plot.save_points)

        settings = self.modaldata.tables['analysis_settings']
        self.modaldata.tables['analysis_settings'] = save_analysis_settings(settings, self.spots_plot.model_id,
                                                        self.spots_plot.analysis_id, self.spots_plot.method,
                                                        self.box_f_min.value(), self.box_f_max.value(),
                                                        self.nmax, self.err_fn, self.err_xi)

    def update(self, modaldata_object):
        """Called when data is loaded/imported."""
        # Modal data object
        self.modaldata = modaldata_object

        #  Update models list
        models = self.modaldata.tables['info'].model_name

        # old_model_index = self.button_model.currentIndex()
        self.button_model.clear()
        self.button_model.addItems(models.values)

        self.spots_plot.model_id = self.button_model.count() - 1
        self.button_model.setCurrentIndex(self.spots_plot.model_id)

        # set column width
        self.spots_plot.dataTable.setColumnWidth(0, 125)
        self.spots_plot.dataTable.horizontalHeader().setStretchLastSection(True)
        self.spots_plot.dataTable.setFixedWidth(250)

        # selection model for measurement values
        self.select_model_meas = (self.modaldata.tables['measurement_values'].loc[:, 'model_id'] ==
                                  self.button_model.currentIndex())

        # set minimum  and maximum frequency values in the spinboxes
        try:
            self.f_min
            self.f_max
        except:
            if np.sum(self.select_model_meas) > 0:
                self.box_f_min.setValue((self.modaldata.tables['measurement_values'].loc[
                                             self.select_model_meas, 'frq'].values).min())
                self.box_f_max.setValue((self.modaldata.tables['measurement_values'].loc[
                                             self.select_model_meas, 'frq'].values).max())
            else:
                self.box_f_min.setValue(1)
                self.box_f_max.setValue(100)

            # frequency region for stabilization
            lr = pg.LinearRegionItem([self.box_f_min.value(), self.box_f_max.value()], movable=False,
                                     brush=pg.mkBrush(204, 91, 3, 100))  # , brush=pg.mkBrush(204, 91, 3, 100)

            # connect spinboxes with stabilisation plot linear region
            self.box_f_min.valueChanged.connect(
                lambda: lr.setRegion([self.box_f_min.value(), self.box_f_max.value()]))
            self.box_f_max.valueChanged.connect(
                lambda: lr.setRegion([self.box_f_min.value(), self.box_f_max.value()]))
            # self.spots_plot.draw_selection.plot_area.addItem(lr)

            # Disconnect old signals
            self.spots_plot.draw_selection.clear_single_frf()

            # Change state of the checkobox in order to trigger the signal
            self.check_box_frf.setChecked(False)
            self.check_box_frf.setChecked(True)

            # Deselect all rows (in order to detect signal change next)
            self.LeftDataTable.clearSelection()

            # Select the first row
            self.LeftDataTable.selectRow(0)

    def plot_frfs(self, state):
        """
        Fuction connecting the FRF checkbox with the plot area.
        :param state: Qt signal
        :return: plotted/cleared FRF on the plot area
        """
        if state == QtCore.Qt.Checked:
            measurement_index = self.modaldata.tables['measurement_index'][self.spots_plot.select_model]
            measurement_values = self.modaldata.tables['measurement_values'][
                self.spots_plot.select_model_meas_val]

            # TODO:
            # convert_frf(self.spots_plot.frf, 2*np.pi*self.spots_plot.f, self.spots_plot.frf_type.values, self.spots_plot.frf_type.values)

            self.spots_plot.draw_selection.measurement_index = measurement_index
            self.spots_plot.draw_selection.drawing_rows(measurement_index, measurement_values, self.LeftDataTable)
            self.LeftDataTable.selectRow(0)
        else:
            try:
                self.spots_plot.draw_selection.clear_single_frf()
            except:
                pass

    def plot_frf_sum(self, state):
        """
        Fuction connecting the FRF sum checkbox with the plot area.
        :param state: Qt signal
        :return: plotted/cleared FRF sum on the plot area
        """
        if state == QtCore.Qt.Checked:
            self.spots_plot.draw_selection.frf_sum()
        else:
            self.spots_plot.draw_selection.clear_frf_sum()

    def plot_cmif(self, state):
        """
        Fuction connecting the CMIF checkbox with the plot area.
        :param state: Qt signal
        :return: plotted/cleared FRF sum on the plot area
        """
        if state == QtCore.Qt.Checked:
            self.spots_plot.draw_selection.cmif()
        else:
            self.spots_plot.draw_selection.clear_cmif()

    def change_nmax(self):
        """ Changes model order. """
        self.nmax = self.maxorder_spinbox.value()

    def change_err_fn(self):
        """ Changes natural frequency error. """
        self.err_fn = self.err_fn_button.value()

    def change_err_xi(self):
        """ Changes damping ratio error. """
        self.err_xi = self.err_xi_button.value()

    def eventFilter(self, widget, event):
        """
        Event detection when the Delete key is pressed in the identification
        data table.
        """
        if (event.type() == QtCore.QEvent.KeyPress):

            key = event.key()
            if key == QtCore.Qt.Key_Delete:
                # get the tables
                index = self.modaldata.tables['analysis_index']
                values = self.modaldata.tables['analysis_values']

                # select the model according to model id and analysis method
                selected_model_index = index.loc[:, 'model_id'] == self.spots_plot.model_id
                selected_model_index = index[selected_model_index].loc[
                                       :, 'analysis_id'] == self.spots_plot.analysis_id

                index = index[selected_model_index]

                selected_model_values = values.loc[:, 'model_id'] == self.spots_plot.model_id
                selected_model_values = values[selected_model_values].loc[
                                        :, 'analysis_id'] == self.spots_plot.analysis_id

                values = values[selected_model_values]

                # get selected row
                rows = self.spots_plot.dataTable.selectedIndexes()

                for row in rows:
                    # update analysis values datatable
                    mode_n = index.iloc[row.row()].loc['mode_n']
                    condition = values.loc[:, 'mode_n'] != mode_n
                    self.modaldata.tables['analysis_values'][selected_model_values] = values[condition]

                    # remove nan rows
                    self.modaldata.tables['analysis_values'] = \
                        self.modaldata.tables['analysis_values'].dropna(axis=0, how='all').reset_index(drop=True)

                    # update analysis index datatable
                    index = index.drop(index.index[row.row()])

                    self.modaldata.tables['analysis_index'][selected_model_index] = index

                    self.modaldata.tables['analysis_index'] = \
                        self.modaldata.tables['analysis_index'].dropna(axis=0, how='all').reset_index(drop=True)

                    # calculate natural frequencies from complex natural frequencies
                    self.spots_plot.nat_freq_dmp = np.array(
                        complex_freq_to_freq_and_damp(index.loc[:, 'eig'].values)).T

                    # update the identification datatable
                    self.spots_plot.dataModel.signal_update(
                        pd.DataFrame(self.spots_plot.nat_freq_dmp, columns=['f [Hz]', 'ξ [/]']))

                    # adjustable table height according to number of rows
                    self.spots_plot.dataTable.setFixedHeight((self.spots_plot.nat_freq_dmp.shape[0] + 1) * 30 - 7)

                    # Reconstruction
                    frq = self.spots_plot.dataModel.df.loc[:, 'f [Hz]'].values
                    dmp = self.spots_plot.dataModel.df.loc[:, 'ξ [/]'].values
                    ome = 2 * np.pi * frq
                    self.spots_plot.lambdak = -dmp * ome - 1j * ome * np.sqrt(1 - dmp ** 2)  # complex frequency

                    h, a, lr, ur = lsfd.lsfd(self.spots_plot.lambdak, self.spots_plot.fstab, self.spots_plot.frfstab)

                    self.spots_plot.a = a

                    self.spots_plot.h = h

                    # plot the reconstructed FRFs
                    try:
                        self.spots_plot.h_rec.clear()  # delete the older frf's
                    except:
                        pass  # if no previous single frf plot

                    try:  # get the selected row
                        row = self.spots_plot.draw_selection.index.row()
                    except:  # no row is selected
                        row = 0

                    self.spots_plot.h_rec = self.spots_plot.draw_selection.plot_area.plot(self.spots_plot.fstab, np.abs(
                        self.spots_plot.h[0, row, :].T))
                    self.spots_plot.h_rec.setPen(color=(0, 0, 255))

        return QtWidgets.QWidget.eventFilter(self, widget, event)

    def set_table_height(self):
        """
        Adjusts the LeftDataTable (FRF table) and the dataTable
        (identified modal parameters table) height according to the
        number of rows. If the height is to large, it is adjusted
        according to canvas (plot_area).
        """

        # canvas (plot_area) height
        height = self.spots_plot.draw_selection.plot_area.viewGeometry().height()

        # LeftDataTable - if the height is too large, use canvas height
        if height - 30 < (self.LeftDataModel.df.shape[0] + 1) * 30 - 7:
            self.LeftDataTable.setFixedHeight(height - 30)

        else:  # use row height
            self.LeftDataTable.setFixedHeight((self.LeftDataModel.df.shape[0] + 1) * 30 - 7)

        # dataTable - if the height is too large, use canvas height
        if height - 347 < ((self.spots_plot.nat_freq_dmp.shape[0] + 1) * 30 - 7):
            self.spots_plot.dataTable.setFixedHeight(height - 347)

        else:  # use row height
            self.spots_plot.dataTable.setFixedHeight((self.spots_plot.nat_freq_dmp.shape[0] + 1) * 30 - 7)

    def update_model(self):
        """
        Updates the data when the Analysis button is clicked
        """
        # self.spots_plot.f, self.spots_plot.frf  m

        # get model id according to selection in combo box
        self.spots_plot.model_id = self.button_model.currentIndex()

        # get selected FRFs in the table according to model id
        self.spots_plot.select_model = (self.modaldata.tables['measurement_index'].loc[:, 'model_id']
                                        == self.spots_plot.model_id)

        self.spots_plot.select_model_meas_val = (
            self.modaldata.tables['measurement_values'].loc[:, 'model_id']
            == self.spots_plot.model_id)

        # get FRF types
        self.spots_plot.frf_type = self.modaldata.tables['measurement_index'] \
                                       [self.spots_plot.select_model].loc[:, ['ordinate_spec_data_type',
                                                                              'orddenom_spec_data_type']]
        self.spots_plot.frf_type = get_frf_type(self.spots_plot.frf_type.values)

        # get the FRF from mdd file
        self.spots_plot.frf, self.spots_plot.f = get_frf_from_mdd(
            self.modaldata.tables['measurement_values'][self.spots_plot.select_model_meas_val], \
            self.modaldata.tables['measurement_index'][self.spots_plot.select_model])

        # update the data model
        self.LeftDataModel.signal_update(self.modaldata.tables['measurement_index'].loc[
            self.spots_plot.select_model, MEASUREMENT_INDEX_SELECT].reset_index(
            drop=True))

        # Set data table (GUI) according to data model
        self.LeftDataTable.setModel(self.LeftDataModel)

        # Adjust data table columns width
        self.LeftDataTable.setColumnWidth(0, 90)
        # self.LeftDataTable.setColumnWidth(1, 100)
        self.LeftDataTable.horizontalHeader().setStretchLastSection(True)
        self.LeftDataTable.setFixedWidth(200)

        # Select the first row
        self.LeftDataTable.selectRow(0)

        # Change state of the checkobox in order to trigger the signal
        self.check_box_frf.setChecked(False)
        self.check_box_frf.setChecked(True)

        # Deselect all rows (in order to detect signal change next)
        self.LeftDataTable.clearSelection()

        # Select the first row
        self.LeftDataTable.selectRow(0)

        # delete the reconstructed FRFs from other model
        try:
            self.spots_plot.h_rec.clear()  # delete the older frf's
        except:
            pass

        # get geometry node numbers
        self.spots_plot.node_nums = self.modaldata.tables[
            'measurement_index'][self.spots_plot.select_model]['rsp_node'].values

        # The selected identification method
        select_model_id = (self.modaldata.tables['analysis_settings'].loc[:, 'model_id'] ==
                         self.spots_plot.model_id)

        select_method = (self.modaldata.tables['analysis_settings'].loc[:, 'analysis_method'] ==
                         self.spots_plot.method)

        select_analysis_ids = select_model_id & select_method

        # get all analysis_id's
        analysis_ids = self.modaldata.tables['analysis_settings'][select_analysis_ids]
        analysis_ids = analysis_ids.loc[:, 'analysis_id'].astype(int).astype(str).tolist()

        self.analysis_id_model.clear()
        self.analysis_id_model.addItems(analysis_ids)

        if len(analysis_ids) == 0:
            pass # TODO

        # set analysis_id
        nr_of_analysis_ids = self.analysis_id_model.count()

        if nr_of_analysis_ids > 0:
            self.spots_plot.analysis_id = nr_of_analysis_ids - 1
            self.analysis_id_model.setCurrentIndex(nr_of_analysis_ids - 1)
        else:
            self.spots_plot.analysis_id = np.nan

        select_model_id = (self.modaldata.tables['analysis_index'].loc[:, 'model_id'] ==
                           self.spots_plot.model_id)

        select_analysis_id = (self.modaldata.tables['analysis_index'].loc[:, 'analysis_id'] ==
                              self.spots_plot.analysis_id)

        select_model = select_model_id & select_analysis_id

        # complex nat. freq.
        lambdak = self.modaldata.tables['analysis_index'].loc[select_model, 'eig']
        nat_freq, dmp = complex_freq_to_freq_and_damp(lambdak)

        # Array to store natural frequencies and damping ratios
        self.spots_plot.nat_freq_dmp = np.array((nat_freq, dmp)).T

        # Update the eigenfrequencies and damping ratios table
        self.spots_plot.dataModel.signal_update(
            pd.DataFrame(self.spots_plot.nat_freq_dmp, columns=['f [Hz]', 'ξ [/]']))

        # Adjustable table height
        self.spots_plot.draw_selection.plot_area.sigYRangeChanged.connect(self.set_table_height)

    def update_analysis_id(self):
        """
        Updates the identification widget according to the selected analysis_id
        """

        self.spots_plot.analysis_id = self.analysis_id_model.currentIndex()

        if self.spots_plot.analysis_id > -1:
            # get analysis_index
            index = self.modaldata.tables['analysis_index']

            # select the model according to model id and analysis method
            selected_model_index = index.loc[:, 'model_id'] == self.spots_plot.model_id
            selected_model_index = index[selected_model_index].loc[
                                   :, 'analysis_id'] == self.spots_plot.analysis_id

            index = index[selected_model_index]

            # calculate natural frequencies from complex natural frequencies
            self.spots_plot.lambdak = index.loc[:, 'eig'].values
            self.spots_plot.nat_freq_dmp = np.array(
                complex_freq_to_freq_and_damp(self.spots_plot.lambdak)).T

            self.spots_plot.dataModel.signal_update(
                pd.DataFrame(self.spots_plot.nat_freq_dmp, columns=['f [Hz]', 'ξ [/]']))

            # get the data from analysis settings
            settings = self.modaldata.tables['analysis_settings']
            self.set_analysis_settings(settings)

            # get saved point
            self.spots_plot.save_points = index.loc[:, 'spots'].values

            # Update stabilisation plot
        # set up stabilisation spots
        select_analysis_model = self.modaldata.tables['analysis_stabilisation'].loc[:,
                                'model_id'] == self.spots_plot.model_id
        select_analysis_analysis = self.modaldata.tables['analysis_stabilisation'].loc[:, 'analysis_id'] == self.spots_plot.analysis_id
        select_analysis_method = self.modaldata.tables['analysis_stabilisation'].loc[:, 'analysis_method'] == self.spots_plot.method

        select_analysis = select_analysis_model & select_analysis_analysis & select_analysis_method
        stabilisation = self.modaldata.tables['analysis_stabilisation'][select_analysis]

        spots = stabilisation.loc[:, ['pos', 'size', 'pen_color', 'pen_width', 'symbol', 'brush']]

        spots = [{'pos': (i[0].real, i[0].imag, i[0].imag + 1), 'size': i[1],
                  'pen': {'color': i[2], 'width': i[3]}, 'symbol': i[4],
                  'brush': i[5]} for i in spots.values]

        self.spots_plot.stabilisation = stabilisation.loc[:, ['pos', 'damp']].values

        # self.spots_plot.clear()
        self.spots_plot.clear()
        self.spots_plot.draw_selection.fig.scene().removeItem(self.spots_plot.draw_selection.stabilisation_spots)
        self.spots_plot.addPoints(spots)

        # sets y-range on stabilisation spots
        self.spots_plot.draw_selection.stabilisation_spots.setRange(rect=None, xRange=None, yRange=(0, self.nmax),
                                                                    padding=None, update=True, disableAutoRange=True)

        # adds frf plots to GUI
        self.spots_plot.draw_selection.fig.scene().addItem(self.spots_plot.draw_selection.stabilisation_spots)

        # Connects stabilisation plots and frf plot views
        self.spots_plot.draw_selection.fig.getAxis('right').linkToView(
            self.spots_plot.draw_selection.stabilisation_spots)

        def update_views():
            """ Updates the stabilisation plot and links it to the x-axis of the FRF plot. """
            self.spots_plot.draw_selection.stabilisation_spots.setGeometry(
                self.spots_plot.draw_selection.fig.plotItem.vb.sceneBoundingRect())
            self.spots_plot.draw_selection.stabilisation_spots.linkedViewChanged(
                self.spots_plot.draw_selection.fig.plotItem.vb,
                self.spots_plot.draw_selection.stabilisation_spots.XAxis)

        update_views()

        self.spots_plot.draw_selection.fig.plotItem.vb.sigResized.connect(update_views)
        self.spots_plot.draw_selection.stabilisation_spots.addItem(self.spots_plot)

        try:
            self.spots_plot.sigClicked.disconnect()  # if stabilisation button is clicked
            # more than once, delete the last signal
        except Exception as error:
            print('ERROR: ', error)

        # select the stored points (from analysis_index mdd table)
        select_model_id = (self.modaldata.tables['analysis_index'].loc[:, 'model_id'] ==
                           self.spots_plot.model_id)

        select_method = (self.modaldata.tables['analysis_index'].loc[:, 'analysis_method'] ==
                           self.spots_plot.method)

        select_analysis_id = (self.modaldata.tables['analysis_index'].loc[:, 'analysis_id'] ==
                              self.spots_plot.analysis_id)

        select_model = select_model_id & select_method & select_analysis_id

        self.spots_plot.spots = self.modaldata.tables['analysis_index'].loc[select_model, 'spots']

        for i in self.spots_plot.spots.values:
            # compare the selected points, with the points from stailisation mdd table
            points = np.array(stabilisation.loc[:, 'pos'].values, dtype=complex)
            index = int(np.argwhere(np.isclose(i, points))[0][0])

            # plot the selected point bold and red
            self.spots_plot.points()[index]._data[7].setPen('r', width=2)

        self.spots_plot.sigClicked.connect(self.clicked)
        self.spots_plot.sigClicked.connect(self.update_mdd)
        self.spots_plot.sigClicked.connect(self.update_spots)
        self.spots_plot.sigClicked.connect(self.set_table_height)


    def set_analysis_settings(self, settings):
        """
        Sets analysis settings according to the selected analysis_id

        :param settings: analysis_settings table in the mdd
        :return: updated analysis settings
        """

        # get the selected model
        selected_model = settings.loc[:, 'model_id'] == self.spots_plot.model_id
        selected_model = settings[selected_model].loc[:, 'analysis_id'] == self.spots_plot.analysis_id

        if np.sum(selected_model) == 1:
            # set values froma analysis_settings
            *_, self.f_min, self.f_max, self.nmax, self.err_fn, self.err_xi = settings[selected_model].iloc[0]

            self.box_f_min.setValue(self.f_min)
            self.box_f_max.setValue(self.f_max)
            self.maxorder_spinbox.setValue(self.nmax)
            self.err_fn_button.setValue(self.err_fn)
            self.err_xi_button.setValue(self.err_xi)

            # get the frequency vector and frquency response function
            limits = (self.spots_plot.f <= self.f_max + ALLOWED_ERROR) & (self.spots_plot.f >= self.f_min)
            self.spots_plot.fstab = self.spots_plot.f[limits]
            self.spots_plot.frfstab = self.spots_plot.frf[:, :, limits]

            # compute the reconstruction
            self.spots_plot.h, self.spots_plot.a, lr, ur = lsfd.lsfd(self.spots_plot.lambdak, self.spots_plot.fstab, self.spots_plot.frfstab)

            # draw reconstructed frfs
            selection = self.spots_plot.draw_selection.dataTable.selectionModel()
            # selection.selectionChanged.disconnect()
            selection.selectionChanged.connect(self.update_reconstruction)

            # Select the first row
            self.LeftDataTable.selectRow(1)
            self.LeftDataTable.selectRow(0)
