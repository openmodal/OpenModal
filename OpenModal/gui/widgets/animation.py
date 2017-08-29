
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


__author__ = 'Miha'

import pandas as pd

from PyQt5 import QtCore, QtWidgets

from PyQt5 import QtGui, QtWidgets

import pyqtgraph.opengl as gl

import pyqtgraph as pg

import numpy as np

from pyqtgraph.parametertree import Parameter

from OpenModal.anim_tools import CUBE,COLORS,CustomGLMeshItem,AnimWidgBase

from OpenGL.GL import *

import qtawesome as qta

from OpenModal.keys import keys

if __name__ == '__main__':
    from OpenModal.languages import LANG_DICT
else:
    from OpenModal.gui.widgets.languages import LANG_DICT

from functools import partial

import datetime as tm

# Warning controls
# import warnings
#warnings.filterwarnings('error')
#warnings.simplefilter('error', FutureWarning)
#np.seterr(all='raise')

# ## Switch to using white background and black foreground
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

WIDGET_MODES = ['raw_data', 'EMA', 'ODS']

SHADER='OpenModal'

GLOPTS= {
        GL_DEPTH_TEST: True,
        GL_BLEND: False,
        GL_ALPHA_TEST: False,
        GL_CULL_FACE: False}
        #'glLightModeli':(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)}
SMOOTH=False # If TRUE then normals are recomputed when new triangles are added
COMPUTENORMALS=True
DRAW_EDGES_NODES=False
DRAW_EDGES_ELEMENTS=True
DRAW_EDGES_GCS=False
DRAW_EDGES_LCS=False


class CustomPlotCurveItem(pg.PlotCurveItem):

    pltClicked = QtCore.pyqtSignal()

    def __init__(self, parent = None, *args, **kwargs):
        super(CustomPlotCurveItem, self).__init__(parent, *args, **kwargs)

    def mousePressEvent(self, ev):
        super(CustomPlotCurveItem, self).mousePressEvent(ev)
        self.pltClicked.emit()


class TableModel(QtCore.QAbstractTableModel):
    '''Table model that suits all tables (for now). It specifies
    access to data and some other stuff.'''

    def __init__(self, parent, *args):
        super(TableModel, self).__init__(parent, *args)
        self.datatable = None

        self.header_labels=[]

    def update(self, dataIn, model_id_list,fields):
        self.layoutAboutToBeChanged.emit()
        self.dataIn = dataIn
        self.datatable = dataIn[dataIn['model_id'].isin(model_id_list)][fields]
        self.layoutChanged.emit()

    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.datatable.index)

    def columnCount(self, parent=QtCore.QModelIndex()):
        return len(self.datatable.columns.values)

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            try:
                return self.header_labels[col]
            except:
                return 'empty'
        return None

    def setData(self, index, value, role):
        row = self.datatable.index[index.row()]
        col = self.datatable.columns[index.column()]
        if hasattr(value, 'toPyObject'):
            # Only for PyQt4? (QVariant)
            value = value.toPyObject()
        else:
            # Only for PySide? (Unicode)
            dtype = self.datatable[col].dtype
            if dtype != object:
                value = None if value == '' else dtype.type(value)


        try:
            self.datatable.ix[row,col]=float(value)
        except:
            #TODO: check input data
            print('only floats allowed')

        self.dataIn.update(self.datatable)
        #self.dataChanged.emit()
        self.dataChanged.emit(self.createIndex(0, 0),
                           self.createIndex(self.rowCount(0),
                                            self.columnCount(0)))
        return True

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None

        i = index.row()
        j = index.column()
        if '{0}'.format(self.datatable.iat[i, j])=='nan':
            return ''
        else:
            return '{0}'.format(self.datatable.iat[i, j])

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



class Error(Exception):
    #TODO: error handling
    """Base class for exceptions in this module."""
    pass


class AnimationWidget(AnimWidgBase):
    ''' Central widget for main window - creating GUI elements '''


    # def __init__(self, modaldata_object, status_bar, language, preferences=dict(), desktop_widget=None, parent=None):
    def __init__(self, *args, **kwargs):
        # Initialize the object as a QWidget and
        # set its title and minimum width
        super(AnimationWidget, self).__init__(*args, **kwargs)

        #default widget mode
        self.widget_mode = 'raw_data'

        #for timing animations
        self.anim_timer = QtCore.QTimer(self)


    def cell_hover(self, index):

        self.current_hover = [index.row(), index.column()]

    def handle_selection_changed(self, selected, deselected):
        """
        Get selected table row (mode) and give it to model object
        :param selected:
        :param deselected:
        :return:
        """
        for index in self.table_view.selectionModel().selectedRows():
            selected = index.row()

        #print(self.table_model.datatable.iloc[selected])

        selected_mode_n = self.table_model.datatable.iloc[selected]['mode_n'].real
        selected_mode_ana_id = self.table_model.datatable.iloc[selected]['analysis_id'].real
        selected_model_id = self.table_model.datatable.iloc[selected]['model_id']
        for model_id, model_obj in self.models.items():
            #model_obj.selected_uffid = selected_uffid
            model_obj.selected_mode=selected_mode_n
            model_obj.selected_mode_ana_id=selected_mode_ana_id
            model_obj.selected_model_id = selected_model_id

        # start animation
        self.animate()

    def create_2dview_actions(self):

        self.plot_all_frfs_act = QtWidgets.QAction(LANG_DICT[self._lang]['2D_view_cnt_menu_allFRF_txt'], self, checkable=True,
                                             statusTip=LANG_DICT[self._lang]['2D_view_cnt_menu_allFRF_statustip'],
                                             triggered=self.set_2d_view_settings)
        self.plot_frf_sum_act = QtWidgets.QAction("FRF sum", self, checkable=True,
                                            statusTip="Plot sum of all available FRFs",
                                            triggered=self.set_2d_view_settings)
        self.plot_frf_sum_act.setChecked(True)  # by default FRF sum is plotted


    def create_model_view_actions(self):

        super(self.__class__,self).create_model_view_actions()

        self.anim_25_fpc_act = QtWidgets.QAction('25 frames/cycle', self, checkable=True,
                                           statusTip='Set animation speed', triggered=self.anim_25_fpc)

        self.anim_50_fpc_act = QtWidgets.QAction('50 frames/cycle', self, checkable=True,
                                           statusTip='Set animation speed', triggered=self.anim_50_fpc)
        self.anim_50_fpc_act.setChecked(True)

        self.anim_75_fpc_act = QtWidgets.QAction('75 frames/cycle', self, checkable=True,
                                           statusTip='Set animation speed', triggered=self.anim_75_fpc)

        self.anim_100_fpc_act = QtWidgets.QAction('100 frames/cycle', self, checkable=True,
                                            statusTip='Set animation speed', triggered=self.anim_100_fpc)

        self.set_rsp_rove_act = QtWidgets.QAction('Response roved', self, checkable=True,
                                            statusTip='Set roving type', triggered=self.set_rsp_rove)
        self.set_rsp_rove_act.setChecked(True)

        self.set_ref_rove_act = QtWidgets.QAction('Reference roved', self, checkable=True,
                                            statusTip='Set roving type', triggered=self.set_ref_rove)

        self.set_ref_x_act = QtWidgets.QAction('Use X', self, checkable=True,
                                            statusTip='Use reference direction x', triggered=self.set_ref_x)
        self.set_ref_x_act.setChecked(True)

        self.set_ref_y_act = QtWidgets.QAction('Use Y', self, checkable=True,
                                            statusTip='Use reference direction y', triggered=self.set_ref_y)
        self.set_ref_y_act.setChecked(True)

        self.set_ref_z_act = QtWidgets.QAction('Use Z', self, checkable=True,
                                            statusTip='Use reference direction z', triggered=self.set_ref_z)
        self.set_ref_z_act.setChecked(True)

    def create_toolbar_actions(self):

        super(self.__class__,self).create_toolbar_actions()

        self.act_anim_stop = QtWidgets.QAction(QtGui.QIcon('gui/icons/icon_anim_pause.png'), 'Stop', self,
                                         statusTip='Stop animation', triggered=self.animation_stop)

        self.act_anim_play = QtWidgets.QAction(QtGui.QIcon('gui/icons/icon_anim_play.png'), 'Play', self,
                                         statusTip='Start animation', triggered=self.animate)

        self.act_analysis_data_mode = QtWidgets.QAction('Analysis mode', self,
                                                  statusTip='Open analysis mode', triggered=self.analysis_data_mode)

        self.act_measurment_data_mode = QtWidgets.QAction('Measurement mode', self,
                                                    statusTip='Open measurement mode',
                                                    triggered=self.measurement_data_mode)

    def model_view_context_menu(self, pos):

        menu = QtWidgets.QMenu()
        menu.addAction(self.act_anim_play)
        menu.addAction(self.act_anim_stop)
        menu.addAction(self.act_fit_view)

        display_menu = menu.addMenu('Display')
        display_menu.addAction(self.plot_nodes_act)
        display_menu.addAction(self.plot_elements_act)
        display_menu.addAction(self.plot_node_lcs_act)
        display_menu.addAction(self.plot_node_labels_act)
        display_menu.addAction(self.plot_gcs_act)
        #node_menu.addMenu('Trace lines')

        color_menu = menu.addMenu('Colors')
        color_menu.addAction(self.node_color_act)
        color_menu.addAction(self.line_color_act)
        color_menu.addAction(self.elem_color_act)

        animation_menu = menu.addMenu('Animation')
        animation_menu.addAction(self.anim_25_fpc_act)
        animation_menu.addAction(self.anim_50_fpc_act)
        animation_menu.addAction(self.anim_75_fpc_act)
        animation_menu.addAction(self.anim_100_fpc_act)

        reference_menu = menu.addMenu('Reference direction filter')
        reference_menu.addAction(self.set_ref_x_act)
        reference_menu.addAction(self.set_ref_y_act)
        reference_menu.addAction(self.set_ref_z_act)

        roving_menu = menu.addMenu('Roving type')
        roving_menu.addAction(self.set_rsp_rove_act)
        roving_menu.addAction(self.set_ref_rove_act)


        menu.exec_(QtGui.QCursor.pos())

    def set_ref_x(self):
        '''
        Set reference direction filter. Specifies which reference directions
        are used for generating animations in 'raw data' mode.
        :return:
        '''

        #check if ref dir x is checked
        set_ref_x_act = self.set_ref_x_act.isChecked()
        #if you clicked on checked item, then set_ref_x_act will be FALSE

        if set_ref_x_act:
            #if previously checked - turn of x direction
            for model_id, model_obj in self.models.items():
                model_obj.reference_map['x']['use']=True
            self.set_ref_x_act.setChecked(True)
        else:
            for model_id, model_obj in self.models.items():
                model_obj.reference_map['x']['use']=False
            self.set_ref_x_act.setChecked(False)

    def set_ref_y(self):
        '''
        Set reference direction filter. Specifies which reference directions
        are used for generating animations in 'raw data' mode.
        :return:
        '''

        #check if ref dir x is checked
        set_ref_y_act = self.set_ref_y_act.isChecked()

        if set_ref_y_act:
            #if previously checked - turn of x direction
            for model_id, model_obj in self.models.items():
                model_obj.reference_map['y']['use']=True
            self.set_ref_y_act.setChecked(True)
        else:
            for model_id, model_obj in self.models.items():
                model_obj.reference_map['y']['use']=False
            self.set_ref_y_act.setChecked(False)

    def set_ref_z(self):
        '''
        Set reference direction filter. Specifies which reference directions
        are used for generating animations in 'raw data' mode.
        :return:
        '''

        #check if ref dir x is checked
        set_ref_z_act = self.set_ref_z_act.isChecked()

        if set_ref_z_act:
            #if previously checked - turn of x direction
            for model_id, model_obj in self.models.items():
                model_obj.reference_map['z']['use']=True
            self.set_ref_z_act.setChecked(True)
        else:
            for model_id, model_obj in self.models.items():
                model_obj.reference_map['z']['use']=False
            self.set_ref_z_act.setChecked(False)

    def set_rsp_rove(self):
        '''
        Set response rove type for ALL models
        :return:
        '''
        self.set_rsp_rove_act.setChecked(True)
        self.set_ref_rove_act.setChecked(False)
        for model_id, model_obj in self.models.items():
            model_obj.roving_type='rsp_roved'

    def set_ref_rove(self):
        '''
        Set reference rove type for ALL models
        :return:
        '''
        self.set_rsp_rove_act.setChecked(False)
        self.set_ref_rove_act.setChecked(True)
        for model_id, model_obj in self.models.items():
            model_obj.roving_type='ref_roved'

    def anim_25_fpc(self):
        '''
        Set frame rate for animation (frames per cycle)
        :return:
        '''
        self.anim_25_fpc_act.setChecked(True)
        self.anim_50_fpc_act.setChecked(False)
        self.anim_75_fpc_act.setChecked(False)
        self.anim_100_fpc_act.setChecked(False)
        for model_id, model_obj in self.models.items():
            model_obj.fpc = 25

    def anim_50_fpc(self):
        '''
        Set frame rate for animation (frames per cycle)
        :return:
        '''
        self.anim_25_fpc_act.setChecked(False)
        self.anim_50_fpc_act.setChecked(True)
        self.anim_75_fpc_act.setChecked(False)
        self.anim_100_fpc_act.setChecked(False)
        for model_id, model_obj in self.models.items():
            model_obj.fpc = 50

    def anim_75_fpc(self):
        '''
        Set frame rate for animation (frames per cycle)
        :return:
        '''
        self.anim_25_fpc_act.setChecked(False)
        self.anim_50_fpc_act.setChecked(False)
        self.anim_75_fpc_act.setChecked(True)
        self.anim_100_fpc_act.setChecked(False)
        for model_id, model_obj in self.models.items():
            model_obj.fpc = 75

    def anim_100_fpc(self):
        '''
        Set frame rate for animation (frames per cycle)
        :return:
        '''
        self.anim_25_fpc_act.setChecked(False)
        self.anim_50_fpc_act.setChecked(False)
        self.anim_75_fpc_act.setChecked(False)
        self.anim_100_fpc_act.setChecked(True)
        for model_id, model_obj in self.models.items():
            model_obj.fpc = 100


    def set_2d_view_settings(self):
        '''
        Trigger 2d view refresh via self.plot_activated_models
        :return:
        '''
        #check if node lcs need to be ploted (via context menu)
        plot_all_frfs_act = self.plot_all_frfs_act.isChecked()
        plot_frf_sum_act = self.plot_frf_sum_act.isChecked()

        for model_id, model_obj in self.models.items():
            model_obj.plot_2d_all_frfs = plot_all_frfs_act
            model_obj.plot_2d_frf_sum = plot_frf_sum_act
            model_obj.needs_refresh_2d = True

        self.plot_activated_models(wheel_event=True)


    def create_2dplot_widget(self):
        """
        Create 2D plot widget and fill it with some default data
        :return:
        """

        # Create 2D plot widget
        self.plot_widget = pg.PlotWidget(self,title='')
        self.plot_area = self.plot_widget.plotItem

        # create context view actions
        self.create_2dview_actions()
        data_menu = QtWidgets.QMenu("Data Options")
        data_menu.addAction(self.plot_frf_sum_act)
        data_menu.addAction(self.plot_all_frfs_act)

        # option 1
        self.plot_area.ctrlMenu = [data_menu, self.plot_area.ctrlMenu]

        # option 2
        #self.plot_area.ctrlMenu.addAction(self.plot_frf_sum_act)
        #self.plot_area.ctrlMenu.addAction(self.plot_all_frfs_act)

        #self.plot_area.plot(def_data_x, def_data_y)
        self.plot_area.setLabel('bottom', 'Frequency [Hz]')
        self.plot_area.setLabel('left', 'Amplitude [/]')

        #add label for use with cross hair and mouse move events
        self.label = pg.LabelItem(justify='left')
        self.label.setParentItem(self.plot_area)  # so that text is show outside graph

        #cross hair
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.hLine = pg.InfiniteLine(angle=0, movable=False)
        self.plot_area.addItem(self.vLine, ignoreBounds=True)
        self.plot_area.addItem(self.hLine, ignoreBounds=True)

        #selection line
        self.line_pen = (0, 255, 0)  # mkPen for curve
        self.sel_freq_vLine = pg.InfiniteLine(angle=90, movable=False, pen=self.line_pen)
        self.plot_area.addItem(self.sel_freq_vLine, ignoreBounds=True)

        vb = self.plot_area.vb

        # Mouse events binding
        self.plot_area.scene().sigMouseMoved.connect(self.mouse_moved)
        self.plot_area.scene().sigMouseClicked.connect(self.mouse_clicked)
        self.plot_area.legend = self.plot_area.addLegend()

    def mouse_moved(self, evt):
        """
        For 2D plot cross hair
        :param evt: PySide.QtCore.QPointF in scene coordinates
        :return:
        """

        if self.plot_area.sceneBoundingRect().contains(evt):
            mousePoint = self.plot_area.vb.mapSceneToView(evt)
            itemname=''

            #check if mouse position is contained in curve path
            for item in self.plot_area.scene().items():
                if isinstance(item, CustomPlotCurveItem):

                    if item.mouseShape().contains(mousePoint):
                        itemname=item.name()

            for model_id, model_obj in self.models.items():
                if model_obj.activated:
                    current_freq=model_obj.anim_freq

            self.label.setText("<span style='font-size: 12pt'><span style='color: green'>Selected freq.=%0.1f Hz</span>, <span style='font-size: 12pt'>x=%0.1f,   <span style='color: red'>y1=%0.1f</span>,   <span style='color: green'>%s</span>" % (
                current_freq,mousePoint.x(), mousePoint.y(),itemname))
            self.vLine.setPos(mousePoint.x())
            self.hLine.setPos(mousePoint.y())


    def mouse_clicked(self, evt):
        """
        For 2D plot cross hair selection
        :param evt:
        :return:
        """

        if self.plot_area.sceneBoundingRect().contains(evt.scenePos()):
            try:
                mousePoint = self.plot_area.vb.mapSceneToView(evt.scenePos())
                for model_id, model_obj in self.models.items():
                    if model_obj.activated:
                        model_obj.anim_freq = mousePoint.x()
                        #self.tree_params.param(model_obj.name)['Selected frequency:'] = mousePoint.x()
                        # selected frequency change event is caught in the 'build_uff_tree' method

                #move selection line if not existing
                self.sel_freq_vLine.setPos(mousePoint.x())

            except:
                print('exception in mouseClicked method')

    def paintEvent(self, event):

        # button sizes
        w = 140
        h = 33
        border_thk=1

        # app window size
        window_width=self.rect().width()
        window_height=self.rect().height()

        # global positioning of buttons
        x_margin=20
        x = (window_width  - w - x_margin-2*border_thk)
        y = 0.2*window_height
        offset=h+5


        # relative positioning of buttons
        self._btn_play.setGeometry(x,y,w,h)
        self._btn_pause.setGeometry(x,y+offset,w,h)
        self._btn_fit_view.setGeometry(x,y+2*offset,w,h)

        self._btn_slider_background.setGeometry(x,y+3*offset,w,h)
        self.anim_scale_slider.setGeometry(x,y+3*offset+2.2*h/3,w,h)

        # positioning of elements/geometry table
        table_width=window_width*0.6
        table_height=window_height*0.3
        table_x=window_width/2-table_width/2
        table_y=0.68*window_height

        x_btn=window_width/2-w-2.5
        y_btn=40
        self._btn_measurement.setGeometry(x_btn,table_y-y_btn,w,h)
        self._btn_analysis.setGeometry(x_btn+w+5,table_y-y_btn,w,h)

        self.table_view.setGeometry(table_x,table_y,table_width,table_height)
        #self.table_view.resizeColumnsToContents()
        self.table_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.plot_widget.setGeometry(table_x,table_y,table_width,table_height)

        # create buttons for available models
        offset=0
        x = x_margin
        y = 0.2*window_height
        for model_id,button in self.model_buttons.items():
            width = self._btn_play.width()+20
            height = self._btn_play.height()
            button.setGeometry(x,y+offset,width,height)
            offset=offset+height+5



    def create_layout(self):
        """
        Create layout of the central Qwidget and add widgets
        :return:
        """
        super(self.__class__,self).create_layout()

        self._btn_play = QtWidgets.QPushButton(qta.icon('fa.play', color='white'),'Play', self)
        self._btn_play.setObjectName('medium')
        self._btn_play.clicked.connect(self.animate)

        self._btn_pause = QtWidgets.QPushButton(qta.icon('fa.pause', color='white'),'Pause', self)
        self._btn_pause.setObjectName('medium')
        self._btn_pause.clicked.connect(self.animation_stop)

        self._btn_fit_view = QtWidgets.QPushButton(qta.icon('fa.search', color='white'),'Fit view', self)
        self._btn_fit_view.setObjectName('medium')
        self._btn_fit_view.clicked.connect(self.autofit_3d_view)

        self._btn_slider_background = QtWidgets.QPushButton('Displacement scale', self)
        self._btn_slider_background.setObjectName('slider_background')

        self._btn_analysis = QtWidgets.QPushButton(qta.icon('fa.list-ol', color='white'),'Analysis', self)
        self._btn_analysis.setObjectName('table_button')
        self._btn_analysis.clicked.connect(self.analysis_data_mode)
        self._btn_analysis.setCheckable(True)

        self._btn_measurement = QtWidgets.QPushButton(qta.icon('fa.area-chart', color='white'),'Measurement', self)
        self._btn_measurement.setObjectName('table_button')
        self._btn_measurement.clicked.connect(self.measurement_data_mode)
        self._btn_measurement.setCheckable(True)
        self._btn_measurement.setChecked(True)

        # Table
        self.table_model = TableModel(self)
        self.fields = ['analysis_id','mode_n','eig_real', 'eig_xi','model_id']
        fake_df=pd.DataFrame(columns=self.fields)
        self.table_model.update(fake_df, [0], self.fields)  # show some data
        self.table_view = QtWidgets.QTableView(self)

        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table_view.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)

        self.table_model.header_labels=[
                                        keys['analysis_id']['15'],
                                        keys['mode_n']['15'],
                                        keys['eig_real']['15'],
                                        keys['eig_xi']['15'],
                                        keys['model_id']['15']
                                        ]

        self.table_view.setColumnHidden(4,True) #hide model_id

        self.table_view.setMouseTracking(True)
        self.current_hover = [0, 0]
        self.table_view.entered.connect(self.cell_hover)

        selection = self.table_view.selectionModel()
        selection.selectionChanged.connect(self.handle_selection_changed)
        self.table_view.setSortingEnabled(True)


        # Create 2D plot area
        self.create_2dplot_widget()

        self.anim_scale_slider = QtWidgets.QSlider(self)
        self.anim_scale_slider.setOrientation(QtCore.Qt.Horizontal)
        self.anim_scale_slider.setInvertedAppearance(False)
        self.anim_scale_slider.setInvertedControls(False)
        self.anim_scale_slider.setObjectName('horizontalSlider')
        self.anim_scale_slider.sliderReleased.connect(partial(self.animate,True))

    def build_uff_tree(self, modal_data,refresh):
        """
        Check available data in uff and load it into data tree widget

        :param modal_data:
        :return:
        """

        def on_activate(inp_model_id):

            #first deactivate all other models
            for model_id, model_obj in self.models.items():
                model_obj.activated=False
                self.model_buttons[int(model_id)].setChecked(False)

            #activate only clicked model
            self.models[inp_model_id].activated = True
            self.model_buttons[int(inp_model_id)].setChecked(True)

            activated_models=[]
            for model_id, model_obj in self.models.items():
                if model_obj.activated:
                    activated_models.append(int(model_obj.model_id))

            #currently selected model_id
            self.preferences['selected_model_id']=inp_model_id

            self.plot_activated_models()

        if refresh==False:
            #reload was called, drop previous models
            print('Clearing previous models')
            self.delete_model(delete_all=True)


        uff_tree_index = 0
        for index, row in self.modaldata.tables['info'].iterrows():
            value = index
            #model_id=int(available_model_ids[i])
            model_id = row['model_id']
            model_name = row['model_name'] + ' ' + str(model_id)
            description = row['description']
            units_code = row['units_code']


            if model_id in self.models.keys():
                print('model %f already stored - skipping' % model_id)
                pass
            else:
                print('Storing model id:',model_id)
                self.models[model_id] = Model(model_id, model_name, modal_data, self.plot_area, self.model_view,
                                          self.table_view, self.table_model, uff_tree_index,self.fields)


                button=QtWidgets.QPushButton(qta.icon('fa.database', color='white'),str(model_name), self)
                button.setObjectName('medium')
                button.setCheckable(True)
                button.clicked.connect(partial(on_activate, model_id))
                button.show()
                self.model_buttons[int(model_id)]=button

        #remove unused model buttons and model object
        available_models=self.modaldata.tables['info'].model_id.values
        button_items = list(self.model_buttons.items())
        for model_id,button in button_items:
            if float(model_id) not in available_models:
                # remove model object
                self.models.pop(float(model_id), None)

                #remove model button
                for child in self.children():
                    if child==self.model_buttons[str(model_id)]:
                        child.deleteLater()
                self.model_buttons[int(model_id)].deleteLater()
                self.model_buttons.pop(int(model_id), None)
            else:
                #refresh model names
                mask=self.modaldata.tables['info']['model_id']==float(model_id)
                model_name=self.modaldata.tables['info']['model_name'][mask].values[0]
                button.setText(model_name+ ' ' + str(float(model_id)))


        #deactivate all models and model buttons
        self.deactivate_all()

        #activate first model automatically
        on_activate(self.preferences['selected_model_id'])

        #Set preferences
        self.set_preferences()

    def set_preferences(self):
        """
        Set some preferences based on user selections in GUI
        :return:
        """

        # Set roving type for all models (based on measurement widget setting)
        if self.preferences['roving_type']=='Ref. node':
            self.set_ref_rove()
        else:
            self.set_rsp_rove()

    def analysis_data_mode(self):
        self.plot_widget.hide()
        self.table_view.show()
        self.widget_mode = 'EMA'
        self._btn_analysis.setChecked(True)
        self._btn_measurement.setChecked(False)

        for model_id, model_obj in self.models.items():
            model_obj.data_mode = 'EMA'

    def measurement_data_mode(self):
        self.plot_widget.show()
        self.table_view.hide()
        self.widget_mode = 'raw_data'
        self._btn_analysis.setChecked(False)
        self._btn_measurement.setChecked(True)

        for model_id, model_obj in self.models.items():
            model_obj.data_mode = 'raw_data'

    def reload(self, refresh=False):
        """Update interface -- read modaldata object again.
        Added by Matjaz!
        """

        #Calculate local coordinate systems and add them to 'geometry' table
        if self.modaldata.tables['info'].empty:
            self.status_bar.setBusy('analysis', 'Modal data object empty! (info table)')
            self.build_uff_tree(self.modaldata,refresh=refresh)
        else:
            #stop animation first
            self.animation_stop()
            self.calc_node_lcs()
            self.clear_all_views()
            self.build_uff_tree(self.modaldata,refresh=refresh)
            self.status_bar.setNotBusy('analysis')

    def refresh(self):
        '''Is called on tab-change (subwidget change) and on preferences change.'''
        self.reload(refresh=True)


    def run_animation(self,slider_run=False):
        """
        Connect correct model and anmimation type to animation timer
        :return:
        """
        # initialize data for animation and connect animation method for activated models to timer
        for model_id, model_obj in self.models.items():
            if model_obj.activated:

                # Setup animation displacement slider
                anim_scale=model_obj.get_def_scale()
                if slider_run==False:
                    self.anim_scale_slider.setValue(25)
                if slider_run==True:
                    slider_val=self.anim_scale_slider.value()
                    anim_scale=slider_val**2/25.**2*anim_scale

                if self.widget_mode == 'raw_data':
                    model_obj.animate = True
                    model_obj.animation_init(anim_scale)
                    self.anim_timer.timeout.connect(model_obj.animation_timer_app)
                    model_obj.timer_conn = True  #indicator that signal connection has been made
                elif self.widget_mode == 'EMA':
                    if model_obj.selected_model_id == model_obj.model_id:
                        model_obj.animate = True
                        model_obj.animation_init(anim_scale)
                        self.anim_timer.timeout.connect(model_obj.animation_timer_app)
                        model_obj.timer_conn = True  #indicator that signal connection has been made
                    else:
                        # disconnect other model_ids from timer
                        model_obj.animate = False
                        if model_obj.timer_conn:
                            self.anim_timer.timeout.disconnect(model_obj.animation_timer_app)
                            model_obj.timer_conn = False  #indicator that signal connection has been made
                else:
                    raise Exception('Wrong widget mode.')
            else:
                model_obj.animate = False

        self.anim_timer.start(40)

    def animate(self, slider_run=False):
        '''
        Animate all activated models at selected frequency
        :param selection_changed: True if different row was selected in table
        :return:
        '''

        #first stop ongoing animation
        self.animation_stop()

        # run new animation
        self.run_animation(slider_run=slider_run)

    def animation_stop(self):
        '''
        Method for stopping animation
        :return:
        '''
        self.anim_timer.stop()

        for model_id, model_obj in self.models.items():

            model_obj.animate = False
            if model_obj.timer_conn:
                self.anim_timer.timeout.disconnect(model_obj.animation_timer_app)
                model_obj.timer_conn = False  #indicator that signal connection has been made


    def clear_all_views(self):
        '''
        Clear everything on 3D and 2D view
        :return:
        '''

        # clear 3D view
        self.model_view.items.clear()
        self.model_view.updateGL()

        # clear 2D view
        self.plot_area.clear()
        self.plot_area.legend.scene().removeItem(self.plot_area.legend)

        # reset 2D view
        self.plot_area.legend = self.plot_area.addLegend()
        self.plot_area.addItem(self.vLine, ignoreBounds=True)
        self.plot_area.addItem(self.hLine, ignoreBounds=True)
        self.plot_area.addItem(self.sel_freq_vLine, ignoreBounds=True)


class Model():
    def __init__(self, model_id, name, modal_data, view_2d, view_3d, table_view, table_model, uff_tree_index,
                 analysis_fields):

        self.model_id = model_id
        self.name = name
        self.view_2d = view_2d
        self.view_3d = view_3d
        self.table_view = table_view
        self.table_model = table_model
        self.modal_data = modal_data
        self.uff_tree_index = uff_tree_index
        self.fields = analysis_fields
        self.analysis_index_copy=pd.DataFrame(columns=self.fields)

        # For storing model_obj
        self.models = {}

        self.data_mode = 'raw_data'  # plot raw measurment data or EMA data, or...

        #was reference or response roved?
        self.roving_type='rsp_roved' # options: 'ref_roved' or 'rsp_roved'

        # Define reference directions for use in Animation 'raw data' mode
        self.reference_map={'x':{'dirs':[1, -1],
                            'use':True},
                       'y':{'dirs':[2, -2],
                            'use':True},
                       'z':{'dirs':[3, -3],
                            'use':True}
                        }

        # selection info from analysis table
        #self.selected_uffid = None
        self.selected_mode = None
        self.selected_model_id = None
        self.selected_mode_ana_id = None

        self.timer_conn = False  #indicator that signal connection has been made

        #initialize nodes meshitem
        self.node_meshitem = CustomGLMeshItem(vertexes=np.array([[[0, 0, 0], [0, 0, 0], [0, 0, 0]]]),
                                      vertexColors=np.array([[[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]]),
                                      shader=SHADER,drawEdges=DRAW_EDGES_NODES,computeNormals=COMPUTENORMALS, glOptions=GLOPTS,smooth=SMOOTH)
        self.nodes_plotted = False


        #initialize lines meshitem
        self.default_line_width=1
        self.default_line_color=np.array([0,1,0,1])
        self.line_xyz=[] # line data
        self.line_disp=[] # node displacements for animation of elements
        self.line_meshitem = gl.GLLinePlotItem(pos=np.array([[0, 0, 0]]),
                                      color=self.default_line_color,
                                      width=self.default_line_width,mode='lines')
        self.line_plotted = False



        #initialize element meshitem
        self.elem_meshitem = CustomGLMeshItem(vertexes=np.array([[[0, 0, 0], [0, 0, 0], [0, 0, 0]]]),
                                      vertexColors=np.array([[[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]]),
                                      shader=SHADER,drawEdges=DRAW_EDGES_ELEMENTS,computeNormals=COMPUTENORMALS, glOptions=GLOPTS,smooth=SMOOTH)
        self.elem_plotted = False
        self.elem_xyz=[] # element node data
        self.elem_colors=[] # element node color data
        self.elem_disp=[] # node displacements for animation of elements

        #initialize model lcs meshitem
        self.lcs_meshitem = CustomGLMeshItem(vertexes=np.array([[[0, 0, 0], [0, 0, 0], [0, 0, 0]]]),
                                          vertexColors=np.array([[[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]]),
                                          shader=SHADER,drawEdges=DRAW_EDGES_LCS,computeNormals=COMPUTENORMALS, glOptions=GLOPTS,smooth=SMOOTH)

        # stuff to plot via 3d view context menu
        self.model_lcs_plotted = False
        self.plot_node_lcs_act = False
        self.plot_nodes_act = True
        self.plot_lines_act = True
        self.plot_elements_act = True

        #initialize model node labels
        self.plot_node_labels_act = False

        self.cube = None  # cube data
        self.xyz_rep = None  # node locations
        self.xyz_order = None  # Node order from xyz (for aligning animiation data)
        self.node_colors = None  # model color

        self.activated = False

        # default settings for 2D plot
        self.plotitems = {'all_frfs': {}, 'frf_sum': {}}

        self.plot_2d_all_frfs = False  # plot this by default?
        self.plotted_all_frfs = False  # flag if allFRF are plotted

        self.plot_2d_frf_sum = True
        self.plotted_frf_sum = False

        self.needs_refresh_2d = True

        self.color = QtGui.QColor(0, 255, 0)
        self.offset = {}
        self.offset['x'] = 0
        self.offset['y'] = 0
        self.offset['z'] = 0

        self.anim_freq = 0  # frequency for animation
        self.fpc = 50  # frames per cycle for animation
        self.curr_frame = 0  # current animation frame
        self.curr_freq = 0  # current frequency for animation

        self.animate = False
        self.wheel_event = False  # true when wheel event is the cause for model refresh

        #COLORS
        #TODO: take colors from color palete template.py
        self.def_node_color=QtGui.QColor(0, 255, 0, 255)
        self.set_node_color(self.def_node_color)

        self.def_triangle_color=QtGui.QColor(0, 0, 255, 255)  # default element color (user cannot change)
        self.cur_triangle_color=QtGui.QColor(0, 0, 255, 255)  # currently set element color (user can change)
        self.set_elem_color(self.def_triangle_color,'triangle')

        self.def_line_color=QtGui.QColor(0, 0, 0, 255)  # default element color (user cannot change)
        self.cur_line_color=QtGui.QColor(0, 0, 0, 255)  # currently set element color (user can change)
        self.set_elem_color(self.def_line_color,'line')


    def set_node_color(self,color):
        """
        Set default color in modal data table

        :return:
        """
        #TODO: is color correctly imported from uff ?

        rgba_color = pg.colorTuple(color)
        model_mask =self.modal_data.tables['geometry']['model_id'] == self.model_id
        self.modal_data.tables['geometry'].ix[model_mask,'clr_r']=rgba_color[0]/ 255.  # rbg values 0-1
        self.modal_data.tables['geometry'].ix[model_mask,'clr_g']=rgba_color[1]/ 255.  # rbg values 0-1
        self.modal_data.tables['geometry'].ix[model_mask,'clr_b']=rgba_color[2]/ 255.  # rbg values 0-1
        self.modal_data.tables['geometry'].ix[model_mask,'clr_a']=rgba_color[3]/ 255.  # alpha values 0-1

    def set_elem_color(self,color,elem_type):
        #TODO: set color for lines and triangles seperately
        if elem_type=='triangle':
            self.cur_triangle_color=color
        elif elem_type=='line':
            self.cur_line_color=color

        rgba_color = pg.colorTuple(color)

        model_mask =self.modal_data.tables['elements_index']['model_id'] == self.model_id
        type_mask =self.modal_data.tables['elements_index']['element_descriptor'] == elem_type
        combined=model_mask & type_mask
        self.modal_data.tables['elements_index'].ix[combined,'clr_r']=rgba_color[0]/ 255.  # rbg values 0-1
        self.modal_data.tables['elements_index'].ix[combined,'clr_g']=rgba_color[1]/ 255.  # rbg values 0-1
        self.modal_data.tables['elements_index'].ix[combined,'clr_b']=rgba_color[2]/ 255.  # rbg values 0-1
        self.modal_data.tables['elements_index'].ix[combined,'clr_a']=rgba_color[3]/ 255.  # alpha values 0-1

    def get_def_scale(self):
        """
        Get automatically determined animation displacement scale
        :return:
        """
        final_node_disp,self.node_disp = self.get_animation_disp(self.modal_data, self.model_id, self.anim_freq)
        disp_aux = (abs(self.node_disp.flatten().max()) + abs(self.node_disp.flatten().min()))
        node_aux=abs(self.xyz_rep.flatten().max()) + abs(self.xyz_rep.flatten().min())
        self.def_scale=0.2*node_aux/disp_aux

        return self.def_scale

    def animation_init(self,anim_scale):

        final_node_disp,self.node_disp = self.get_animation_disp(self.modal_data, self.model_id, self.anim_freq)

        # get triangle and line displacements
        self.elem_disp=self.get_elem_disp(final_node_disp,'triangle')
        self.line_disp=self.get_elem_disp(final_node_disp,'line')
        self.def_scale=anim_scale


        if self.curr_freq == self.anim_freq:
            # pause was used -> continue from previous frame
            pass
        else:
            # reset animation
            self.curr_frame = 0

        self.curr_freq = self.anim_freq


    def animation_timer_app(self):

        #print(self.model_id, self.curr_frame)
        self.cube_scale, lcs_scale = self.get_cube_and_lcs_scale()

        new_node_loc = self.cube * self.cube_scale + self.xyz_rep + np.sin(
            self.curr_frame / self.fpc * 2 * np.pi) * self.node_disp * self.def_scale
        #print(i,self.new_node_loc[0])


        # if there is no elements...don't even try to animate them
        if len(self.elem_xyz)==0:
            pass
        else:
            new_elem_loc=self.elem_xyz+np.sin(self.curr_frame / self.fpc * 2 * np.pi) * self.elem_disp * self.def_scale
            self.elem_meshitem.setMeshData(vertexes=np.real(new_elem_loc), vertexColors=self.elem_colors, shader=SHADER,drawEdges=DRAW_EDGES_ELEMENTS,computeNormals=COMPUTENORMALS, glOptions=GLOPTS,smooth=SMOOTH)
            self.elem_meshitem.meshDataChanged()

        if len(self.line_xyz)==0:
            pass
        else:
            #check types...if object type, then np.real(x) does not work!
            #TODO: why types change?
            if self.line_xyz.dtype==object:
                self.line_xyz=self.line_xyz.astype(np.complex64)
                self.line_disp=self.line_disp.astype(np.complex64)

            new_line_loc=self.line_xyz+np.sin(self.curr_frame / self.fpc * 2 * np.pi) * self.line_disp * self.def_scale
            self.line_meshitem.setData(pos=np.real(new_line_loc), color=self.line_colors, width=self.default_line_width,antialias=True,mode='lines')


        self.node_meshitem.setMeshData(vertexes=np.real(new_node_loc), vertexColors=self.node_colors, shader=SHADER,drawEdges=DRAW_EDGES_NODES,computeNormals=COMPUTENORMALS, glOptions=GLOPTS,smooth=SMOOTH)
        self.node_meshitem.meshDataChanged()



        self.view_3d.updateGL()

        #print(tm.datetime.now())

        if self.curr_frame == self.fpc:
            self.curr_frame = 0
        else:
            self.curr_frame = self.curr_frame + 1

    def get_elem_disp(self,final_node_data,elem_type):
        """
        Get displacements for elements
        :param modal_data:
        :param model_id:
        :param freq:
        :return:
        """
        model_mask=self.modal_data.tables['elements_index']['model_id']==self.model_id
        type_mask=self.modal_data.tables['elements_index']['element_descriptor']==elem_type

        combined_mask=model_mask & type_mask

        elem=pd.merge(self.modal_data.tables['elements_index'][combined_mask],self.modal_data.tables['elements_values'],how='left',left_on='element_id',right_on='element_id')

        elem_disp_df=pd.merge(elem,final_node_data.reset_index(),how='left',left_on='node_id',right_on='node_nums')

        # Use same node order as when the meshitem was generated
        elem_disp_df.sort_values(['element_id','node_pos'],inplace=True)


        elem_disp=np.array(
                (elem_disp_df['anim_disp_1'].values, elem_disp_df['anim_disp_2'].values, elem_disp_df['anim_disp_3'].values))
        elem_disp=elem_disp.transpose()

        if elem_type=='triangle':
            elem_disp=elem_disp.reshape(-1,3,3)
        elif elem_type=='line':
            elem_disp=elem_disp.reshape(-1,3)

        return elem_disp

    def get_animation_disp(self, modal_data, model_id, freq):
        """
        Build animation data
        :return:
        """
        if self.data_mode == 'raw_data':
            # extract data only for selected frequency
            def find_nearest(array, value):
                idx = (np.abs(array - value)).argmin()
                return array[idx]


            # Get reference directions for use in animation
            dir_list=[]
            for item,value in self.reference_map.items():
                if value['use']==True:
                    dir_list=dir_list+value['dirs']
            if len(dir_list)==0:
                raise(Exception('No reference directions selected!'))


            #roving_type='ref_roved'
            roving_map={'rsp_roved':['rsp_node','rsp_dir','ref_dir'],
                        'ref_roved':['ref_node','ref_dir','rsp_dir']}


            #find frequency nearest to clicked one
            anim_freq = find_nearest(np.unique(modal_data.tables['measurement_values']['frq'].values), freq)

            mv_model_mask = modal_data.tables['measurement_values']['model_id'] == model_id
            mv = modal_data.tables['measurement_values'][mv_model_mask]

            mx_model_mask = modal_data.tables['measurement_index']['model_id'] == model_id
            mx = modal_data.tables['measurement_index'][mx_model_mask]

            g_model_mask = modal_data.tables['geometry']['model_id'] == model_id
            g = modal_data.tables['geometry'][g_model_mask]

            new = pd.merge(mx, mv[mv.frq == anim_freq], on='measurement_id')
            final = pd.merge(g, new, left_on='node_nums', right_on=roving_map[self.roving_type][0])

            #select only one reference dir
            #TODO: reference dir summation : odziv x(ref x) + odziv x(ref y) + odziv x(ref z) = skupni odziv x.  Analogno še ostale smeri
            ref_dirs = np.unique(final[roving_map[self.roving_type][2]].values)

            #ref_dir = ref_dirs[0]  #use first available
            #ref_dir=-1 # manual selection
            #final = final[final['ref_dir'] == ref_dir] #use single direction
            final = final[final[roving_map[self.roving_type][2]].isin(ref_dirs)] #sum all available directions

            #print('Used reference dir: ', ref_dir)
            print('Available reference directions: ', ref_dirs)

            # Create dataframe with all rsp_dir...nodes without measurements will have zeros later
            nodes = g['node_nums'].values

            # all possible response directions
            #dir = np.array((1, 2, 3, -1, -2, -3))
            dir = np.asarray(dir_list)

            multi_index = [nodes.repeat(len(dir)), np.tile(dir, len(nodes))]
            id = pd.MultiIndex.from_arrays(multi_index, names=['node_nums', roving_map[self.roving_type][1]])
            df = pd.DataFrame(index=id)

            df = df.reset_index()
            new_final = pd.merge(df, final, how='left')

            # Replace nans with zeros for nodes which do not have measurement data or response dir is not available
            new_final.fillna(0, inplace=True)

            final = new_final.reset_index()

            # # total number of nodes in geometry data
            #total_node_num = len(np.unique(final['node_nums'].values))
            #

            # create functions for use with pandas apply function
            def func_1(df):
                dir = df[roving_map[self.roving_type][1]]

                if dir == 1:
                    res = df['lcs_x1'] * np.imag(df['amp'])
                if dir == 2:
                    res = df['lcs_y1'] * np.imag(df['amp'])
                if dir == 3:
                    res = df['lcs_z1'] * np.imag(df['amp'])
                if dir == -1:
                    res = -df['lcs_x1'] * np.imag(df['amp'])
                if dir == -2:
                    res = -df['lcs_y1'] * np.imag(df['amp'])
                if dir == -3:
                    res = -df['lcs_z1'] * np.imag(df['amp'])

                return res

            def func_2(df):
                dir = df[roving_map[self.roving_type][1]]

                if dir == 1:
                    res = df['lcs_x2'] * np.imag(df['amp'])
                if dir == 2:
                    res = df['lcs_y2'] * np.imag(df['amp'])
                if dir == 3:
                    res = df['lcs_z2'] * np.imag(df['amp'])
                if dir == -1:
                    res = -df['lcs_x2'] * np.imag(df['amp'])
                if dir == -2:
                    res = -df['lcs_y2'] * np.imag(df['amp'])
                if dir == -3:
                    res = -df['lcs_z2'] * np.imag(df['amp'])

                return res

            def func_3(df):
                dir = df[roving_map[self.roving_type][1]]

                if dir == 1:
                    res = df['lcs_x3'] * np.imag(df['amp'])
                if dir == 2:
                    res = df['lcs_y3'] * np.imag(df['amp'])
                if dir == 3:
                    res = df['lcs_z3'] * np.imag(df['amp'])
                if dir == -1:
                    res = -df['lcs_x3'] * np.imag(df['amp'])
                if dir == -2:
                    res = -df['lcs_y3'] * np.imag(df['amp'])
                if dir == -3:
                    res = -df['lcs_z3'] * np.imag(df['amp'])

                return res

            # multiply ampltudes with LCS vectors for each node
            final['anim_disp_1'] = final.apply(func_1, axis=1)
            final['anim_disp_2'] = final.apply(func_2, axis=1)
            final['anim_disp_3'] = final.apply(func_3, axis=1)

            # group by node numbers and sum (from 3 rows per node num we get 1 row and summed disp)
            final = final.groupby(['node_nums']).sum()

            # Use same node order as when the meshitem was generated
            final = final.reindex(self.xyz_order)

            final_node_disp = np.array(
                (final['anim_disp_1'].values, final['anim_disp_2'].values, final['anim_disp_3'].values))
            final_node_disp = final_node_disp.transpose()

            # repeat every line 12x due to 2 triangles per 6 cube sides
            total_node_num=len(final_node_disp)

            #remove zero imaginary part (it crashes openGL)
            final_node_disp=final_node_disp.real

            final_node_disp_rep = final_node_disp.repeat(36, axis=0).reshape(12 * total_node_num, 3, 3)

        elif self.data_mode == 'EMA':
            #select correct model
            geom_model_mask = modal_data.tables['geometry']['model_id'] == model_id

            #drop nan lines defined in geometry
            nan_mask = self.modal_data.tables['geometry'][['node_nums','x', 'y', 'z','thz', 'thy', 'thx' , 'model_id']].notnull().all(axis=1)

            combined= geom_model_mask & nan_mask
            geom = modal_data.tables['geometry'][combined]

            analysis_data = self.modal_data.tables['analysis_values'].set_index(['model_id','analysis_id', 'mode_n'])

            selected_data = analysis_data.ix[int(self.model_id)].ix[int(self.selected_mode_ana_id)].ix[int(self.selected_mode)]
            final = pd.merge(geom, selected_data, how='left', on='node_nums')

            # Replace nans with zeros for nodes which do not have measurement data or response dir is not available
            final.fillna(0, inplace=True)

            # total number of nodes in geometry data
            total_node_num = len(np.unique(final['node_nums'].values))

            # create functions for use with pandas apply function
            def func_1(df):

                res_x = df['lcs_x1'] * np.imag(df['r1'])
                res_y = df['lcs_y1'] * np.imag(df['r2'])
                res_z = df['lcs_z1'] * np.imag(df['r3'])

                return res_x + res_y + res_z

            def func_2(df):

                res_x = df['lcs_x2'] * np.imag(df['r1'])
                res_y = df['lcs_y2'] * np.imag(df['r2'])
                res_z = df['lcs_z2'] * np.imag(df['r3'])

                return res_x + res_y + res_z

            def func_3(df):

                res_x = df['lcs_x3'] * np.imag(df['r1'])
                res_y = df['lcs_y3'] * np.imag(df['r2'])
                res_z = df['lcs_z3'] * np.imag(df['r3'])

                return res_x + res_y + res_z

            # multiply ampltudes with LCS vectors for each node
            final['anim_disp_1'] = final.apply(func_1, axis=1)
            final['anim_disp_2'] = final.apply(func_2, axis=1)
            final['anim_disp_3'] = final.apply(func_3, axis=1)

            # Use same node order as when the meshitem was generated
            #final=final.reindex(self.xyz_order) #not necessary in 'EMA mode' as the order is inherited directly from geometry table

            # if r1, r2, r3 values are amplitudes in LCS
            final_node_disp = np.array(
                (final['anim_disp_1'].values, final['anim_disp_2'].values, final['anim_disp_3'].values))

            #discard fake zero imag part (created automatically by pandas)
            final_node_disp = final_node_disp.real
            #if  r1, r2, r3 values are amplitudes in GCS
            #final_node_disp=np.array((final['r1'].values.imag,final['r2'].values.imag,final['r3'].values.imag))

            final_node_disp = final_node_disp.transpose()

            # repeat every line 12x due to 2 triangles per 6 cube sides
            final_node_disp_rep = final_node_disp.repeat(36, axis=0).reshape(12 * total_node_num, 3, 3)


        else:
            raise Exception('Wrong data mode.')

        return final,final_node_disp_rep

    def plot_node_lcs(self, modal_data, offset, view, model_id, scale):
        """
        Plot nodal local csys, X dir = RED, Y dir = GREEN, Z dir = BLUE

        :param model:
        :return:
        """
        #take only rows without Nans
        nan_mask = self.modal_data.tables['geometry'][['node_nums','x', 'y', 'z','thz', 'thy', 'thx' , 'model_id']].notnull().all(axis=1)

        # node locations
        model_mask = modal_data.tables['geometry']['model_id'][nan_mask] == model_id
        xyz = modal_data.tables['geometry'][nan_mask][['x', 'y', 'z']][model_mask].values

        # local coordinate system vectors
        lcs_x_data = self.modal_data.tables['geometry'][nan_mask][['lcs_x1', 'lcs_x2', 'lcs_x3']][model_mask].values
        lcs_y_data = self.modal_data.tables['geometry'][nan_mask][['lcs_y1', 'lcs_y2', 'lcs_y3']][model_mask].values
        lcs_z_data = self.modal_data.tables['geometry'][nan_mask][['lcs_z1', 'lcs_z2', 'lcs_z3']][model_mask].values

        # add model offset
        xyz[:, 0] = xyz[:, 0] + offset['x']
        xyz[:, 1] = xyz[:, 1] + offset['y']
        xyz[:, 2] = xyz[:, 2] + offset['z']

        verts = np.zeros((len(lcs_x_data) * 3, 3, 3))
        colors = np.zeros((len(lcs_x_data) * 3, 3, 4))
        k = 0
        for i in range(len(lcs_x_data)):
            # x dir triangle
            verts[k, 0, :] = xyz[i, :]
            verts[k, 1, :] = xyz[i, :] + scale * lcs_x_data[i, :]
            verts[k, 2, :] = xyz[i, :] + scale / 5 * lcs_z_data[i, :]
            colors[k, :, :] = (1, 0, 0, 0)

            # y dir triangle
            verts[k + 1, 0, :] = xyz[i, :]
            verts[k + 1, 1, :] = xyz[i, :] + scale * lcs_y_data[i, :]
            verts[k + 1, 2, :] = xyz[i, :] + scale / 5 * lcs_z_data[i, :]
            colors[k + 1, :, :] = (0, 1, 0, 0)

            # z dir triangle
            verts[k + 2, 0, :] = xyz[i, :]
            verts[k + 2, 1, :] = xyz[i, :] + scale * lcs_z_data[i, :]
            verts[k + 2, 2, :] = xyz[i, :] + scale / 5 * lcs_x_data[i, :]
            colors[k + 2, :, :] = (0, 0, 1, 0)

            k = k + 3


        #lcs_meshitem = gl.GLMeshItem(vertexes=verts, vertexColors=node_colors,  shader='balloon')
        return verts, colors

    def get_elem_meshitem_data(self, modal_data, model_id, offset,elem_type):
        """
        Get node_meshitem data for specific model_id
        :param modal_data:
        :param model_id:
        :param cube_scale:
        :param offset:
        :param color:  0-255 float (RGB value)
        :param alpha:  0-255 float
        """


        #get model specific element data
        model_mask=modal_data.tables['elements_index']['model_id']==model_id
        geom_mask=modal_data.tables['geometry']['model_id']==model_id

        type_mask=modal_data.tables['elements_index']['element_descriptor']==elem_type
        combined_mask= model_mask & type_mask

        elem=pd.merge(modal_data.tables['elements_index'][combined_mask],modal_data.tables['elements_values'],how='left',left_on='element_id',right_on='element_id')

        #take only rows without Nans
        nan_mask = self.modal_data.tables['geometry'][['node_nums','x', 'y', 'z','thz', 'thy', 'thx' , 'model_id']].notnull().all(axis=1)
        combined_mask2=geom_mask & nan_mask


        #get element ids
        new=pd.merge(elem,modal_data.tables['geometry'][combined_mask2],how='left',left_on='node_id',right_on='node_nums')
        new.sort_values(['element_id','node_pos'],inplace=True)

        #get nodes from element ids
        xyz = new[['x','y','z']].values

        colors = new[['clr_r_x','clr_g_x','clr_b_x','clr_a_x']].values # suffix _x due to dataframe merge

        #use offset
        xyz[:, 0] = xyz[:, 0] + offset['x']
        xyz[:, 1] = xyz[:, 1] + offset['y']
        xyz[:, 2] = xyz[:, 2] + offset['z']

        #reshape for meshitem
        if elem_type=='triangle':
            self.elem_xyz=xyz.reshape(-1,3,3) # -1 -> dimension is infered from array dim

            self.elem_colors=colors.reshape(-1,3,4) # -1 -> dimension is infered from array dim
            self.elem_xyz_order = new['node_nums']
        elif elem_type=='line':
            #self.line_xyz=xyz.reshape(-1,2,3) # -1 -> dimension is infered from array dim
            self.line_xyz=xyz.reshape(-1,3) # -1 -> dimension is infered from array dim

            #self.line_colors=colors.reshape(-1,2,4) # -1 -> dimension is infered from array dim
            self.line_colors=colors.reshape(-1,4) # -1 -> dimension is infered from array dim
            self.line_xyz_order = new['node_nums']

    def get_meshitem_data(self, modal_data, model_id, offset):
        """
        Get node_meshitem data for specific model_id
        :param modal_data:
        :param model_id:
        :param cube_scale:
        :param offset:
        :param color:  0-255 float (RGB value)
        :param alpha:  0-255 float
        """
        #take only rows without Nans
        nan_mask = modal_data.tables['geometry'][['node_nums','x', 'y', 'z','thz', 'thy', 'thx' , 'model_id']].notnull().all(axis=1)

        model_mask = modal_data.tables['geometry']['model_id'][nan_mask] == model_id

        xyz = modal_data.tables['geometry'][['x', 'y', 'z']][nan_mask][model_mask].values
        colors = modal_data.tables['geometry'][['clr_r','clr_g','clr_b','clr_a']][nan_mask][model_mask].values
        self.xyz_order = modal_data.tables['geometry'][nan_mask][model_mask]['node_nums']


        xyz[:, 0] = xyz[:, 0] + offset['x']
        xyz[:, 1] = xyz[:, 1] + offset['y']
        xyz[:, 2] = xyz[:, 2] + offset['z']

        self.cube = np.tile(CUBE, (xyz.shape[0], 1, 1))
        self.xyz_rep = xyz.repeat(36, axis=0).reshape(self.cube.shape[0], 3, 3)

        self.node_colors = colors.repeat(36, axis=0).reshape(self.cube.shape[0], 3, 4)

    def get_meshitem(self, cube_scale):

        if self.wheel_event:
            node_loc = (self.cube * cube_scale + self.xyz_rep)

        else:
            self.get_meshitem_data(self.modal_data, self.model_id, self.offset)
            node_loc = (self.cube * cube_scale + self.xyz_rep)

        meshitem = CustomGLMeshItem(vertexes=node_loc, vertexColors=self.node_colors, shader=SHADER,drawEdges=DRAW_EDGES_NODES,computeNormals=COMPUTENORMALS, glOptions=GLOPTS,smooth=SMOOTH)#, glOptions='opaque')

        return meshitem


    def refresh(self, wheel_event=False):
        """
        Call this on first plot
        :return:
        """
        self.wheel_event = wheel_event  # wheel event is True when it is the cause for referesh -> only zoom changed

        if self.activated:

            if self.view_2d!=None:
                if not self.modal_data.tables['measurement_index'][
                            self.modal_data.tables['measurement_index']['model_id'] == self.model_id].empty:
                    # do default 2d plot
                    self.plot_2d()
                else:
                    print("2D data not available.")

            if self.table_model!=None:
                self.populate_table()


            # do default 3d plot
            self.plot_3d()

        else:
            self.deactivate()


        self.wheel_event = False  #reset wheel event
    def deactivate(self):
        """
        Deactivate model in a way that the 3D view is aware of deactivation
        :return:
        """
        #depopulate analysis data table
        if self.table_model!=None:
            self.depopulate_table()

        if self.view_2d!=None:
            self.remove_plotitems('frf_sum')
            self.plotted_frf_sum = False
            self.remove_plotitems('all_frfs')
            self.plotted_all_frfs = False

        #self.remove_meshitems()
        self.remove_meshitem(self.node_meshitem)
        self.nodes_plotted = False
        self.remove_meshitem(self.line_meshitem)
        self.line_plotted = False
        self.remove_meshitem(self.elem_meshitem)
        self.elem_plotted = False

        self.remove_meshitems_lcs()
        self.model_lcs_plotted = False
        self.needs_refresh_2d = True

        #remove node labels
        self.remove_node_labels()

        #stop animating so that meshitems are updated
        self.animate=False

    def populate_table(self):
        """
        Show analysis data for activated models
        :return:
        """

        model_id_list = np.unique(self.table_model.datatable.model_id).tolist()

        #add self to the list
        model_id_list.append(self.model_id)

        def get_eig_real(df):
            fr = np.round(np.abs(df['eig'])/(2 * np.pi),2)
            return fr

        def get_eig_xi(df):
            fr = np.abs(df['eig'])
            xir = np.round(-df['eig'].real/fr,3)
            return xir

        #change complex eigenvalue to real if analysis data present
        self.analysis_index_copy=self.modal_data.tables['analysis_index'].copy()
        self.analysis_index_copy['eig_real']=np.nan
        self.analysis_index_copy['eig_xi']=np.nan

        if not self.analysis_index_copy.empty:
            self.analysis_index_copy['eig_real']=self.analysis_index_copy.apply(get_eig_real,axis=1)
            self.analysis_index_copy['eig_xi']=self.analysis_index_copy.apply(get_eig_xi,axis=1)
            self.table_model.update(self.analysis_index_copy, model_id_list,self.fields)


        self.table_model.update(self.analysis_index_copy, model_id_list, self.fields)


    def depopulate_table(self):
        """
        Remove analysis data for deactivated models
        :return:
        """

        model_id_list = np.unique(self.table_model.datatable.model_id).tolist()

        #remove self to the list
        try:
            model_id_list.remove(self.model_id)
        except:
            pass

        self.table_model.update(self.analysis_index_copy, model_id_list, self.fields)

    def get_cube_and_lcs_scale(self):
        # Get current distance from 3D view (for setting cube size)

        dist = self.view_3d.opts['distance']
        if dist==0:
            self.view_3d.opts['distance']=10
            dist=10
        # cube size is proportional to autofit distance
        # Ratio due to app window size changes
        current_width = self.view_3d.width()  # current 3d_view width
        window_width_ratio = current_width / self.view_3d.default_width
        cube_scale = dist * 0.006 / window_width_ratio

        # scale of local coordinate system triangles
        lcs_scale = dist * 0.03

        return cube_scale, lcs_scale

    def manage_line_plot(self):

        nan_mask = self.modal_data.tables['elements_index'][['model_id', 'element_id', 'element_descriptor',
                                                      'nr_of_nodes']].notnull().all(axis=1)
        model_mask = self.modal_data.tables['elements_index']['model_id'][nan_mask] == self.model_id


        # Do 3d stuff only if there is at least one element
        if not model_mask.empty:
            # prepare data mesh item
            self.get_elem_meshitem_data(self.modal_data,self.model_id,self.offset,'line')

            # 3D view
            if self.animate:
                pass

            else:
                #plot elements
                self.line_meshitem.setData(pos=self.line_xyz,
                                           color=self.line_colors,
                                           width=self.default_line_width,
                                           antialias=True,
                                           mode='lines')

                self.view_3d.updateGL()

            if self.plot_lines_act:
                if self.line_plotted:
                    pass
                else:
                    self.view_3d.addItem(self.line_meshitem)
                    self.line_plotted=True
            else:
                if self.line_plotted:
                    self.remove_meshitem(self.line_meshitem)
                    self.line_plotted=False
        else:
            #delete previous data
            self.line_xyz=[]

            # remove single element (this happens when last element is deleted)
            view_items = list(self.view_3d.items)
            for itm in view_items:
                 if itm == self.line_meshitem:
                    self.view_3d.removeItem(self.line_meshitem)
            self.line_plotted=False

    def manage_elem_plot(self):

        nan_mask = self.modal_data.tables['elements_index'][['model_id', 'element_id', 'element_descriptor',
                                                      'nr_of_nodes']].notnull().all(axis=1)
        model_mask = self.modal_data.tables['elements_index']['model_id'][nan_mask] == self.model_id


        # Do 3d stuff only if there is at least one element
        if not model_mask.empty:
            # prepare data mesh item
            self.get_elem_meshitem_data(self.modal_data,self.model_id,self.offset,'triangle')

            # 3D view
            if self.animate:
                pass

            else:
                #plot elements
                self.elem_meshitem.setMeshData(vertexes=self.elem_xyz,
                                               vertexColors=self.elem_colors,
                                               indexed='faces',
                                               resetNormals=False,
                                               shader=SHADER,
                                               drawEdges=DRAW_EDGES_ELEMENTS,
                                               computeNormals=COMPUTENORMALS,
                                               glOptions=GLOPTS,
                                               smooth=SMOOTH)

                self.elem_meshitem.meshDataChanged()

                self.view_3d.updateGL()

            if self.plot_elements_act:
                if self.elem_plotted:
                    pass
                else:
                    self.view_3d.addItem(self.elem_meshitem)
                    self.elem_plotted=True
            else:
                if self.elem_plotted:
                    self.remove_meshitem(self.elem_meshitem)
                    self.elem_plotted=False
        else:
            #delete previous data
            self.elem_xyz=[]

            # remove single element (this happens when last element is deleted)
            view_items = list(self.view_3d.items)
            for itm in view_items:
                 if itm == self.elem_meshitem:
                    self.view_3d.removeItem(self.elem_meshitem)
            self.elem_plotted=False

    def plot_3d(self):

        nan_mask = self.modal_data.tables['geometry'][['node_nums','x', 'y', 'z','thz', 'thy', 'thx' , 'model_id']].notnull().all(axis=1)
        model_mask = self.modal_data.tables['geometry']['model_id'][nan_mask] == self.model_id

        # Do 3d stuff only if there is at least one point
        if not model_mask.empty:
            cube_scale, lcs_scale = self.get_cube_and_lcs_scale()


            # prepare data mesh item
            self.get_meshitem_data(self.modal_data, self.model_id, self.offset)

            # 3D view
            if self.animate:
                pass

            else:
                # plot nodes
                self.node_meshitem.setMeshData(vertexes=(self.cube * cube_scale + self.xyz_rep), vertexColors=self.node_colors,
                                          shader=SHADER,drawEdges=DRAW_EDGES_NODES,computeNormals=COMPUTENORMALS, glOptions=GLOPTS,smooth=SMOOTH)
                self.node_meshitem.meshDataChanged()


                self.view_3d.updateGL()

            if self.plot_nodes_act:
                if self.nodes_plotted:
                    pass
                else:
                    self.view_3d.addItem(self.node_meshitem)
                    self.nodes_plotted=True
            else:
                if self.nodes_plotted:
                    self.remove_meshitem(self.node_meshitem)
                    self.nodes_plotted=False


            #plot or not elements
            self.manage_elem_plot()

            #plot or not lines
            self.manage_line_plot()


            # plot node local coordinate systems if checked in context menu (or remove from plot)
            if self.plot_node_lcs_act:
                if self.model_lcs_plotted:
                    pass
                else:
                    self.view_3d.addItem(self.lcs_meshitem)
                    self.model_lcs_plotted = True
                verts, colors = self.plot_node_lcs(self.modal_data, self.offset, self.view_3d, self.model_id, lcs_scale)
                self.lcs_meshitem.setMeshData(vertexes=verts, vertexColors=colors, shader=SHADER,drawEdges=DRAW_EDGES_LCS,computeNormals=COMPUTENORMALS, glOptions=GLOPTS,smooth=SMOOTH)
                self.lcs_meshitem.meshDataChanged()
                self.view_3d.updateGL()
            else:
                if self.model_lcs_plotted:
                    self.remove_meshitems_lcs()
                    self.model_lcs_plotted = False


            # plot node labels
            if self.plot_node_labels_act:
                self.plot_node_labels()
            else:
                self.remove_node_labels()

        else:
            #this happens when all nodes are deleted via gui
            # plot nodes
            self.remove_meshitem(self.node_meshitem)
            self.nodes_plotted=False

            self.remove_meshitems_lcs()
            self.model_lcs_plotted = False

            #plot or not elements (this is needed when all nodes are deleted BEFORE elements)
            self.manage_elem_plot()

    def plot_node_labels(self):
        '''
        - prepare and paint node labels for all activated models
        - node labels are plotted when 'plot_activated_models' is called
        '''

        cube_scale, lcs_scale = self.get_cube_and_lcs_scale()
        label_offset = cube_scale * 2
        view = self.view_3d
        modal_data = self.modal_data


        # Do node labels for specific model id
        model_mask = modal_data.tables['geometry']['model_id'] == self.model_id
        # node_labels_data = modal_data.tables['geometry'][['node_nums', 'x', 'y', 'z']][
        #     model_mask].sort_index().values

        node_labels_data = modal_data.tables['geometry'].ix[model_mask,['node_nums', 'x', 'y', 'z']].sort_index().values

        node_labels_data[:, 1] = node_labels_data[:, 1] + self.offset['x'] + label_offset
        node_labels_data[:, 2] = node_labels_data[:, 2] + self.offset['y'] + label_offset
        node_labels_data[:, 3] = node_labels_data[:, 3] + self.offset['z'] + label_offset

        view.render_text_dict[self.model_id] = node_labels_data
        view.render_text_dict_str=np.char.mod('%d', node_labels_data[:, 0])

        #self.node_labels=node_labels_data




    def get_allFRF_plotitems(self):
        '''
        Initialize and store all FRF plotitems for 2d plot
        :return:
        '''

        model_mask = self.modal_data.tables['measurement_values']['model_id'] == self.model_id
        measurements = np.unique(self.modal_data.tables['measurement_values'][model_mask]['measurement_id'].values)


        #check number of all measurements
        num_of_meas = len(np.unique(self.modal_data.tables['measurement_values']['measurement_id'].values))
        #TODO: plot only selected FRFs via context menu via extra true/false dialogue


        pens = []
        if (num_of_meas) <= 7:
            for i in range(num_of_meas):
                pens.append(pg.mkPen(COLORS[i], width=1, style=QtCore.Qt.DashLine))
        else:
            color_chg = 256. / num_of_meas * 3

            start_col = np.zeros(np.round(num_of_meas / 3))
            start_col.fill(255)
            end_col = np.zeros(np.round(num_of_meas / 3))

            red_chg = np.arange(0, 255, color_chg)
            green_chg = np.arange(0, 255, color_chg)
            blue_chg = np.arange(0, 255, color_chg)

            red = np.concatenate((start_col, red_chg[::-1], end_col))
            green = np.concatenate((green_chg, start_col, green_chg[::-1]))
            blue = np.concatenate((end_col, blue_chg, start_col))
            for i in range(num_of_meas):
                pens.append(pg.mkPen(color=(red[i], green[i], blue[i]), width=1))  #, style=QtCore.Qt.DashLine))

        grouped = self.modal_data.tables['measurement_values']
        grouped = grouped.set_index(['model_id', 'measurement_id'],
                                    inplace=False)  #copy need to be made so that original data is preserved

        m = 0
        plotitems = {}

        # if all FRFs must be plotted

        for j in measurements:
            data = grouped.ix[self.model_id].ix[j]
            itm_name = 'model_id: ' + str(self.model_id) + ' measurement_id: ' + str(int(j))
            #itm = pg.PlotCurveItem(data['frq'].values, np.imag(data['amp']), pen=pens[m], name=itm_name) #original
            itm = CustomPlotCurveItem(data['frq'].values, np.imag(data['amp']), pen=pens[m], name=itm_name)
            itm.setClickable(True,width=1)
            plotitems[itm_name] = itm
            m = m + 1

        self.view_2d.setLabel('left', 'Amplitude [/]')

        return plotitems

    def get_FRFsum_plotitems(self):
        '''
        Initialize and store FRF sum plotitems for 2d plot
        :return:
        '''

        plotitems = {}

        #select color based on model_id
        if self.uff_tree_index < 7:
            color = COLORS[self.uff_tree_index]
        else:
            ind = self.uff_tree_index - (self.uff_tree_index // 7) * 7
            color = COLORS[ind]

        mv_model_mask = self.modal_data.tables['measurement_values']['model_id'] == self.model_id
        mv = self.modal_data.tables['measurement_values'][mv_model_mask]

        #number of measurements
        num_of_meas = len(np.unique(mv['measurement_id']))

        mv['amp_abs']=mv['amp'].abs()

        # group by freq and sum
        data = mv.groupby(mv['frq']).sum()

        itm_name = 'FRF sum [dB] - model: ' + str(int(self.model_id))
        # itm = pg.PlotCurveItem(data.index.values, np.abs(data['amp_abs'].values)/num_of_meas,
        #                        pen=pg.mkPen(color=color, width=1), name=itm_name)
        itm = CustomPlotCurveItem(data.index.values, np.log10(np.abs(data['amp_abs'].values)/num_of_meas),
                               pen=pg.mkPen(color=color, width=1), name=itm_name)
        itm.setClickable(True,width=1)
        plotitems[itm_name] = itm
        self.view_2d.setLabel('left', 'Amplitude [dB]')

        return plotitems

    def plot_2d(self):


        if self.needs_refresh_2d:

            if self.plot_2d_all_frfs:
                if self.plotted_all_frfs:
                    pass
                else:
                    self.plotitems['all_frfs'] = self.get_allFRF_plotitems()
                    for itm in self.plotitems['all_frfs']:
                        self.view_2d.addItem(self.plotitems['all_frfs'][itm])
                    self.plotted_all_frfs = True
            else:
                self.remove_plotitems('all_frfs')
                self.plotted_all_frfs = False

            # add FRF sum to plot or remove it
            if self.plot_2d_frf_sum:
                if self.plotted_frf_sum:
                    pass
                else:
                    self.plotitems['frf_sum'] = self.get_FRFsum_plotitems()
                    for itm in self.plotitems['frf_sum']:
                        self.view_2d.addItem(self.plotitems['frf_sum'][itm])
                    self.plotted_frf_sum = True
            else:
                self.remove_plotitems('frf_sum')
                self.plotted_frf_sum = False

        self.view_2d.update()
        self.needs_refresh_2d = False

    def remove_plotitems(self, type):
        '''
        Remove given model (plotitem) from 2D view
        type can be: 'all_FRFs', 'FRF_sum'
        '''

        view_items = list(self.view_2d.items)
        if bool(self.plotitems) == True:  # empty dict evaluates to False
            for itm in view_items:
                for itm2 in self.plotitems[type]:
                    if itm == self.plotitems[type][itm2]:
                        self.view_2d.removeItem(self.plotitems[type][itm2])
                        self.view_2d.legend.removeItem(itm2)
            self.view_2d.update()

    def remove_meshitem(self,item):
        '''
        Remove given meshitem from 3D view

        Accepted items:
        self.node_meshitem
        self.elem_meshitem
        '''
        # copy view list, because 'view.items' is updated during for loop(this breaks loop)
        view_items = list(self.view_3d.items)
        for itm in view_items:
            if itm == item:
                self.view_3d.removeItem(item)


    def remove_meshitems_OLD(self):
        '''
        Remove given model (node_meshitem) from 3D view
        '''
        # copy view list, because 'view.items' is updated during for loop(this breaks loop)
        view_items = list(self.view_3d.items)
        for itm in view_items:
            if itm == self.node_meshitem:
                self.view_3d.removeItem(self.node_meshitem)
            if itm == self.elem_meshitem:
                            self.view_3d.removeItem(self.elem_meshitem)

    def remove_meshitems_lcs(self):
        '''
        Remove given model lcs triangles (node_meshitem) from 3D view
        '''
        # copy view list, because 'view.items' is updated during for loop(this breaks loop)
        view_items = list(self.view_3d.items)
        for itm in view_items:
            if itm == self.lcs_meshitem:
                self.view_3d.removeItem(self.lcs_meshitem)

    def remove_node_labels(self):
        try:
            self.view_3d.render_text_dict.pop(self.model_id)
        except KeyError:
            return False
        
        self.view_3d.paintGL()


# Create an instance of the application window and run it
if __name__ == '__main__':
    import sys

    import OpenModal.modaldata as md

    obj = md.ModalData()
    app = QtWidgets.QApplication(sys.argv)

    main_window = AnimationWidget(obj, None, 'en_GB')
    main_window.setGeometry(100, 100, 640, 480)
    main_window.show()

    sys.exit(app.exec_())
    app = QtWidgets.QApplication(sys.argv)
    window = main_window()
    window.setGeometry(80, 80, 1000, 800)
    window.show()
    sys.exit(app.exec_())
