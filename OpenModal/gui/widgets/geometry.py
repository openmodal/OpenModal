
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


from OpenModal.gui.widgets.animation import TableModel,Model

from PyQt5 import QtCore, QtGui,QtWidgets

import pyqtgraph as pg

import numpy as np

from numpy.core.umath_tests import inner1d

import time

import pandas as pd

from pyqtgraph.parametertree import Parameter, ParameterTree

from OpenModal.anim_tools import AnimWidgBase

import os

from OpenModal.keys import keys

import qtawesome as qta

from OpenGL.GL import *

from functools import partial

from OpenModal.gui.templates import COLOR_PALETTE, LIST_FONT_FAMILY, LIST_FONT_SIZE, MENUBAR_WIDTH

from string import Template

SHADER='OpenModal'

GLOPTS= {
        GL_DEPTH_TEST: True,
        GL_BLEND: False,
        GL_ALPHA_TEST: False,
        GL_CULL_FACE: False}
        #'glLightModeli':(GL_LIGHT_MODEL_TWO_SIDE, GL_TRUE)}
SMOOTH=True
COMPUTENORMALS=True
DRAW_EDGES_NODES=False
DRAW_EDGES_ELEMENTS=True
DRAW_EDGES_GCS=False

# ## Switch to using white background and black foreground
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')



class CustomQTableView(QtWidgets.QTableView):

    def __init__(self,parent):
        super(self.__class__, self).__init__(parent)
        self.catch=False #for catching right/left arrow keypress events in editor mode
        self.keys = [QtCore.Qt.Key_Left,
                     QtCore.Qt.Key_Right]

    def focusInEvent(self, event):
        self.catch = False
        return QtWidgets.QTableView.focusInEvent(self, event)

    def focusOutEvent(self, event):
        self.catch = True
        return QtWidgets.QTableView.focusOutEvent(self, event)

    def event(self, event):
        if self.catch and event.type() == QtCore.QEvent.KeyRelease and event.key() in self.keys:
            self._moveCursor(event.key())

        return QtWidgets.QTableView.event(self,event)

    def keyPressEvent(self, event):
        if not self.catch:
            return QtWidgets.QTableView.keyPressEvent(self, event)

        self._moveCursor(event.key())


    def _moveCursor(self, key):
        row = self.currentIndex().row()
        col = self.currentIndex().column()

        if key == QtCore.Qt.Key_Left and col > 0:
            col -= 1

        elif key == QtCore.Qt.Key_Right and col < (self.model().columnCount()-1):
            col += 1

        elif key == QtCore.Qt.Key_Up and row > 0:
            row -= 1

        elif key == QtCore.Qt.Key_Down and row < (self.model().rowCount()-1):
            row += 1

        else:
            return

        self.setCurrentIndex(self.model().createIndex(row,col))
        self.edit(self.currentIndex())

    def mousePressEvent(self,event):
        """
        Reimplement mousePressEvent in order to deselect rows when clicking into blank space
        """

        if self.indexAt(event.pos()).isValid():
            super(self.__class__, self).mousePressEvent(event)

        else:
            #user has clicked into blank space...clear selection and send signal
            self.selectionModel().clearSelection()

class GeometryWidget(AnimWidgBase):

    # def __init__(self, modaldata_object,status_bar,language, preferences=dict(), desktop_widget=None, parent=None):

    def __init__(self, *args, **kwargs):

        super(self.__class__, self).__init__(*args, **kwargs)
        self.setContentsMargins(0, 0, 0, 0)
        self.selection=[] # list of nodes clicked with mouse in 3d view
        self.selection_ind=[] # list of indicies of selected nodes
        self.selection_color=[] # original model color
        self.selected_elem_ids=[] #element ids of elements selected in element table view
        self.selected_elem_col=None #color of selected elements
        self.activated_models=[] # model_ids of currently activated models

        #default widget mode!
        self.widget_mode = 'nodes'

        #connect cliked signal from 3d view
        self.model_view.clicked_signal.clicked.connect(self.mouse_clicked)

    def color_selected_node(self,test,nodes_index,nodes):

        #index of the node in the original dataframe
        ind=nodes_index[test]

        #check if node was already selected, if it was...deselect it
        if ind in self.selection_ind:
            #index already selected -> deselect it
            loc=self.selection_ind.index(ind)
            del self.selection_ind[loc]
            del self.selection[loc]
            #if ind already in selection -> set default color
            self.modaldata.tables['geometry'].ix[ind, 'clr_r']=self.selection_color[0]
            self.modaldata.tables['geometry'].ix[ind, 'clr_g']=self.selection_color[1]
            self.modaldata.tables['geometry'].ix[ind, 'clr_b']=self.selection_color[2]
            self.modaldata.tables['geometry'].ix[ind, 'clr_a']=self.selection_color[3]

        else:
            #index not yet selected -> add it to selection
            self.selection.append(nodes.iloc[test][['node_nums','x','y','z','model_id','color']].values[0])
            self.selection_ind.append(ind)
            self.selection_color=[self.modaldata.tables['geometry'].ix[ind, 'clr_r'].values[0],
                                  self.modaldata.tables['geometry'].ix[ind, 'clr_g'].values[0],
                                  self.modaldata.tables['geometry'].ix[ind, 'clr_b'].values[0],
                                  self.modaldata.tables['geometry'].ix[ind, 'clr_a'].values[0]]

            self.modaldata.tables['geometry'].ix[ind, 'clr_r']=1
            self.modaldata.tables['geometry'].ix[ind, 'clr_g']=0
            self.modaldata.tables['geometry'].ix[ind, 'clr_b']=0
            self.modaldata.tables['geometry'].ix[ind, 'clr_a']=1

    def handle_node_clicked(self):
        '''
        Check if click was near a node, if it was then add it to selection, if coincident with previously selected node,
        deselect it. Also node is colored if selected.
        :return:
        '''

        #get cube size for determening selection sphere size
        for model_id, model_obj in self.models.items():
            if model_obj.activated:
                cube_scale, lcs_scale=model_obj.get_cube_and_lcs_scale()

        #look only among activated models
        act_mod=[]
        for model_id, model_obj in self.models.items():
            if model_obj.activated:
                act_mod.append(model_obj.model_id)

        nodes=self.modaldata.tables['geometry'][self.modaldata.tables['geometry']['x'].notnull()]
        nodes=nodes[nodes['model_id'].isin(act_mod)]
        nodes_index=nodes.index.values

        ind=-1
        node_data=nodes.ix[:,['x','y','z']].values

        # CHECK if nodes are near clicked point
        start_point=self.model_view.ray[0] #get ray data from 3d view widget
        ray_dir=self.model_view.ray[1]

        #sel_sph_r=0.05 # selection sphere radius
        sel_sph_r=cube_scale*3

        aux_1=-node_data+start_point
        aux_1=aux_1.astype(np.float64)

        b=inner1d(ray_dir,aux_1)
        c=inner1d(aux_1,aux_1)-sel_sph_r**2

        #get boolean array - true means that node is under mouse
        test=(b**2-c)>=0

        #check for coincident nodes!
        coincident_nodes=np.sum(test)-1 # =0 if only one node clicked, >0 if multiple nodes clicked


        if coincident_nodes==0:
            self.color_selected_node(test,nodes_index,nodes)

            self.plot_activated_models()
        elif coincident_nodes>0:
            #TODO: handle this!
            print('multiple nodes clicked! - NOT HANDLED YET')
        elif coincident_nodes==-1:
            #TODO: handle this!
            print('blank space clicked')

    def clear_node_selection(self):
        """
        Clear selected nodes and restore node colors to default
        :return:
        """
        self.selection=[]
        for ind in self.selection_ind:
            self.modaldata.tables['geometry'].ix[ind, 'clr_r']=self.selection_color[0]
            self.modaldata.tables['geometry'].ix[ind, 'clr_g']=self.selection_color[1]
            self.modaldata.tables['geometry'].ix[ind, 'clr_b']=self.selection_color[2]
            self.modaldata.tables['geometry'].ix[ind, 'clr_a']=self.selection_color[3]
        self.selection_ind=[]
        self.selection_color=[]

        self.plot_activated_models()


    def mouse_clicked(self):
        """
        For 2D plot cross hair selection
        :param evt:
        :return:
        """

        #only select nodes if widget is not in geometry mode
        if self.widget_mode!='nodes':
            self.handle_node_clicked()

            if self.widget_mode=='lines':
                nr_of_nodes=2
                if len(self.selection)==nr_of_nodes:
                    self.addElement(nr_of_nodes)
                    self.clear_node_selection()

            if self.widget_mode=='elements':
                nr_of_nodes=3
                if len(self.selection)==nr_of_nodes:
                    self.addElement(nr_of_nodes)
                    self.clear_node_selection()

    def addElement(self,nr_of_nodes):
        """
        Add selection data to modal_data object as new element
        :return:
        """

        #get next pandas index
        if len(self.modaldata.tables['elements_index'].index)==0:
            ind=0
            node_ind=0
            element_id=1
        else:
            ind= self.modaldata.tables['elements_index'].index.max() + 1
            element_id= self.modaldata.tables['elements_index']['element_id'].max() + 1
            node_ind= self.modaldata.tables['elements_values'].index.max() + 1


        #store data data from selection
        #store element
        model_id=self.selection[0][4]

        def get_color(id,elem_type):
            for model_id, model_obj in self.models.items():
                if model_id==id:
                    if elem_type=='triangle':
                        color=model_obj.cur_triangle_color
                    elif elem_type=='line':
                        color=model_obj.cur_line_color
                    return color

        aux_color=self.selection[0][5]

        if nr_of_nodes==3:
            element_descriptor='triangle'
            color=get_color(model_id,element_descriptor)
            self.modaldata.tables['elements_index'].loc[ind]=[model_id, element_id, element_descriptor, aux_color, nr_of_nodes,
                                                              color.red() / 255., color.green() / 255., color.blue() / 255., color.alpha() / 255.]
            #store nodes
            for i in range(nr_of_nodes):
                node_id=self.selection[i][0]
                node_pos=i
                self.modaldata.tables['elements_values'].loc[node_ind]=[model_id, element_id, node_id, node_pos]
                node_ind=node_ind+1

        if nr_of_nodes==2:
            element_descriptor='line'
            color=get_color(model_id,element_descriptor)
            self.modaldata.tables['elements_index'].loc[ind]=[model_id, element_id, element_descriptor, aux_color, nr_of_nodes,
                                                              color.red() / 255., color.green() / 255., color.blue() / 255., color.alpha() / 255.]
            #store nodes
            for i in range(nr_of_nodes):
                node_id=self.selection[i][0]
                node_pos=i
                self.modaldata.tables['elements_values'].loc[node_ind]=[model_id, element_id, node_id, node_pos]
                node_ind=node_ind+1

            ## for line the third node is same as second

        #update table model
        self.populate_elem_table_view([model_id])

    def delete_selection_aux(self):
        """
        Delete selection in table view via context menu
        :return:
        """
        if self.gcs_type==0:
            self.delete_selection(self.geom_table_view,self.geom_table_model)
        if self.gcs_type==1:
            self.delete_selection(self.cyl_geom_table_view,self.cyl_geom_table_model)

    def delete_selection(self,geom_table_view,geom_table_model):
            if self.widget_mode=='nodes':

                cells=geom_table_view.selectedIndexes()
                cells.sort()

                # start index is where first cell is selected (caution: table view shows only a view into table model,
                #  selections indexes are relative to current view!)
                curr_row=cells[0].model().datatable.index.values[0]

                cols=[]
                rows=[]
                for cell in cells:
                    rows.append(curr_row+cell.row())
                    cols.append(cells[0].model().datatable.columns[cell.column()])

                geom_table_model.datatable.ix[rows,cols]=np.nan
                geom_table_model.dataIn.ix[rows,cols]=np.nan # this is necessary as update method does not work with NANs


                geom_table_model.dataIn.update(geom_table_model.datatable)


                geom_table_model.dataChanged.emit(geom_table_model.createIndex(0, 0),
                                   geom_table_model.createIndex(geom_table_model.rowCount(0),
                                                    geom_table_model.columnCount(0)))
                geom_table_model.layoutChanged.emit()

            if self.widget_mode=='lines' or self.widget_mode=='elements':

                rows=self.elem_table_view.selectionModel().selectedRows()

                rows.sort()


                el_id_list=[]
                for row in rows:
                    el_id_list.append(self.elem_table_model.datatable['element_id'].iloc[[row.row()]].values[0])

                element_id_mask=self.modaldata.tables['elements_values']['element_id'].isin(el_id_list)
                self.modaldata.tables['elements_values'].drop(self.modaldata.tables['elements_values']['element_id'].index[element_id_mask], inplace=True)

                element_id_mask=self.elem_table_model.datatable['element_id'].isin(el_id_list)
                self.elem_table_model.datatable.drop(self.elem_table_model.datatable['element_id'].index[element_id_mask],inplace=True) # change stuff in GUI
                self.elem_table_model.dataIn.update(self.elem_table_model.datatable)

                element_id_mask=self.elem_table_model.dataIn['element_id'].isin(el_id_list)
                self.elem_table_model.dataIn.drop(self.elem_table_model.dataIn['element_id'].index[element_id_mask],inplace=True) # change stuff directly in modal data obj

                #PyQt
                self.elem_table_model.dataChanged.emit(self.elem_table_model.createIndex(0, 0),
                                   self.elem_table_model.createIndex(self.elem_table_model.rowCount(0),
                                                    self.elem_table_model.columnCount(0)))
                self.elem_table_model.layoutChanged.emit()



    def copy_selection(self):
            if self.gcs_type==0:
                cells=self.geom_table_view.selectedIndexes()
            elif self.gcs_type==1:
                cells=self.cyl_geom_table_view.selectedIndexes()

            cells.sort()

            curr_row=cells[0].row()
            text=''
            for cell in cells:
                if len(text)==0:
                    text=str(cell.data())
                else:
                    if cell.row()!=curr_row:
                        #text=text+' \\n '
                        text=text+os.linesep # os independent newline seperator
                        curr_row=curr_row+1
                    else:
                        text=text+'\t'
                    text=text+str(cell.data())

            QtCore.QCoreApplication.instance().clipboard().setText(text)


    def paste_selection(self):


            text=QtCore.QCoreApplication.instance().clipboard().text()


            lines=text.splitlines()

            if self.gcs_type==0:
                cells=self.geom_table_view.selectedIndexes()
            elif self.gcs_type==1:
                cells=self.cyl_geom_table_view.selectedIndexes()
            cells.sort()

            # start index is where first cell is selected (caution: table view shows only a view into table model,
            #  selections indexes are relative to current view!)
            curr_row=cells[0].model().datatable.index.values[0]+cells[0].row()
            curr_col=cells[0].column()

            # get selection dimensions
            num_of_cols=len(lines[0].split('\t'))
            num_of_rows=len(lines)

            # expand table if number of rows in clipboard is larger than current table size
            for model_id in self.activated_models:
                #get node index corresponding with existing geomtry table
                model_mask=self.modaldata.tables['geometry'].ix[:,'model_id']==model_id
                node_index=self.modaldata.tables['geometry'].ix[model_mask].index

                if (curr_row+num_of_rows)>len(node_index):
                    # add rows for selected model
                    rows_to_add=curr_row+num_of_rows-len(node_index)
                    self.add_geom_rows(rows_to_add=rows_to_add)

            # duplicate stuff from clipboard based on the selection size
            # we want to copy rows
            if num_of_cols==(cells[-1].column()-cells[0].column()+1):
                copy_rows=(cells[-1].row()-cells[0].row()+1)/num_of_rows
                if copy_rows>1:
                    lines=lines*np.floor(copy_rows)

            # we want to copy columns
            elif num_of_rows==(cells[-1].row()-cells[0].row()+1):
                copy_cols=(cells[-1].column()-cells[0].column()-num_of_cols+1)/num_of_cols
                if copy_cols>0:
                    lines=[(i+('\t'+i)*np.floor(copy_cols)) for i in lines]


            for line in lines:
                data=line.split('\t')
                for val in data:
                    if val=='':
                        #skip empty cell
                        curr_col=curr_col+1
                    else:
                        try:
                            if self.gcs_type==0:
                                self.geom_table_model.datatable.set_value(curr_row, cells[0].model().datatable.columns[curr_col], float(val))
                            if self.gcs_type==1:
                                self.cyl_geom_table_model.datatable.set_value(curr_row, cells[0].model().datatable.columns[curr_col], float(val))
                        except ValueError:
                            if self.gcs_type==0:
                                self.geom_table_model.datatable.set_value(curr_row, cells[0].model().datatable.columns[curr_col], float(val.replace(',', '.')))
                            if self.gcs_type==1:
                                self.cyl_geom_table_model.datatable.set_value(curr_row, cells[0].model().datatable.columns[curr_col], float(val.replace(',', '.')))


                        curr_col=curr_col+1
                curr_col=cells[0].column() #restart column index
                curr_row=curr_row+1

            if self.gcs_type==0:
                self.geom_table_model.dataIn.update(self.geom_table_model.datatable)


                self.geom_table_model.dataChanged.emit(self.geom_table_model.createIndex(0, 0),
                                   self.geom_table_model.createIndex(self.geom_table_model.rowCount(0),
                                                    self.geom_table_model.columnCount(0)))


                self.geom_table_model.layoutChanged.emit()

            if self.gcs_type==1:
                self.cyl_geom_table_model.dataIn.update(self.geom_table_model.datatable)


                self.cyl_geom_table_model.dataChanged.emit(self.cyl_geom_table_model.createIndex(0, 0),
                                       self.cyl_geom_table_model.createIndex(self.cyl_geom_table_model.rowCount(0),
                                                        self.cyl_geom_table_model.columnCount(0)))


                self.cyl_geom_table_model.layoutChanged.emit()

    def keyPressEvent(self,evt):
        """
        Catch Ctrl+C and Ctrl+V to handle copying from clipboard
        Catch Delete to delete values in selected cells
        :param evt:
        :return:
        """

        if evt.key()==QtCore.Qt.Key_C and evt.modifiers()==QtCore.Qt.ControlModifier:
            self.copy_selection()

        if evt.key()==QtCore.Qt.Key_V and evt.modifiers()==QtCore.Qt.ControlModifier:
            self.paste_selection()

        if evt.key()==QtCore.Qt.Key_Delete:
            self.delete_selection_aux()


        super(self.__class__,self).keyPressEvent(evt)

    def create_toolbar_actions(self):

        super(self.__class__,self).create_toolbar_actions()
        self.act_new_model = QtWidgets.QAction('New model', self,
                                    statusTip='Create new model', triggered=self.new_model)

        self.act_delete_model = QtWidgets.QAction('Delete model', self,
                                            statusTip='Delete model', triggered=self.delete_model_dialog)

        self.act_nodes_mode = QtWidgets.QAction('Nodes', self,
                                                  statusTip='Geometry input mode', triggered=self.nodes_data_mode)

        self.act_lines_mode = QtWidgets.QAction('Lines', self,
                                                  statusTip='Lines input mode', triggered=self.lines_data_mode)

        self.act_elements_mode = QtWidgets.QAction('Elements', self,
                                                  statusTip='Elements input mode', triggered=self.elements_data_mode)
    def create_model_view_actions(self):

        super(self.__class__,self).create_model_view_actions()

        self.elem_desel_act = QtWidgets.QAction('Deselect elements', self, checkable=False,
                                               statusTip='Clear element selection', triggered=partial(self.handle_elem_select,True))

    def nodes_data_mode(self):
        self.elem_table_view.hide()
        if self.gcs_type==0:
            self.geom_table_view.show()
            self.cyl_geom_table_view.hide()
            #cartesian gcs
            self.geom_table_model.update(self.modaldata.tables['geometry'], self.activated_models, self.fields)


        elif self.gcs_type==1:
            self.cyl_geom_table_view.show()
            self.geom_table_view.hide()
            #cylindrical csys
            self.cyl_geom_table_model.update(self.modaldata.tables['geometry'], self.activated_models, self.cyl_fields)
        self.widget_mode = 'nodes'
        self._button3.setChecked(True)
        self._button6.setChecked(False)
        self._button4.setChecked(False)

    def lines_data_mode(self):
        self.elem_table_view.show()
        self.geom_table_view.hide()
        self.cyl_geom_table_view.hide()
        self.widget_mode = 'lines'
        self._button3.setChecked(False)
        self._button6.setChecked(True)
        self._button4.setChecked(False)

    def elements_data_mode(self):
        self.elem_table_view.show()
        self.geom_table_view.hide()
        self.cyl_geom_table_view.hide()
        self.widget_mode = 'elements'
        self._button3.setChecked(False)
        self._button6.setChecked(False)
        self._button4.setChecked(True)


    def model_view_context_menu(self, pos):
        menu = QtWidgets.QMenu()

        menu.addAction(self.act_fit_view)
        menu.addAction(self.elem_desel_act)

        display_menu = menu.addMenu('Display')
        display_menu.addAction(self.plot_nodes_act)
        display_menu.addAction(self.plot_lines_act)
        display_menu.addAction(self.plot_elements_act)
        display_menu.addAction(self.plot_node_lcs_act)
        display_menu.addAction(self.plot_node_labels_act)
        display_menu.addAction(self.plot_gcs_act)

        #display_menu.addMenu('Trace lines')

        color_menu = menu.addMenu('Colors')
        color_menu.addAction(self.node_color_act)
        color_menu.addAction(self.line_color_act)
        color_menu.addAction(self.elem_color_act)

        csys_menu = menu.addMenu('Change csys')
        csys_menu.addAction(self.cart_csys_act)
        csys_menu.addAction(self.cyl_csys_act)

        menu.exec_(QtGui.QCursor.pos())


    def paintEvent(self, event):

        # button sizes
        w = 140 #this is overridden by css
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
        self._button.setGeometry(x,y,w,h)
        self._button5.setGeometry(x,y+offset,w,h)
        self._button2.setGeometry(x,y+2*offset,w,h)
        self._b_geom_prim.setGeometry(x,y+3*offset,w,h)

        # positioning of elements/geometry table
        table_width=window_width*0.6
        table_height=window_height*0.3
        table_x=window_width/2-table_width/2
        table_y=0.68*window_height

        x_btn=window_width/2-1.5*w-5
        y_btn=40
        self._button3.setGeometry(x_btn,table_y-y_btn,w,h)
        self._button6.setGeometry(x_btn+w+5,table_y-y_btn,w,h)
        self._button4.setGeometry(x_btn+2*w+10,table_y-y_btn,w,h)

        self.cyl_geom_table_view.setGeometry(table_x,table_y,table_width,table_height)
        self.cyl_geom_table_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        self.geom_table_view.setGeometry(table_x,table_y,table_width,table_height)
        self.geom_table_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)


        self.elem_table_view.setGeometry(table_x,table_y,table_width,table_height)
        self.elem_table_view.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Stretch)

        # selected model label
        #self._label.setGeometry(window_width/2-self._label.width()/2,0.1*window_height,200,20)

        # create buttons for available models
        offset=0
        x = x_margin
        y = 0.2*window_height
        for model_id,button in self.model_buttons.items():
            width = self._button.width()+20
            height = self._button.height()
            button.setGeometry(x,y+offset,width,height)
            offset=offset+height+5

    def table_view_context_menu(self, pos):
        menu = QtWidgets.QMenu()
        menu.addAction(self.act_delete)
        menu.addAction(self.act_copy)
        menu.addAction(self.act_paste)
        menu.addAction(self.elem_desel_act)
        menu.addAction(self.add_rows_act)
        menu.exec_(QtGui.QCursor.pos())

    def model_btn_context_menu(self, pos):
        #get model button which was right clicked
        self.sending_button = self.sender()

        menu = QtWidgets.QMenu()
        menu.addAction(self.act_model_rename)
        menu.exec_(QtGui.QCursor.pos())

    def model_btn_context_menu_act(self):
        self.act_model_rename = QtWidgets.QAction('Rename', self, statusTip='Rename model', triggered=self.rename_model)

    def context_menu_act(self):

        self.act_delete = QtWidgets.QAction('Delete', self, statusTip='Delete selection', triggered=self.delete_selection_aux)
        self.act_copy = QtWidgets.QAction('Copy', self, statusTip='Copy selection', triggered=self.copy_selection)
        self.act_paste = QtWidgets.QAction('Paste', self, statusTip='Paste selection', triggered=self.paste_selection)
        self.add_rows_act = QtWidgets.QAction('Add 100 rows', self, checkable=False,
                                               statusTip='Add 100 blank rows', triggered=partial(self.add_geom_rows,rows_to_add=100))



    def create_layout(self):
        """
        Create layout of the central Qwidget and add widgets
        :return:
        """
        super(self.__class__,self).create_layout()

        self._button = QtWidgets.QPushButton(qta.icon('fa.plus-circle', color='white'),'New model', self)
        self._button.setObjectName('medium')
        self._button.clicked.connect(self.new_model)

        self._button5 = QtWidgets.QPushButton(qta.icon('fa.trash-o', color='white'),'Delete model', self)
        self._button5.setObjectName('medium')
        self._button5.clicked.connect(self.delete_model_dialog)

        self._button2 = QtWidgets.QPushButton(qta.icon('fa.search', color='white'),'Fit view', self)
        self._button2.setObjectName('medium')
        self._button2.clicked.connect(self.autofit_3d_view)

        self._b_geom_prim= QtWidgets.QPushButton(qta.icon('fa.industry', color='white'),'Create geometry', self)
        self._b_geom_prim.setObjectName('medium')
        self._b_geom_prim.clicked.connect(self.create_geom_primitive)

        self._button3 = QtWidgets.QPushButton('Add nodes', self)
        self._button3.setObjectName('table_button')

        self._button3.setCheckable(True)
        self._button3.setChecked(True)
        self._button3.clicked.connect(self.nodes_data_mode)

        self._button6 = QtWidgets.QPushButton('Add lines', self)
        self._button6.setObjectName('table_button')
        self._button6.setCheckable(True)
        self._button6.clicked.connect(self.lines_data_mode)

        self._button4 = QtWidgets.QPushButton('Add triangles', self)
        self._button4.setObjectName('table_button')
        self._button4.setCheckable(True)
        self._button4.clicked.connect(self.elements_data_mode)

        # common for both tables
        self.context_menu_act() #create actions for table context menu

        # Context menu actions for model buttons
        self.model_btn_context_menu_act()

        # geometry Table (cartesian coordinate system)
        self.geom_table_model = TableModel(self)
        self.fields = ['node_nums','x', 'y', 'z','thz', 'thy', 'thx' , 'model_id']
        self.geom_table_model.update(self.modaldata.tables['geometry'], [0], self.fields) # show some data
        self.geom_table_view = CustomQTableView(self)
        self.geom_table_view.setModel(self.geom_table_model)
        self.geom_table_model.dataChanged.connect(self.geometry_changed)
        self.geom_table_view.setSortingEnabled(False)
        self.geom_table_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.geom_table_view.customContextMenuRequested.connect(self.table_view_context_menu)



        #replace header from dataframe with custom one
        self.geom_table_model.header_labels=[keys['node_nums']['15'],
                                             keys['x']['15'],
                                             keys['y']['15'],
                                             keys['z']['15'],
                                             keys['thz']['15'],
                                             keys['thy']['15'],
                                             keys['thx']['15'] ,
                                             keys['model_id']['15']]



        # geometry Table (cylindrical coordinate system)
        self.cyl_geom_table_model = TableModel(self)
        self.cyl_fields = ['node_nums','r', 'phi', 'z','cyl_thz', 'thy', 'thx' , 'model_id']
        self.cyl_geom_table_model.update(self.modaldata.tables['geometry'], [0], self.cyl_fields) # show some data
        self.cyl_geom_table_view = CustomQTableView(self)
        self.cyl_geom_table_view.setModel(self.cyl_geom_table_model)
        self.cyl_geom_table_model.dataChanged.connect(self.geometry_changed)
        self.cyl_geom_table_view.hide()
        self.cyl_geom_table_view.setSortingEnabled(False)
        self.cyl_geom_table_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.cyl_geom_table_view.customContextMenuRequested.connect(self.table_view_context_menu)

        #replace header from dataframe with custom one
        self.cyl_geom_table_model.header_labels=[keys['node_nums']['15'],
                                             keys['r']['15'],
                                             keys['phi']['15'],
                                             keys['z']['15'],
                                             keys['cyl_thz']['15'],
                                             keys['thy']['15'],
                                             keys['thx']['15'] ,
                                             keys['model_id']['15']]


        # elements Table
        self.elem_table_model = TableModel(self)

        #print(self.modal_data.tables['analysis_index'])
        self.elem_fields = ['model_id', 'element_id', 'element_descriptor', 'color',
                                                      'nr_of_nodes']
        self.elem_table_model.update(self.modaldata.tables['elements_index'], [0], self.elem_fields) # show some data
        self.elem_table_view = CustomQTableView(self)
        self.elem_table_view.setModel(self.elem_table_model)
        self.elem_table_view.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.elem_table_model.dataChanged.connect(self.plot_activated_models)
        self.elem_table_view.setMinimumHeight(150)

        self.elem_table_view.setSortingEnabled(True)
        self.elem_table_view.hide()
        self.elem_table_view.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.elem_table_view.customContextMenuRequested.connect(self.table_view_context_menu)

        #replace header from dataframe with custom one
        self.elem_table_model.header_labels=[keys['model_id']['15'],
                                             keys['element_id']['15'],
                                             keys['element_descriptor']['15'],
                                             keys['color']['15'],
                                             keys['nr_of_nodes']['15']]
        self.elem_table_view.setColumnHidden(3,True) #hide color
        self.elem_table_view.setColumnHidden(4,True) #hide nr_of_nodes

        selection = self.elem_table_view.selectionModel()
        selection.selectionChanged.connect(self.handle_elem_select)

    def restore_elem_color(self,elem_ids):
        """
        Change element color to original (before selection)
        :param elem_ids:
        :return:
        """
        #restore color
        element_id_mask=self.modaldata.tables['elements_index']['element_id'].isin(elem_ids)

        self.modaldata.tables['elements_index'].ix[element_id_mask, 'clr_r']=self.selected_elem_col[0]  # rbg values 0-1
        self.modaldata.tables['elements_index'].ix[element_id_mask, 'clr_g']=self.selected_elem_col[1]  # rbg values 0-1
        self.modaldata.tables['elements_index'].ix[element_id_mask, 'clr_b']=self.selected_elem_col[2]  # rbg values 0-1
        self.modaldata.tables['elements_index'].ix[element_id_mask, 'clr_a']=self.selected_elem_col[3]  # alpha values 0-1

    def change_elem_color(self,elem_ids,selection_color):
        #change color of selected elements
        element_id_mask=self.modaldata.tables['elements_index']['element_id'].isin(elem_ids)

        #store current element color
        self.selected_elem_col= self.modaldata.tables['elements_index'][element_id_mask][['clr_r', 'clr_g', 'clr_b', 'clr_a']].values[0, :]

        self.modaldata.tables['elements_index'].ix[element_id_mask, 'clr_r']= selection_color[0] / 255.  # rbg values 0-1
        self.modaldata.tables['elements_index'].ix[element_id_mask, 'clr_g']= selection_color[1] / 255.  # rbg values 0-1
        self.modaldata.tables['elements_index'].ix[element_id_mask, 'clr_b']= selection_color[2] / 255.  # rbg values 0-1
        self.modaldata.tables['elements_index'].ix[element_id_mask, 'clr_a']= selection_color[3] / 255.  # alpha values 0-1

    def handle_elem_select(self,deselect=False):
        """
        Change color of elements selected in element table
        :return:
        """

        #element selection color
        #TODO: move this to color pallete?
        #TODO: fix - selecting mulitple lines and triangles changes their color -  element color change must be element type sensitive
        rgba_color = QtGui.QColor(255, 0, 0, 255)
        rgba_color = pg.colorTuple(rgba_color)

        rows=self.elem_table_view.selectionModel().selectedRows()
        rows.sort()

        new_elem_ids=[] # newly selected elements
        for row in rows:
           new_elem_ids.append(self.elem_table_model.datatable['element_id'].iloc[[row.row()]].values[0])

        if deselect==True:
            self.restore_elem_color(self.selected_elem_ids)
            self.selected_elem_ids=[]
        else:
            #restore color of previously selected elements
            if len(self.selected_elem_ids)!=0:
                self.restore_elem_color(self.selected_elem_ids)
            #change color of selected elements
            if len(new_elem_ids)!=0:
                self.change_elem_color(new_elem_ids,rgba_color)

            # store current selection
            self.selected_elem_ids=new_elem_ids

        self.plot_activated_models(wheel_event=True)


    def create_geom_primitive(self):
        """
        Create geometry primitives (nodes + triangles) for currently active model
        :return:
        """
        response,input_data=dialog_geom_primitives.return_data()

        if response==1:
            if input_data['geom_type']=='line':
                self.create_line_geom(input_data)
            if input_data['geom_type']=='plane':
                self.create_plane_geom(input_data)
            if input_data['geom_type']=='box':
                self.create_box_geom(input_data)
            if input_data['geom_type']=='cylinder':
                self.create_cyl_geom(input_data)


    def create_line_geom(self,line_data):
        """
        Create line geometry based on user input (for currently active model)
        :return:
        """

        xs=float(line_data['xs']) # s = start point
        ys=float(line_data['ys'])
        zs=float(line_data['zs'])
        xe=float(line_data['xe']) # e = end point
        ye=float(line_data['ye'])
        ze=float(line_data['ze'])
        num_of_points=int(line_data['num_of_points'])
        start_num=float(line_data['start_num'])

        s_point=np.array((xs,ys,zs))
        e_point=np.array((xe,ye,ze))

        for model_id in self.activated_models:

            node_nums=np.arange(start_num,start_num+num_of_points)

            line_vec=(e_point-s_point)
            dir_arr=np.tile(line_vec,(num_of_points,1))

            div_arr=np.linspace(0,1,num_of_points)
            div_arr_rshp=np.tile(div_arr.reshape(num_of_points,1),3)

            nodes=np.tile(s_point,(num_of_points,1))+div_arr_rshp*dir_arr

            #realign index in order to prevent double node names (geometry data frame starts with 1 by default)
            #node_index=node_nums-1

            #get node index corresponding with existing geomtry table
            model_mask=self.modaldata.tables['geometry'].ix[:,'model_id']==model_id
            node_mask=self.modaldata.tables['geometry'].ix[:,'node_nums'].isin(node_nums)
            final_mask=model_mask & node_mask
            node_index=self.modaldata.tables['geometry'].ix[final_mask].index

            if len(node_nums)>len(node_index):
                # add rows for selected model
                rows_to_add=len(node_nums)-len(node_index)
                self.add_geom_rows(rows_to_add=rows_to_add)
                # get index
                model_mask=self.modaldata.tables['geometry'].ix[:,'model_id']==model_id
                node_mask=self.modaldata.tables['geometry'].ix[:,'node_nums'].isin(node_nums)
                final_mask=model_mask*node_mask
                node_index=self.modaldata.tables['geometry'].ix[final_mask].index

            #create node data
            df=pd.DataFrame(index=node_index, columns=self.modaldata.tables['geometry'].columns)
            df['model_id']=model_id
            df['node_nums']=node_nums
            df['x']=nodes[:,0]
            df['y']=nodes[:,1]
            df['z']=nodes[:,2]
            #TODO: oritent lcs according to line orientation
            df['thx']=0
            df['thy']=0
            df['thz']=0
            rgba_color = pg.colorTuple(QtGui.QColor(0,255,0,255))
            df['clr_r']=rgba_color[0]/ 255.  # rbg values 0-1
            df['clr_g']=rgba_color[1]/ 255.  # rbg values 0-1
            df['clr_b']=rgba_color[2]/ 255.  # rbg values 0-1
            df['clr_a']=rgba_color[3]/ 255.  # alpha values 0-1

            #calculate r,phi from x,y
            df['r'] = np.sqrt(df['x']**2 + df['y']**2)
            df['phi'] = np.arcsin(df['y']/df['r'])*180./np.pi
            df['cyl_thz']= 0


            #update geometry table with new data
            self.modaldata.tables['geometry'].update(df)#,overwrite=True)
            #self.modal_data.tables['geometry']=pd.concat([self.modal_data.tables['geometry'],df])

            #create element data
            #get next pandas index
            if len(self.modaldata.tables['elements_index'].index)==0:
                ind=0
                elem_node_ind=0
                element_id=0
            else:
                ind= self.modaldata.tables['elements_index'].index.max() + 1
                element_id= self.modaldata.tables['elements_index']['element_id'].max() + 1
                elem_node_ind= self.modaldata.tables['elements_values'].index.max() + 1

            for model_id_aux, model_obj_aux in self.models.items():
                if model_obj_aux.model_id==model_id:
                    color=model_obj_aux.cur_triangle_color
            element_descriptor='line'
            nr_of_nodes=2

            tot_num_of_elem=num_of_points-1 #total number of elements
            elem_nums=np.arange(ind,ind+tot_num_of_elem)
            elem_ids=np.arange(element_id,element_id+tot_num_of_elem)
            df_elem=pd.DataFrame(index=elem_nums, columns=self.modaldata.tables['elements_index'].columns)
            df_elem['model_id']=model_id
            df_elem['element_id']=elem_ids
            df_elem['element_descriptor']=element_descriptor
            df_elem['color']=color
            df_elem['nr_of_nodes']=nr_of_nodes
            df_elem['clr_r']=color.red()/255.
            df_elem['clr_g']=color.green()/255.
            df_elem['clr_b']=color.blue()/255.
            df_elem['clr_a']=color.alpha()/255.

            if len(self.modaldata.tables['elements_index'].index)==0:
                self.modaldata.tables['elements_index']=df_elem
            else:
                #self.modal_data.tables['elements_index'].update(df_elem)#,overwrite=True)
                self.modaldata.tables['elements_index']=pd.concat([self.modaldata.tables['elements_index'], df_elem])

            #store nodes

            #tot_elem_nums=circ_div*(height_div-1)*2 #total number of  elements
            #elem_nums=np.arange(element_id,element_id+tot_elem_nums+1)

            #walk through nodes and store elements
            pos_1=[]
            pos_2=[]
            node_number=start_num


            for i in range(1,int(num_of_points)):
                pos_1.append(node_number)
                pos_2.append(node_number+1)

                node_number=node_number+1


            df_elem_index=np.arange(elem_node_ind,elem_node_ind+len(np.tile(elem_ids,2)))
            df_elem_nodes=pd.DataFrame(index=df_elem_index, columns=self.modaldata.tables['elements_values'].columns)
            #df_elem_nodes['model_id']=model_id
            df_elem_nodes['element_id']=np.tile(elem_ids,2)
            df_elem_nodes['node_id']=np.asarray(pos_1+pos_2) #node numbers
            df_elem_nodes['node_pos']=np.repeat([1,2],len(pos_1)) #node position in element

            if len(self.modaldata.tables['elements_values'].index)==0:
                self.modaldata.tables['elements_values']=df_elem_nodes
            else:
                #self.modal_data.tables['elements_values'].update(df_elem_nodes)#,overwrite=True)
                self.modaldata.tables['elements_values']=pd.concat([self.modaldata.tables['elements_values'], df_elem_nodes])

            #refresh
            self.calc_node_lcs()
            self.populate_table_view(self.activated_models)
            self.populate_elem_table_view(self.activated_models)
            self.plot_activated_models()

    def add_geom_rows(self,rows_to_add=100):
        """
        Add 100 blank rows to geometry table of selected model id
        :return:
        """


        for model_id in self.activated_models:

            #get node index corresponding with existing geomtry table
            model_mask=self.modaldata.tables['geometry'].ix[:,'model_id']==model_id

            if len(self.modaldata.tables['geometry'][model_mask].index)==0:
                ind=0
                node_num=0

            else:
                ind= self.modaldata.tables['geometry'][model_mask].index.max() + 1
                node_num = self.modaldata.tables['geometry'].ix[model_mask,'node_nums'].max() + 1

            node_nums=np.arange(node_num,node_num+rows_to_add)
            node_index=np.arange(ind,ind+rows_to_add)

            #create node data
            df=pd.DataFrame(index=node_index, columns=self.modaldata.tables['geometry'].columns)
            df['model_id']=model_id
            df['node_nums']=node_nums

            rgba_color = pg.colorTuple(QtGui.QColor(0,255,0,255))
            df['clr_r']=rgba_color[0]/ 255.  # rbg values 0-1
            df['clr_g']=rgba_color[1]/ 255.  # rbg values 0-1
            df['clr_b']=rgba_color[2]/ 255.  # rbg values 0-1
            df['clr_a']=rgba_color[3]/ 255.  # alpha values 0-1

            if len(self.modaldata.tables['geometry'].index)==0:
                self.modaldata.tables['geometry']=df
            else:
                #self.modal_data.tables['elements_values'].update(df_elem_nodes)#,overwrite=True)
                self.modaldata.tables['geometry']=pd.concat([self.modaldata.tables['geometry'], df])

            #refresh
            self.populate_table_view(self.activated_models)




    def create_plane_nodes_df(self,plane_orient,len1,len2,div1,div2,start_num,model_id,x_offset,y_offset,z_offset):
        maximum_number_of_nodes=div1*div2
        node_nums=np.arange(start_num,start_num+maximum_number_of_nodes)


        len1_arr = np.linspace(0, len1, div1)
        len2_arr = np.linspace(0, len2, div2)
        if plane_orient=='XY':
            xx, yy = np.meshgrid(len1_arr, len2_arr)
            zz=np.zeros((maximum_number_of_nodes))
        if plane_orient=='YZ':
            yy, zz = np.meshgrid(len1_arr, len2_arr)
            xx=np.zeros((maximum_number_of_nodes))
        if plane_orient=='ZX':
            zz, xx = np.meshgrid(len1_arr, len2_arr)
            yy=np.zeros((maximum_number_of_nodes))

        #realign index in order to prevent double node names (geometry data frame starts with 1 by default)
        #node_index=node_nums-1

        #get node index corresponding with existing geomtry table
        model_mask=self.modaldata.tables['geometry'].ix[:,'model_id']==model_id
        node_mask=self.modaldata.tables['geometry'].ix[:,'node_nums'].isin(node_nums)
        final_mask=model_mask*node_mask
        node_index=self.modaldata.tables['geometry'].ix[final_mask].index

        if len(node_nums)>len(node_index):
            # add rows for selected model
            rows_to_add=len(node_nums)-len(node_index)
            self.add_geom_rows(rows_to_add=rows_to_add)
            # get index
            model_mask=self.modaldata.tables['geometry'].ix[:,'model_id']==model_id
            node_mask=self.modaldata.tables['geometry'].ix[:,'node_nums'].isin(node_nums)
            final_mask=model_mask*node_mask
            node_index=self.modaldata.tables['geometry'].ix[final_mask].index

        #create node data
        df=pd.DataFrame(index=node_index, columns=self.modaldata.tables['geometry'].columns)
        df['model_id']=model_id
        df['node_nums']=node_nums
        df['x']=xx.flatten()+x_offset
        df['y']=yy.flatten()+y_offset
        df['z']=zz.flatten()+z_offset
        df['thx']=0
        df['thy']=0
        df['thz']=0
        rgba_color = pg.colorTuple(QtGui.QColor(0,255,0,255))
        df['clr_r']=rgba_color[0]/ 255.  # rbg values 0-1
        df['clr_g']=rgba_color[1]/ 255.  # rbg values 0-1
        df['clr_b']=rgba_color[2]/ 255.  # rbg values 0-1
        df['clr_a']=rgba_color[3]/ 255.  # alpha values 0-1

        #calculate r,phi from x,y
        df['r'] = np.sqrt(df['x']**2 + df['y']**2)
        df['phi'] = np.arcsin(df['y']/df['r'])*180./np.pi
        df['cyl_thz']= 0

        return df

    def create_plane_elem_df(self,div1,div2,start_num,model_id,custom_num=None):

        #create element data
        #get next pandas index
        if custom_num==None:
            if len(self.modaldata.tables['elements_index'].index)==0:
                ind=0
                elem_node_ind=0
                element_id=0
            else:
                ind= self.modaldata.tables['elements_index'].index.max() + 1
                element_id= self.modaldata.tables['elements_index']['element_id'].max() + 1
                elem_node_ind= self.modaldata.tables['elements_values'].index.max() + 1
        else:
            ind=custom_num['ind']
            element_id=custom_num['element_id']
            elem_node_ind=custom_num['elem_node_ind']

        for model_id_aux, model_obj_aux in self.models.items():
            if model_obj_aux.model_id==model_id:
                color=model_obj_aux.cur_triangle_color
        element_descriptor='triangle'
        nr_of_nodes=3

        tot_num_of_elem=(div1-1)*(div2-1)*2 #total number of elements
        elem_nums=np.arange(ind,ind+tot_num_of_elem)
        elem_ids=np.arange(element_id,element_id+tot_num_of_elem)
        df_elem=pd.DataFrame(index=elem_nums, columns=self.modaldata.tables['elements_index'].columns)
        df_elem['model_id']=model_id
        df_elem['element_id']=elem_ids
        df_elem['element_descriptor']=element_descriptor
        df_elem['color']=color
        df_elem['nr_of_nodes']=nr_of_nodes
        df_elem['clr_r']=color.red()/255.
        df_elem['clr_g']=color.green()/255.
        df_elem['clr_b']=color.blue()/255.
        df_elem['clr_a']=color.alpha()/255.


        #store element nodes

        #walk through nodes and store elements
        pos_1=[]
        pos_2=[]
        pos_3=[]
        node_number=start_num

        k=0
        for i in range(1,int(div2+1)): # len1 division
            for j in range(1,int(div1+1)): # len2 divisions
                if j==div1:
                    #last column
                    pass
                else:
                    if i==(div2): #vertical
                        #last row/last column
                        pass
                    else:
                        pos_1.append(node_number)
                        pos_2.append(node_number+1)
                        pos_3.append(node_number+1+div1)

                        pos_1.append(node_number)
                        pos_2.append(node_number+div1)
                        pos_3.append(node_number+1+div1)

                node_number=node_number+1


        df_elem_index=np.arange(elem_node_ind,elem_node_ind+len(np.tile(elem_ids,3)))
        df_elem_nodes=pd.DataFrame(index=df_elem_index, columns=self.modaldata.tables['elements_values'].columns)
        #df_elem_nodes['model_id']=model_id
        df_elem_nodes['element_id']=np.tile(elem_ids,3)
        df_elem_nodes['node_id']=np.asarray(pos_1+pos_2+pos_3) #node numbers
        df_elem_nodes['node_pos']=np.repeat([1,2,3],len(pos_1)) #node position in element

        return df_elem,df_elem_nodes


    def create_plane_geom(self,plane_data):
        """
        Create cylinder geometry based on user input (for currently active model)
        :return:
        """

        plane_orient=plane_data['plane_orient']
        len1=float(plane_data['len1'])
        len2=float(plane_data['len2'])
        div1=float(plane_data['div1'])
        div2=float(plane_data['div2'])
        x_offset=float(plane_data['x_offset'])
        y_offset=float(plane_data['y_offset'])
        z_offset=float(plane_data['z_offset'])
        start_num=float(plane_data['start_num'])


        for model_id in self.activated_models:

            # get nodes
            df=self.create_plane_nodes_df(plane_orient,len1,len2,div1,div2,start_num,model_id,x_offset,y_offset,z_offset)
            #update geometry table with new data
            self.modaldata.tables['geometry'].update(df)#,overwrite=True)

            # get elements and element connectivity
            df_elem,df_elem_nodes=self.create_plane_elem_df(div1,div2,start_num,model_id)

            # update modal_data object with new geometry
            if len(self.modaldata.tables['elements_index'].index)==0:
                self.modaldata.tables['elements_index']=df_elem
            else:
                 self.modaldata.tables['elements_index']=pd.concat([self.modaldata.tables['elements_index'], df_elem])


            if len(self.modaldata.tables['elements_values'].index)==0:
                self.modaldata.tables['elements_values']=df_elem_nodes
            else:
                self.modaldata.tables['elements_values']=pd.concat([self.modaldata.tables['elements_values'], df_elem_nodes])

            #refresh
            self.calc_node_lcs()
            self.populate_table_view(self.activated_models)
            self.populate_elem_table_view(self.activated_models)
            self.plot_activated_models()

    def create_box_geom(self,box_data):
        """
        Create box geometry based on user input (for currently active model)
        :return:
        """

        lenx=float(box_data['lenx'])
        leny=float(box_data['leny'])
        lenz=float(box_data['lenz'])

        divx=float(box_data['divx'])
        divy=float(box_data['divy'])
        divz=float(box_data['divz'])

        x_offset=float(box_data['x_offset'])
        y_offset=float(box_data['y_offset'])
        z_offset=float(box_data['z_offset'])
        start_num=float(box_data['start_num'])

        for model_id in self.activated_models:
            maximum_number_of_nodes=2*divx*divy+(divz-2)*(divy+(divx-1)+(divy-1)+(divx-2))
            node_nums=np.arange(start_num,start_num+maximum_number_of_nodes)

            # xz plane
            spc_x=np.linspace(0,lenx,divx)
            x_arr_1=np.repeat(spc_x,divz)
            y_arr_1=np.zeros((divx*divz))
            spc_z=np.linspace(0,lenz,divz)
            z_arr_1=np.tile(spc_z[::-1],divx)

            # far side yz plane

            x_arr_2=np.repeat([lenx],divy*divz)
            spc_y=np.linspace(0,leny,divy)
            y_arr_2=np.repeat(spc_y,divz)
            z_arr_2=np.tile(spc_z[::-1],divy)

            # far side xz plane

            spc_x=np.linspace(0,lenx,divx)
            x_arr_3=np.repeat(spc_x[::-1],divz)
            y_arr_3=np.repeat([leny],divx*divz)
            spc_z=np.linspace(0,lenz,divz)
            z_arr_3=np.tile(spc_z[::-1],divx)

            # yz plane

            x_arr_4=np.repeat([0],divy*divz)
            spc_y=np.linspace(0,leny,divy)
            y_arr_4=np.repeat(spc_y[::-1],divz)
            z_arr_4=np.tile(spc_z[::-1],divy)

            # xy plane (top)

            x_arr_5=np.tile(spc_x,divy)
            spc_y=np.linspace(0,leny,divy)
            y_arr_5=np.repeat(spc_y,divx)
            z_arr_5=np.repeat(lenz,divy*divx)

            #remove corner nodes
            x_mask=(x_arr_5!=lenx)*(x_arr_5!=0) # True where x coordinate is not on edge
            y_mask=(y_arr_5!=leny)*(y_arr_5!=0) # True where y coordinate is not on edge
            fin_mask=x_mask*y_mask
            x_arr_5=x_arr_5[fin_mask]
            y_arr_5=y_arr_5[fin_mask]
            z_arr_5=z_arr_5[fin_mask]

            # xy plane (bottom)

            x_arr_6=np.tile(spc_x,divy)
            spc_y=np.linspace(0,leny,divy)
            y_arr_6=np.repeat(spc_y,divx)
            z_arr_6=np.repeat(0,divy*divx)

            #remove corner nodes
            x_mask=(x_arr_6!=lenx)*(x_arr_6!=0) # True where x coordinate is not on edge
            y_mask=(y_arr_6!=leny)*(y_arr_6!=0) # True where y coordinate is not on edge
            fin_mask=x_mask*y_mask
            x_arr_6=x_arr_6[fin_mask]
            y_arr_6=y_arr_6[fin_mask]
            z_arr_6=z_arr_6[fin_mask]

            x_arr=np.concatenate((x_arr_1[:-divz],x_arr_2[:-divz],x_arr_3[:-divz],x_arr_4[:-divz],x_arr_5,x_arr_6))
            y_arr=np.concatenate((y_arr_1[:-divz],y_arr_2[:-divz],y_arr_3[:-divz],y_arr_4[:-divz],y_arr_5,y_arr_6))
            z_arr=np.concatenate((z_arr_1[:-divz],z_arr_2[:-divz],z_arr_3[:-divz],z_arr_4[:-divz],z_arr_5,z_arr_6))

            #realign index in order to prevent double node names (geometry data frame starts with 1 by default)
            #node_index=node_nums-1

            #get node index corresponding with existing geomtry table
            model_mask=self.modaldata.tables['geometry'].ix[:,'model_id']==model_id
            node_mask=self.modaldata.tables['geometry'].ix[:,'node_nums'].isin(node_nums)
            final_mask=model_mask*node_mask
            node_index=self.modaldata.tables['geometry'].ix[final_mask].index

            if len(node_nums)>len(node_index):
                # add rows for selected model
                rows_to_add=len(node_nums)-len(node_index)
                self.add_geom_rows(rows_to_add=rows_to_add)
                # get index
                model_mask=self.modaldata.tables['geometry'].ix[:,'model_id']==model_id
                node_mask=self.modaldata.tables['geometry'].ix[:,'node_nums'].isin(node_nums)
                final_mask=model_mask*node_mask
                node_index=self.modaldata.tables['geometry'].ix[final_mask].index

            #create node data
            df=pd.DataFrame(index=node_index, columns=self.modaldata.tables['geometry'].columns)
            df['model_id']=model_id
            df['node_nums']=node_nums
            df['x']=x_arr+x_offset
            df['y']=y_arr+y_offset
            df['z']=z_arr+z_offset
            df['thx']=0
            df['thy']=0
            df['thz']=0
            rgba_color = pg.colorTuple(QtGui.QColor(0,255,0,255))
            df['clr_r']=rgba_color[0]/ 255.  # rbg values 0-1
            df['clr_g']=rgba_color[1]/ 255.  # rbg values 0-1
            df['clr_b']=rgba_color[2]/ 255.  # rbg values 0-1
            df['clr_a']=rgba_color[3]/ 255.  # alpha values 0-1

            #calculate r,phi from x,y
            df['r'] = np.sqrt(df['x']**2 + df['y']**2)
            df['phi'] = np.arcsin(df['y']/df['r'])*180./np.pi
            df['cyl_thz']= 0

            #update geometry table with new data
            self.modaldata.tables['geometry'].update(df)#,overwrite=True)
            #self.modal_data.tables['geometry']=pd.concat([self.modal_data.tables['geometry'],df])
            #
            #create element data
            #get next pandas index
            if len(self.modaldata.tables['elements_index'].index)==0:
                ind=0
                elem_node_ind=0
                element_id=0
            else:
                ind= self.modaldata.tables['elements_index'].index.max() + 1
                element_id= self.modaldata.tables['elements_index']['element_id'].max() + 1
                elem_node_ind= self.modaldata.tables['elements_values'].index.max() + 1

            for model_id_aux, model_obj_aux in self.models.items():
                if model_obj_aux.model_id==model_id:
                    color=model_obj_aux.cur_triangle_color
            element_descriptor='triangle'
            nr_of_nodes=3

            tot_num_of_elem=4*(divx-1)*(divz-1)+4*(divy-1)*(divz-1)+4*(divy-1)*(divx-1) #total number of elements
            elem_nums=np.arange(ind,ind+tot_num_of_elem)
            elem_ids=np.arange(element_id,element_id+tot_num_of_elem)
            df_elem=pd.DataFrame(index=elem_nums, columns=self.modaldata.tables['elements_index'].columns)
            df_elem['model_id']=model_id
            df_elem['element_id']=elem_ids
            df_elem['element_descriptor']=element_descriptor
            df_elem['color']=color
            df_elem['nr_of_nodes']=nr_of_nodes
            df_elem['clr_r']=color.red()/255.
            df_elem['clr_g']=color.green()/255.
            df_elem['clr_b']=color.blue()/255.
            df_elem['clr_a']=color.alpha()/255.

            if len(self.modaldata.tables['elements_index'].index)==0:
                self.modaldata.tables['elements_index']=df_elem
            else:
                #self.modal_data.tables['elements_index'].update(df_elem)#,overwrite=True)
                self.modaldata.tables['elements_index']=pd.concat([self.modaldata.tables['elements_index'], df_elem])

            #store nodes

            #walk through nodes and store elements
            pos_1=[]
            pos_2=[]
            pos_3=[]
            node_number=start_num

            num_of_divs=int(2*divx+2*(divy-2)) # number of verticals along z
            k=0
            for i in range(1,num_of_divs+1):
                for j in range(1,int(divz+1)):

                    if i==num_of_divs:
                        #last vertical line - elements have nodes also from first vertical line
                        if j==(divz):
                            #last row
                            pass
                        else:
                            pos_1.append(node_number)
                            pos_2.append(node_number+1)
                            pos_3.append(start_num+k+1)

                            pos_1.append(node_number)
                            pos_2.append(start_num+k)
                            pos_3.append(start_num+k+1)
                        k=k+1
                    else:
                        if j==(divz): #vertical
                            #last row/last column
                            pass
                        else:
                            pos_1.append(node_number)
                            pos_2.append(node_number+1)
                            pos_3.append(node_number+1+divz)

                            pos_1.append(node_number)
                            pos_2.append(node_number+divz)
                            pos_3.append(node_number+1+divz)

                    node_number=node_number+1



            def get_nnum(x,y,z):
                # get node number based on known location
                x_mask = x_arr == x
                y_mask = y_arr == y
                z_mask = z_arr == z
                fin_mask=x_mask*y_mask*z_mask
                nnum=node_nums[fin_mask]
                return nnum

            x_cord=np.linspace(0,lenx,divx)
            y_cord=np.linspace(0,leny,divy)

            # Top plane
            z_cord=lenz
            for i in range(0,int(divy-1)):
                for j in range(0,int(divx-1)):


                    pos_1.append(get_nnum(x_cord[j],y_cord[i],z_cord))
                    pos_2.append(get_nnum(x_cord[j+1],y_cord[i],z_cord))
                    pos_3.append(get_nnum(x_cord[j+1],y_cord[i+1],z_cord))

                    pos_1.append(get_nnum(x_cord[j],y_cord[i],z_cord))
                    pos_2.append(get_nnum(x_cord[j],y_cord[i+1],z_cord))
                    pos_3.append(get_nnum(x_cord[j+1],y_cord[i+1],z_cord))

            # Bottom plane
            z_cord=0
            for i in range(0,int(divy-1)):
                for j in range(0,int(divx-1)):


                    pos_1.append(get_nnum(x_cord[j],y_cord[i],z_cord))
                    pos_2.append(get_nnum(x_cord[j+1],y_cord[i],z_cord))
                    pos_3.append(get_nnum(x_cord[j+1],y_cord[i+1],z_cord))

                    pos_1.append(get_nnum(x_cord[j],y_cord[i],z_cord))
                    pos_2.append(get_nnum(x_cord[j],y_cord[i+1],z_cord))
                    pos_3.append(get_nnum(x_cord[j+1],y_cord[i+1],z_cord))

            df_elem_index=np.arange(elem_node_ind,elem_node_ind+len(np.tile(elem_ids,3)))
            df_elem_nodes=pd.DataFrame(index=df_elem_index, columns=self.modaldata.tables['elements_values'].columns)
            df_elem_nodes['element_id']=np.tile(elem_ids,3)
            df_elem_nodes['node_id']=np.asarray(pos_1+pos_2+pos_3) #node numbers
            df_elem_nodes['node_pos']=np.repeat([1,2,3],len(pos_1)) #node position in element

            if len(self.modaldata.tables['elements_values'].index)==0:
                self.modaldata.tables['elements_values']=df_elem_nodes
            else:
                #self.modal_data.tables['elements_values'].update(df_elem_nodes)#,overwrite=True)
                self.modaldata.tables['elements_values']=pd.concat([self.modaldata.tables['elements_values'], df_elem_nodes])

            #refresh
            self.calc_node_lcs()
            self.populate_table_view(self.activated_models)
            self.populate_elem_table_view(self.activated_models)
            self.plot_activated_models()



    def create_cyl_geom(self,cylinder_data):
        """
        Create cylinder geometry based on user input (for currently active model)
        :return:
        """
        cyl_r=float(cylinder_data['radius'])
        cyl_h=float(cylinder_data['height'])
        start_num=cylinder_data['start_num']
        num_orient=cylinder_data['num_orient']
        z_offset=cylinder_data['z_offset']
        height_div=float(cylinder_data['height_div'])
        circ_div=float(cylinder_data['circ_div'])

        for model_id in self.activated_models:

            maximum_number_of_nodes=height_div*circ_div
            node_nums=np.arange(start_num,start_num+maximum_number_of_nodes)

            cyl_r_array=np.repeat(cyl_r,maximum_number_of_nodes)

            phi_div=360./circ_div
            cyl_phi_single_row=np.arange(0,360.,phi_div)
            if num_orient=='Vertical':
                cyl_phi_array=np.repeat(cyl_phi_single_row,height_div) # VERTICAL NUMBERING
            else:
                cyl_phi_array=np.tile(cyl_phi_single_row,height_div) # HORIZONTAL NUMBERING


            ##bottom->up numbering
            #cyl_z_array_single_row=np.arange(0,cyl_h+z_div,z_div)

            #top->down numbering
            cyl_z_array_single_row=np.linspace(0,cyl_h,height_div)
            cyl_z_array_single_row=cyl_z_array_single_row[::-1]
            if num_orient=='Vertical':
                cyl_z_array=np.tile(cyl_z_array_single_row,circ_div) # VERTICAL NUMBERING
            else:
                cyl_z_array=np.repeat(cyl_z_array_single_row,circ_div) # HORIZONTAL NUMBERING

            #realign index in order to prevent double node names (geometry data frame starts with 1 by default)
            #node_index=node_nums-1

            #get node index corresponding with existing geomtry table
            model_mask=self.modaldata.tables['geometry'].ix[:,'model_id']==model_id
            node_mask=self.modaldata.tables['geometry'].ix[:,'node_nums'].isin(node_nums)
            final_mask=model_mask*node_mask
            node_index=self.modaldata.tables['geometry'].ix[final_mask].index

            if len(node_nums)>len(node_index):
                # add rows for selected model
                rows_to_add=len(node_nums)-len(node_index)
                self.add_geom_rows(rows_to_add=rows_to_add)
                # get index
                model_mask=self.modaldata.tables['geometry'].ix[:,'model_id']==model_id
                node_mask=self.modaldata.tables['geometry'].ix[:,'node_nums'].isin(node_nums)
                final_mask=model_mask*node_mask
                node_index=self.modaldata.tables['geometry'].ix[final_mask].index

            #create node data
            df=pd.DataFrame(index=node_index, columns=self.modaldata.tables['geometry'].columns)
            df['model_id']=model_id
            df['node_nums']=node_nums
            df['r']=cyl_r_array
            df['phi']=cyl_phi_array
            df['z']=cyl_z_array+z_offset
            df['thx']=0
            df['thy']=0
            df['cyl_thz']=0
            rgba_color = pg.colorTuple(QtGui.QColor(0,255,0,255))
            df['clr_r']=rgba_color[0]/ 255.  # rbg values 0-1
            df['clr_g']=rgba_color[1]/ 255.  # rbg values 0-1
            df['clr_b']=rgba_color[2]/ 255.  # rbg values 0-1
            df['clr_a']=rgba_color[3]/ 255.  # alpha values 0-1

            #calculate x,y from r,phi
            df['x'] = df['r'] * np.cos(df['phi'].astype(np.float64)*np.pi/180)
            df['y'] = df['r'] * np.sin(df['phi'].astype(np.float64)*np.pi/180)
            df['thz']= df['cyl_thz'] + df['phi']

            #update geometry table with new data
            self.modaldata.tables['geometry'].update(df)#,overwrite=True)
            #self.modaldata.tables['geometry']=pd.concat([self.modaldata.tables['geometry'],df])

            #create element data
            #get next pandas index
            if len(self.modaldata.tables['elements_index'].index)==0:
                ind=0
                elem_node_ind=0
                element_id=0
            else:
                ind= self.modaldata.tables['elements_index'].index.max() + 1
                element_id= self.modaldata.tables['elements_index']['element_id'].max() + 1
                elem_node_ind= self.modaldata.tables['elements_values'].index.max() + 1

            for model_id_aux, model_obj_aux in self.models.items():
                if model_obj_aux.model_id==model_id:
                    color=model_obj_aux.cur_triangle_color
            element_descriptor='triangle'
            nr_of_nodes=3

            tot_num_of_elem=circ_div*(height_div-1)*2 #total number of elements
            elem_nums=np.arange(ind,ind+tot_num_of_elem)
            elem_ids=np.arange(element_id,element_id+tot_num_of_elem)
            df_elem=pd.DataFrame(index=elem_nums, columns=self.modaldata.tables['elements_index'].columns)
            df_elem['model_id']=model_id
            df_elem['element_id']=elem_ids
            df_elem['element_descriptor']=element_descriptor
            df_elem['color']=color
            df_elem['nr_of_nodes']=nr_of_nodes
            df_elem['clr_r']=color.red()/255.
            df_elem['clr_g']=color.green()/255.
            df_elem['clr_b']=color.blue()/255.
            df_elem['clr_a']=color.alpha()/255.

            if len(self.modaldata.tables['elements_index'].index)==0:
                self.modaldata.tables['elements_index']=df_elem
            else:
                #self.modal_data.tables['elements_index'].update(df_elem)#,overwrite=True)
                self.modaldata.tables['elements_index']=pd.concat([self.modaldata.tables['elements_index'], df_elem])

            #store nodes

            #tot_elem_nums=circ_div*(height_div-1)*2 #total number of  elements
            #elem_nums=np.arange(element_id,element_id+tot_elem_nums+1)

            #walk through nodes and store elements
            pos_1=[]
            pos_2=[]
            pos_3=[]
            node_number=start_num

            if num_orient=='Vertical':
                k=0
                for i in range(1,int(circ_div+1)): # circumference division
                    for j in range(1,int(height_div+1)): # height divisions
                        if i==circ_div:
                            #last circumference division - elements have nodes also from first division
                            if j==(height_div):
                                #last row
                                pass
                            else:
                                pos_1.append(node_number)
                                pos_2.append(node_number+1)
                                pos_3.append(start_num+k+1)

                                pos_1.append(node_number)
                                pos_2.append(start_num+k)
                                pos_3.append(start_num+k+1)
                            k=k+1
                        else:
                            if j==(height_div): #vertical
                                #last row/last column
                                pass
                            else:
                                pos_1.append(node_number)
                                pos_2.append(node_number+1)
                                pos_3.append(node_number+1+height_div)

                                pos_1.append(node_number)
                                pos_2.append(node_number+height_div)
                                pos_3.append(node_number+1+height_div)

                        node_number=node_number+1
            else:
                k=0
                for i in range(1,int(height_div+1)): # height division
                    for j in range(1,int(circ_div+1)): # circumference divisions
                        if j==circ_div:
                            #last circumference division - elements have nodes also from first division
                            if i==(height_div):
                                #last row
                                pass
                            else:
                                pos_1.append((start_num-1)+i*circ_div) # 4, 8
                                pos_2.append(start_num+k*circ_div) # 1, 5
                                pos_3.append(start_num+i*circ_div) # 5, 9

                                pos_1.append((start_num-1)+i*circ_div) # 4, 8
                                pos_2.append((start_num-1)+(i+1)*circ_div) # 8, 12
                                pos_3.append(start_num+i*circ_div) # 5, 9
                            k=k+1
                        else:
                            if i==(height_div):
                                #last row
                                pass
                            else:
                                pos_1.append(node_number) # 1,2
                                pos_2.append(node_number+1) # 2,3
                                pos_3.append(node_number+circ_div) # 5,6

                                pos_1.append(node_number+1) # 1, 2
                                pos_2.append(node_number+circ_div) # 5, 6
                                pos_3.append(node_number+1+circ_div) # 6, 7
                        node_number=node_number+1

            df_elem_index=np.arange(elem_node_ind,elem_node_ind+len(np.tile(elem_ids,3)))
            df_elem_nodes=pd.DataFrame(index=df_elem_index, columns=self.modaldata.tables['elements_values'].columns)
            #df_elem_nodes['model_id']=model_id
            df_elem_nodes['element_id']=np.tile(elem_ids,3)
            df_elem_nodes['node_id']=np.asarray(pos_1+pos_2+pos_3) #node numbers
            df_elem_nodes['node_pos']=np.repeat([1,2,3],len(pos_1)) #node position in element

            if len(self.modaldata.tables['elements_values'].index)==0:
                self.modaldata.tables['elements_values']=df_elem_nodes
            else:
                #self.modal_data.tables['elements_values'].update(df_elem_nodes)#,overwrite=True)
                self.modaldata.tables['elements_values']=pd.concat([self.modaldata.tables['elements_values'], df_elem_nodes])

            #refresh
            self.calc_node_lcs()
            self.populate_table_view(self.activated_models)
            self.populate_elem_table_view(self.activated_models)
            self.plot_activated_models()



    def new_model(self,description=None):
        """
        Open dialogue for new model creation
        :param description:
        :return:
        """


        response,model_name=dialog_new_model.return_data()

        if response==1:


            #check for available model_ids
            current_model_ids=self.modaldata.tables['info']['model_id'].values

            # increment model_id
            if len(current_model_ids)==0:
                model_id=0
            else:
                model_id=np.max(np.unique(current_model_ids))+1

            fields = {'db_app': 'ModalData', 'time_db_created': time.strftime("%d-%b-%y %H:%M:%S"),
                      'time_db_saved': time.strftime("%d-%b-%y %H:%M:%S"), 'program': 'modaldata.py',
                      'model_name': model_name, 'description': description, 'units_code': 9,
                      'temp': 1.0, 'temp_mode': 1, 'temp_offset': 1.0, 'length': 1.0, 'force': 1.0,
                      'units_description': 'User unit system'}

            self.modaldata.new_model(model_id, entries=fields)
            self.build_geometry([model_id])

            #select new model
            #self.modaldata.current_model_id=model_id
            self.preferences['selected_model_id']=model_id

            # open new model dialog
            self.build_uff_tree(self.modaldata,refresh=True)

    def rename_model(self):
        """
        Open dialogue for new model creation
        :param description:
        :return:
        """

        response,model_name=dialog_rename_model.return_data()

        if response==1:
            mask=self.modaldata.tables['info']['model_id']==self.sending_button.model_id
            #change model name in modaldata object
            self.modaldata.tables['info']['model_name'][mask]=model_name
            self.sending_button.setText(model_name+ ' ' + str(self.sending_button.model_id))


    def delete_model_dialog(self):
        """
        Delete model from modal data object
        :param model_id:
        :return:
        """

        response=dialog_delete_model.return_data()

        if response==1:
            self.delete_model()


    def build_geometry(self,model_id_list):

        #generate space for 1000 nodes for new models
        for model_id in model_id_list:
            if self.modaldata.tables['geometry'][self.modaldata.tables['geometry']['model_id'] == model_id].empty:
                maximum_number_of_nodes=100
                node_nums=np.arange(1,maximum_number_of_nodes+1)
                #create data
                df=pd.DataFrame(index=node_nums, columns=self.modaldata.tables['geometry'].columns)
                df['model_id']=model_id
                df['node_nums']=node_nums

                rgba_color = pg.colorTuple(QtGui.QColor(0,255,0,255))
                df['clr_r']=rgba_color[0]/ 255.  # rbg values 0-1
                df['clr_g']=rgba_color[1]/ 255.  # rbg values 0-1
                df['clr_b']=rgba_color[2]/ 255.  # rbg values 0-1
                df['clr_a']=rgba_color[3]/ 255.  # alpha values 0-1
                #create empty rows in geometry
                self.modaldata.tables['geometry']=self.modaldata.tables['geometry'].append(df, ignore_index=True)



    def populate_table_view(self,model_id_list):

        #generate nodes if geometry is empty
        self.build_geometry(model_id_list)

        #cartesian gcs
        self.geom_table_model.update(self.modaldata.tables['geometry'], model_id_list, self.fields)

        #cylindrical csys
        self.cyl_geom_table_model.update(self.modaldata.tables['geometry'], model_id_list, self.cyl_fields)


    def populate_elem_table_view(self,model_id_list):
        self.elem_table_model.update(self.modaldata.tables['elements_index'], model_id_list, self.elem_fields)


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


            self.activated_models=[]

            for model_id, model_obj in self.models.items():
                if model_obj.activated:
                    self.activated_models.append(int(model_obj.model_id))

            self.populate_table_view(self.activated_models)
            self.populate_elem_table_view(self.activated_models)

            #currently selected model_id
            self.preferences['selected_model_id']=inp_model_id

            self.plot_activated_models()

        params = []

        if refresh==False:
            #reload was called, drop previous models
            print('Clearing previous models')
            self.delete_model(delete_all=True)

        uff_tree_index = 0
        #for i in range(len(available_model_ids)):
        for index, row in self.modaldata.tables['info'].iterrows():
            value = index
            #model_id=int(available_model_ids[i])
            model_id = row['model_id']
            model_name = row['model_name'] + ' ' + str(model_id)
            description = row['description']
            units_code = row['units_code']

            if model_id in self.models.keys():
                print('model %f already stored - skipping' % model_id)

            else:
                print('Storing model id:',model_id)
                self.models[model_id] = Model(model_id, model_name, modal_data, None, self.model_view,
                                              None, None, uff_tree_index,None)


                button=QtWidgets.QPushButton(qta.icon('fa.database', color='white'),str(model_name), self)
                button.setObjectName('medium')
                button.setCheckable(True)
                button.clicked.connect(partial(on_activate, model_id))
                button.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
                button.customContextMenuRequested.connect(self.model_btn_context_menu)
                button.model_name=model_name
                button.model_id=model_id
                button.show()
                self.model_buttons[int(model_id)]=button

        #deactivate all models and model buttons
        self.deactivate_all()

        #activate first model automatically
        #TODO: implement 'current and previously selected models'

        try:
            on_activate(self.preferences['selected_model_id'])

        except:
            try:
                #if current model_id was not yet set
                keys=list(self.models.keys())
                on_activate(self.models[keys[0]].model_id)
            except:
                print('There is no model to show.')


    def build_uff_tree_OLD(self, modal_data):
        """
        Check available data in uff and load it into data tree widget

        :param modal_data:
        :return:
        """
        #TODO: localization via python gettext

        params = []

        uff_tree_index = 0
        #for i in range(len(available_model_ids)):
        for index, row in self.modaldata.tables['info'].iterrows():
            value = index
            #model_id=int(available_model_ids[i])
            model_id = row['model_id']
            model_name = row['model_name'] + ' ' + str(model_id)
            description = row['description']
            units_code = row['units_code']

            if model_id in self.models.keys():
                print('model %f already stored - skipping' % model_id)
            else:
                self.models[model_id] = Model(model_id, model_name, modal_data, None, self.model_view,
                                              None, None, uff_tree_index)

            params.append({'name': model_name, 'type': 'group', 'extra': 6, 'children': [
                {'name': 'Activate:', 'type': 'bool', 'value': False, 'tip': "Click to activate model",
                 'model': model_id},
                {'name': 'Model name:', 'type': 'str', 'value': str(model_id), 'tip': "Click to change model name",
                 'model': model_id},
                {'name': 'Analysis data available:', 'type': 'str',
                 'value': not self.modaldata.tables['analysis_index'][
                     self.modaldata.tables['analysis_index']['model_id'] == model_id].empty,
                 'tip': "Indicates if processed modes are available", 'model': model_id},
                {'name': 'Measurement data available:', 'type': 'str',
                 'value': not self.modaldata.tables['measurement_index'][
                     self.modaldata.tables['measurement_index']['model_id'] == model_id].empty,
                 'tip': "Indicates if measurement data is available", 'model': model_id},
            ]})

            #TODO: coordinate system selection (cartesian, cylindrical, ...)
            if not self.modaldata.tables['geometry'][self.modaldata.tables['geometry']['model_id'] == model_id].empty:
                params[value]['children'].append(
                    {'name': 'View settings', 'type': 'group', 'expanded': False, 'children': [
                        {'name': 'Cube scale:', 'type': 'float', 'value': 0.01, 'model': model_id},
                        {'name': 'Node color:', 'type': 'color', 'value': "00FF00", 'model': model_id},
                        {'name': 'Element color:', 'type': 'color', 'value': "0000FF", 'model': model_id},
                        {'name': 'Units code:', 'type': 'int', 'value': units_code, 'model': model_id},
                        {'name': 'Description:', 'type': 'str', 'value': description, 'model': model_id},
                        {'name': 'Offset x:', 'type': 'float', 'value': 0, 'model': model_id},
                        {'name': 'Offset y:', 'type': 'float', 'value': 0, 'model': model_id},
                        {'name': 'Offset z:', 'type': 'float', 'value': 0, 'model': model_id},
                    ]})
            if not self.modaldata.tables['info'][self.modaldata.tables['info']['model_id'] == model_id].empty:
                params[value]['children'].append({'name': 'Info', 'type': 'group', 'expanded': False, 'children': [
                    {'name': 'Model name:', 'type': 'str', 'value': model_name},
                    #{'name': 'Date created:', 'type': 'str', 'value': info_data.ix[model_id].ix['date_db_created'].value},
                ]})
            uff_tree_index = uff_tree_index + 1

        ## Create tree of Parameter objects
        self.tree_params = Parameter.create(name='params', type='group', children=params)

        ## If anything changes in the tree, print a message
        def change(param, changes):

            for param, change, data in changes:

                if param.name() == 'Activate:' and change == 'value':
                    model_id = param.opts['model']
                    self.models[model_id].activated = data

                    activated_models=[]
                    for model_id, model_obj in self.models.items():
                        if model_obj.activated:
                            activated_models.append(int(model_obj.model_id))

                    self.populate_table_view(activated_models)
                    self.populate_elem_table_view(activated_models)

                if param.name() == 'Offset x:' and change == 'value':
                    model_id = param.opts['model']
                    self.models[model_id].offset['x'] = data

                if param.name() == 'Offset y:' and change == 'value':
                    model_id = param.opts['model']
                    self.models[model_id].offset['y'] = data

                if param.name() == 'Offset z:' and change == 'value':
                    model_id = param.opts['model']
                    self.models[model_id].offset['z'] = data

                if param.name() == 'Node color:' and change == 'value':
                    model_id = param.opts['model']
                    self.models[model_id].set_node_color(data)

                if param.name() == 'Element color:' and change == 'value':
                    model_id = param.opts['model']
                    self.models[model_id].set_elem_color(data)

                if param.name() == 'Cube scale:' and change == 'value':
                    model_id = param.opts['model']
                    self.activated_models[model_id]['needs_refresh'] = True

            self.plot_activated_models()

        #empty out table when new model is created
        self.populate_table_view([])

        self.tree_params.sigTreeStateChanged.connect(change)
        self.t.setParameters(self.tree_params, showTop=False)

    def geometry_changed(self):
        """
        Method called when data in geometry table changes
        :return:
        """

        if self.gcs_type==1:
            #calculate x,y from r,phi
            nan_mask = self.modaldata.tables['geometry'][['node_nums', 'r', 'phi', 'z', 'cyl_thz', 'thy', 'thx' , 'model_id']].notnull().all(axis=1)
            self.modaldata.tables['geometry'].ix[nan_mask, 'x']= \
                self.modaldata.tables['geometry'].ix[nan_mask, 'r'] * \
                np.cos(self.modaldata.tables['geometry'].ix[nan_mask, 'phi'].astype(np.float64) * np.pi / 180)
            self.modaldata.tables['geometry'].ix[nan_mask, 'y']= \
                self.modaldata.tables['geometry'].ix[nan_mask, 'r'] * \
                np.sin(self.modaldata.tables['geometry'].ix[nan_mask, 'phi'].astype(np.float64) * np.pi / 180)
            self.modaldata.tables['geometry'].ix[nan_mask, 'thz']= \
                self.modaldata.tables['geometry'].ix[nan_mask, 'cyl_thz'] + \
                self.modaldata.tables['geometry'].ix[nan_mask, 'phi']

        if self.gcs_type==0:
            #calculate r,phi from x,y
            nan_mask = self.modaldata.tables['geometry'][['node_nums', 'x', 'y', 'z', 'thz', 'thy', 'thx', 'model_id']].notnull().all(axis=1)
            self.modaldata.tables['geometry'].ix[nan_mask, 'r']=\
                np.sqrt((self.modaldata.tables['geometry'].ix[nan_mask, 'x'] ** 2 +
                         self.modaldata.tables['geometry'].ix[nan_mask, 'y'] ** 2).astype(np.float64))
            self.modaldata.tables['geometry'].ix[nan_mask, 'phi']=\
                np.arcsin((self.modaldata.tables['geometry'].ix[nan_mask, 'y'].astype(np.float64) /
                           self.modaldata.tables['geometry'].ix[nan_mask, 'r'].astype(np.float64)))

            #change NaNs to zero due to division with zeros
            # this is also necessary so that cyl_thz is changed to 0 for later subtraction
            aux_df=self.modaldata.tables['geometry'].ix[nan_mask,['r','phi','cyl_thz']]
            aux_df.fillna(0,inplace=True)
            self.modaldata.tables['geometry'].update(aux_df, overwrite=False)

            self.modaldata.tables['geometry'].ix[nan_mask, 'cyl_thz']= \
                self.modaldata.tables['geometry'].ix[nan_mask, 'thz'] - \
                self.modaldata.tables['geometry'].ix[nan_mask, 'phi']

        self.calc_node_lcs()
        self.plot_activated_models()


    def clear_all_views(self):
        '''
        Clear everything on 3D and 2D view
        :return:
        '''

        # clear 3D view
        self.model_view.items.clear()
        self.model_view.updateGL()


    def reload(self, refresh=False):
        """Update interface -- read modaldata object again.
        Added by Matjaz!
        """

        #Calculate local coordinate systems and add them to 'geometry' table
        if self.modaldata.tables['info'].empty:

            self.status_bar.setBusy('geometry', 'Modal data object empty! (info table)')
        else:
            #self.calc_node_lcs()
            self.clear_all_views()
            self.build_uff_tree(self.modaldata,refresh=refresh)
            self.status_bar.setNotBusy('geometry')


    def refresh(self):
        '''Is called on tab-change (subwidget change) and on preferences change.'''
        self.reload(refresh=True)


class dialog_new_model(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(dialog_new_model, self).__init__(parent)
        self.setWindowTitle('Create new model')

        with open('gui/styles/style_template.css', 'r', encoding='utf-8') as fh:
            src = Template(fh.read())
            src = src.substitute(COLOR_PALETTE)
            self.setStyleSheet(src)

        # Create widgets
        self.model_name = QtWidgets.QLineEdit("Enter model name")
        self.button = QtWidgets.QPushButton("Done")
        self.button.setObjectName('small')

        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.setObjectName('small')

        # Create layout and add widgets
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.model_name)
        button_layout= QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Set dialog layout
        self.setLayout(layout)
        self.button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    @staticmethod
    def return_data(parent = None):
        dialog = dialog_new_model(parent)
        result = dialog.exec_()
        model_name=dialog.model_name.text()
        return (result,model_name)

class dialog_rename_model(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(dialog_new_model, self).__init__(parent)
        self.setWindowTitle('Rename model')

        with open('gui/styles/style_template.css', 'r', encoding='utf-8') as fh:
            src = Template(fh.read())
            src = src.substitute(COLOR_PALETTE)
            self.setStyleSheet(src)

        # Create widgets
        self.model_name = QtWidgets.QLineEdit("Enter new model name")
        self.button = QtWidgets.QPushButton("Done")
        self.button.setObjectName('small')

        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.setObjectName('small')

        # Create layout and add widgets
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.model_name)
        button_layout= QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        # Set dialog layout
        self.setLayout(layout)
        self.button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    @staticmethod
    def return_data(parent = None):
        dialog = dialog_new_model(parent)
        result = dialog.exec_()
        model_name=dialog.model_name.text()
        return (result,model_name)


class dialog_delete_model(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(dialog_delete_model, self).__init__(parent)
        self.setWindowTitle('Delete model')
        with open('gui/styles/style_template.css', 'r', encoding='utf-8') as fh:
            src = Template(fh.read())
            src = src.substitute(COLOR_PALETTE)
            self.setStyleSheet(src)

        # Create widgets
        self.question = QtWidgets.QLabel("Are you sure you want to delete current model?")
        self.delete_button = QtWidgets.QPushButton("Yes")
        self.delete_button.setObjectName('small')
        self.cancel_button = QtWidgets.QPushButton("No")
        self.cancel_button.setObjectName('small')

        # Create layout and add widgets
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.question)
        button_layout= QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.delete_button)
        layout.addLayout(button_layout)

        # Set dialog layout
        self.setLayout(layout)
        self.delete_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    @staticmethod
    def return_data(parent = None):
        dialog = dialog_delete_model(parent)
        result = dialog.exec_()
        return (result)

class dialog_geom_primitives(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(dialog_geom_primitives, self).__init__(parent)
        self.leftlist = QtWidgets.QListWidget ()
        self.leftlist.insertItem (0, 'Line' )
        self.leftlist.insertItem (1, 'Plane' )
        self.leftlist.insertItem (2, 'Box' )
        self.leftlist.insertItem (3, 'Cylinder' )

        self.stack1 = QtWidgets.QWidget()
        self.stack2 = QtWidgets.QWidget()
        self.stack3 = QtWidgets.QWidget()
        self.stack4 = QtWidgets.QWidget()

        self.stack1UI()
        self.stack2UI()
        self.stack3UI()
        self.stack4UI()

        self.Stack = QtWidgets.QStackedWidget(self)
        self.Stack.addWidget(self.stack1)
        self.Stack.addWidget(self.stack2)
        self.Stack.addWidget(self.stack3)
        self.Stack.addWidget(self.stack4)

        with open('gui/styles/style_template.css', 'r', encoding='utf-8') as fh:
            src = Template(fh.read())
            src = src.substitute(COLOR_PALETTE)
            self.setStyleSheet(src)

        base_layout = QtWidgets.QVBoxLayout(self)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.leftlist)
        layout.addWidget(self.Stack)

        base_layout.addLayout(layout)

        self.ok_button = QtWidgets.QPushButton("Ok")
        self.ok_button.setObjectName('small')
        self.cancel_button = QtWidgets.QPushButton("Cancel")
        self.cancel_button.setObjectName('small')
        button_layout= QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        base_layout.addLayout(button_layout)
        # Set dialog layout
        self.setLayout(layout)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self.leftlist.currentRowChanged.connect(self.display)
        self.setGeometry(300, 200, 100,100)
        self.setWindowTitle('Create geometry')

        #set default selection
        self.Stack.setCurrentIndex(0)
        self.leftlist.setCurrentItem(self.leftlist.item(0))
        self.show()

    def stack1UI(self):
        """
        Input data for creating line
        :return:
        """

        self.line_title = QtWidgets.QLabel("Create line")

        self.line_label_s = QtWidgets.QLabel("Start point coordinates: [m]")
        self.line_xs_str = QtWidgets.QLabel("X")
        self.line_xs_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.line_xs = QtWidgets.QDoubleSpinBox(self)
        self.line_xs.setRange(-100000,100000)

        self.line_ys_str = QtWidgets.QLabel("Y")
        self.line_ys_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.line_ys = QtWidgets.QDoubleSpinBox(self)
        self.line_ys.setRange(-100000,100000)

        self.line_zs_str = QtWidgets.QLabel("Z")
        self.line_zs_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.line_zs = QtWidgets.QDoubleSpinBox(self)
        self.line_zs.setRange(-100000,100000)

        self.line_label_e = QtWidgets.QLabel("End point coordinates: [m]")
        self.line_xe_str = QtWidgets.QLabel("X")
        self.line_xe_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.line_xe = QtWidgets.QDoubleSpinBox(self)
        self.line_xe.setRange(-100000,100000)
        self.line_xe.setValue(1)

        self.line_ye_str = QtWidgets.QLabel("Y")
        self.line_ye_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.line_ye = QtWidgets.QDoubleSpinBox(self)
        self.line_ye.setRange(-100000,100000)
        self.line_ye.setValue(0)

        self.line_ze_str = QtWidgets.QLabel("Z")
        self.line_ze_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.line_ze = QtWidgets.QDoubleSpinBox(self)
        self.line_ze.setRange(-100000,100000)
        self.line_ze.setValue(0)

        self.line_start_num_str = QtWidgets.QLabel("Start number:")
        self.line_start_num = QtWidgets.QDoubleSpinBox(self)
        self.line_start_num.setDecimals(0)
        self.line_start_num.setRange(1,100000)

        self.line_div_str = QtWidgets.QLabel("Number of points:")
        self.line_div = QtWidgets.QDoubleSpinBox(self)
        self.line_div.setDecimals(0)
        self.line_div.setRange(2,1000)

        left=0
        top=0
        first_top=0 #first widget from top
        right=0
        bottom=20

        # Create layout and add widgets
        main_layout = QtWidgets.QVBoxLayout()

        layout = QtWidgets.QGridLayout()
        layout.setContentsMargins(left, first_top, right, bottom)
        layout.addWidget(self.line_label_s,0,1)
        layout.addWidget(self.line_xs_str,1,0)
        layout.addWidget(self.line_ys_str,1,1)
        layout.addWidget(self.line_zs_str,1,2)
        layout.addWidget(self.line_xs,2,0)
        layout.addWidget(self.line_ys,2,1)
        layout.addWidget(self.line_zs,2,2)

        layout2 = QtWidgets.QGridLayout()
        layout2.setContentsMargins(left, top, right, bottom)
        layout2.addWidget(self.line_label_e,0,1)
        layout2.addWidget(self.line_xe_str,1,0)
        layout2.addWidget(self.line_ye_str,1,1)
        layout2.addWidget(self.line_ze_str,1,2)
        layout2.addWidget(self.line_xe,2,0)
        layout2.addWidget(self.line_ye,2,1)
        layout2.addWidget(self.line_ze,2,2)

        main_layout.addLayout(layout)
        main_layout.addLayout(layout2)
        main_layout.addWidget(self.line_start_num_str)
        main_layout.addWidget(self.line_start_num)
        main_layout.addWidget(self.line_div_str)
        main_layout.addWidget(self.line_div)
        main_layout.addStretch()

        self.stack1.setLayout(main_layout)

    def stack2UI(self):
        """
        Input data for creating plane
        :return:
        """
        self.plane_title = QtWidgets.QLabel("Create plane")
        self.plane_orient_str= QtWidgets.QLabel("Plane orientation:")
        self._r_plane_group=QtWidgets.QButtonGroup(self) # Number group
        self._r_plane_xy=QtWidgets.QRadioButton("XY")
        self._r_plane_xy.setChecked(True)
        self._r_plane_group.addButton(self._r_plane_xy)

        self._r_plane_yz=QtWidgets.QRadioButton("YZ")
        self._r_plane_group.addButton(self._r_plane_yz)

        self._r_plane_zx=QtWidgets.QRadioButton("ZX")
        self._r_plane_group.addButton(self._r_plane_zx)

        self.plane_len1_str = QtWidgets.QLabel("Length along first direction: [m]")
        self.plane_len1 = QtWidgets.QDoubleSpinBox(self)
        self.plane_len1.setRange(0,100000)
        self.plane_len1.setValue(1)

        self.plane_len2_str = QtWidgets.QLabel("Length along second direction: [m]")
        self.plane_len2 = QtWidgets.QDoubleSpinBox(self)
        self.plane_len2.setRange(0,100000)
        self.plane_len2.setValue(1)

        self.plane_div1_str = QtWidgets.QLabel("Num. of points in first direction: ")
        self.plane_div1 = QtWidgets.QDoubleSpinBox(self)
        self.plane_div1.setRange(2,1000)
        self.plane_div1.setDecimals(0)

        self.plane_div2_str = QtWidgets.QLabel("Num. of points in second direction: ")
        self.plane_div2 = QtWidgets.QDoubleSpinBox(self)
        self.plane_div2.setRange(2,1000)
        self.plane_div2.setDecimals(0)

        self.plane_x_off_str = QtWidgets.QLabel("X axis offset: [m]")
        self.plane_x_off = QtWidgets.QDoubleSpinBox(self)
        self.plane_x_off.setRange(-100000,100000)

        self.plane_y_off_str = QtWidgets.QLabel("Y axis offset: [m]")
        self.plane_y_off = QtWidgets.QDoubleSpinBox(self)
        self.plane_y_off.setRange(-100000,100000)

        self.plane_z_off_str = QtWidgets.QLabel("Z axis offset: [m]")
        self.plane_z_off = QtWidgets.QDoubleSpinBox(self)
        self.plane_z_off.setRange(-100000,100000)


        self.plane_start_num_str = QtWidgets.QLabel("Start numbering with:")
        self.plane_start_num = QtWidgets.QDoubleSpinBox(self)
        self.plane_start_num.setDecimals(0)
        self.plane_start_num.setRange(1,100000)

        left=0
        top=0
        first_top=0 #first widget from top
        right=0
        bottom=20

        # Create layout and add widgets
        main_layout = QtWidgets.QVBoxLayout()

        layout=QtWidgets.QGridLayout()
        layout.setContentsMargins(left, first_top, right, bottom)
        #layout.addWidget(self.plane_title,0,1)
        layout.addWidget(self.plane_orient_str,1,1)
        layout.addWidget(self._r_plane_xy,2,0)
        layout.addWidget(self._r_plane_yz,2,1)
        layout.addWidget(self._r_plane_zx,2,2)


        layout2=QtWidgets.QGridLayout()
        layout2.setContentsMargins(left, top, right, bottom)
        layout2.addWidget(self.plane_len1_str,0,0)
        layout2.addWidget(self.plane_len1,1,0)
        layout2.addWidget(self.plane_len2_str,0,1)
        layout2.addWidget(self.plane_len2,1,1)
        layout2.addWidget(self.plane_div1_str,2,0)
        layout2.addWidget(self.plane_div1,3,0)
        layout2.addWidget(self.plane_div2_str,2,1)
        layout2.addWidget(self.plane_div2,3,1)


        layout3=QtWidgets.QGridLayout()
        layout3.setContentsMargins(left, top, right, bottom)
        layout3.addWidget(self.plane_x_off_str,0,0)
        layout3.addWidget(self.plane_x_off,1,0)
        layout3.addWidget(self.plane_y_off_str,0,1)
        layout3.addWidget(self.plane_y_off,1,1)
        layout3.addWidget(self.plane_z_off_str,0,2)
        layout3.addWidget(self.plane_z_off,1,2)


        main_layout.addLayout(layout)
        main_layout.addLayout(layout2)
        main_layout.addLayout(layout3)
        main_layout.addWidget(self.plane_start_num_str)
        main_layout.addWidget(self.plane_start_num)
        main_layout.addStretch()

        self.stack2.setLayout(main_layout)

    def stack3UI(self):
        """
        Input data for creating box
        :return:
        """
        self.box_title = QtWidgets.QLabel("Create box")

        self.box_len_str = QtWidgets.QLabel("Length: [m]")
        self.box_len_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.box_lenx_str = QtWidgets.QLabel("X")
        self.box_lenx_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.box_leny_str = QtWidgets.QLabel("Y")
        self.box_leny_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.box_lenz_str = QtWidgets.QLabel("Z")
        self.box_lenz_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        self.box_lenx = QtWidgets.QDoubleSpinBox(self)
        self.box_lenx.setRange(0,100000)
        self.box_lenx.setValue(1)


        self.box_leny = QtWidgets.QDoubleSpinBox(self)
        self.box_leny.setRange(0,100000)
        self.box_leny.setValue(1)

        self.box_lenz = QtWidgets.QDoubleSpinBox(self)
        self.box_lenz.setRange(0,100000)
        self.box_lenz.setValue(1)

        self.box_div_str = QtWidgets.QLabel("Num. of points: ")
        self.box_div_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.box_divx_str = QtWidgets.QLabel("X")
        self.box_divx_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.box_divy_str = QtWidgets.QLabel("Y")
        self.box_divy_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.box_divz_str = QtWidgets.QLabel("Z")
        self.box_divz_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        self.box_divx = QtWidgets.QDoubleSpinBox(self)
        self.box_divx.setRange(2,1000)
        self.box_divx.setDecimals(0)

        self.box_divy = QtWidgets.QDoubleSpinBox(self)
        self.box_divy.setRange(2,1000)
        self.box_divy.setDecimals(0)

        self.box_divz = QtWidgets.QDoubleSpinBox(self)
        self.box_divz.setRange(2,1000)
        self.box_divz.setDecimals(0)

        self.box_off_str = QtWidgets.QLabel("Offset: [m]")
        self.box_off_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.box_offx_str = QtWidgets.QLabel("X")
        self.box_offx_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.box_offy_str = QtWidgets.QLabel("Y")
        self.box_offy_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.box_offz_str = QtWidgets.QLabel("Z")
        self.box_offz_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        self.box_x_off = QtWidgets.QDoubleSpinBox(self)
        self.box_x_off.setRange(-100000,100000)

        self.box_y_off = QtWidgets.QDoubleSpinBox(self)
        self.box_y_off.setRange(-100000,100000)

        self.box_z_off = QtWidgets.QDoubleSpinBox(self)
        self.box_z_off.setRange(-100000,100000)

        self.box_start_num_str = QtWidgets.QLabel("Start numbering with:")
        self.box_start_num = QtWidgets.QDoubleSpinBox(self)
        self.box_start_num.setDecimals(0)
        self.box_start_num.setRange(1,100000)

        left=0
        top=0
        first_top=0 #first widget from top
        right=0
        bottom=20

        # Create layout and add widgets
        main_layout = QtWidgets.QVBoxLayout()
        #layout.addWidget(self.box_title)

        layout=QtWidgets.QGridLayout()
        layout.setContentsMargins(left, first_top, right, bottom)
        layout.addWidget(self.box_len_str,0,1)
        layout.addWidget(self.box_lenx_str,1,0)
        layout.addWidget(self.box_leny_str,1,1)
        layout.addWidget(self.box_lenz_str,1,2)
        layout.addWidget(self.box_lenx,2,0)
        layout.addWidget(self.box_leny,2,1)
        layout.addWidget(self.box_lenz,2,2)

        layout2=QtWidgets.QGridLayout()
        layout2.setContentsMargins(left, top, right, bottom)
        layout2.addWidget(self.box_div_str,0,1)
        layout2.addWidget(self.box_divx_str,1,0)
        layout2.addWidget(self.box_divy_str,1,1)
        layout2.addWidget(self.box_divz_str,1,2)
        layout2.addWidget(self.box_divx,2,0)
        layout2.addWidget(self.box_divy,2,1)
        layout2.addWidget(self.box_divz,2,2)

        layout3=QtWidgets.QGridLayout()
        layout3.setContentsMargins(left, top, right, bottom)
        layout3.addWidget(self.box_off_str,0,1)
        layout3.addWidget(self.box_offx_str,1,0)
        layout3.addWidget(self.box_offy_str,1,1)
        layout3.addWidget(self.box_offz_str,1,2)
        layout3.addWidget(self.box_x_off,2,0)
        layout3.addWidget(self.box_y_off,2,1)
        layout3.addWidget(self.box_z_off,2,2)

        main_layout.addLayout(layout)
        main_layout.addLayout(layout2)
        main_layout.addLayout(layout3)
        main_layout.addWidget(self.box_start_num_str)
        main_layout.addWidget(self.box_start_num)
        main_layout.addStretch()

        self.stack3.setLayout(main_layout)

    def stack4UI(self):
        """
        Input data for creating cylinder
        :return:
        """
        self.title = QtWidgets.QLabel("Create cylinder")
        self.title.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)

        self.input_cyl_r_str = QtWidgets.QLabel("Radius: [m]")
        self.input_cyl_r_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.input_cyl_r = QtWidgets.QDoubleSpinBox(self)
        self.input_cyl_r.setRange(0,100000)
        self.input_cyl_r.setValue(1)

        self.input_cyl_h_str = QtWidgets.QLabel("Height: [m]")
        self.input_cyl_h_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.input_cyl_h = QtWidgets.QDoubleSpinBox(self)
        self.input_cyl_h.setRange(0,100000)
        self.input_cyl_h.setValue(1)

        self.input_cyl_z_off_str = QtWidgets.QLabel("Z axis offset: [m]")
        self.input_cyl_z_off_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.input_cyl_z_off = QtWidgets.QDoubleSpinBox(self)
        self.input_cyl_z_off.setRange(-100000,100000)

        self.input_start_num_str = QtWidgets.QLabel("Start numbering with:")
        self.input_start_num = QtWidgets.QDoubleSpinBox(self)
        self.input_start_num.setDecimals(0)
        self.input_start_num.setRange(1,100000)

        self.input_num_orient_str= QtWidgets.QLabel("Numbering orientation:")
        self._r_orient_group=QtWidgets.QButtonGroup(self) # Number group
        self._r_vert_orient=QtWidgets.QRadioButton("Vertical")
        self._r_vert_orient.setChecked(True)

        self._r_orient_group.addButton(self._r_vert_orient)
        self._r_horiz_orient=QtWidgets.QRadioButton("Horizontal")
        self._r_orient_group.addButton(self._r_horiz_orient)
        self.input_num_orient=0

        self.input_main_div_str = QtWidgets.QLabel("Number of points:")
        self.input_main_div_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.input_height_div_str = QtWidgets.QLabel("Along height:")
        self.input_height_div_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.input_height_div = QtWidgets.QDoubleSpinBox(self)
        self.input_height_div.setDecimals(0)
        self.input_height_div.setRange(2,100)

        self.input_circ_div_str = QtWidgets.QLabel("Along circumference:")
        self.input_circ_div_str.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        self.input_circ_div = QtWidgets.QDoubleSpinBox(self)
        self.input_circ_div.setDecimals(0)
        self.input_circ_div.setRange(3,100)

        left=0
        top=0
        first_top=0 #first widget from top
        right=0
        bottom=20

        # Create layout and add widgets
        main_layout = QtWidgets.QVBoxLayout()

        layout=QtWidgets.QGridLayout()
        layout.setContentsMargins(left, first_top, right, bottom)
        #layout.addWidget(self.title,0,1)
        layout.addWidget(self.input_cyl_r_str,1,0)
        layout.addWidget(self.input_cyl_h_str,1,1)
        layout.addWidget(self.input_cyl_z_off_str,1,2)
        layout.addWidget(self.input_cyl_r,2,0)
        layout.addWidget(self.input_cyl_h,2,1)
        layout.addWidget(self.input_cyl_z_off,2,2)

        layout2=QtWidgets.QGridLayout()
        layout2.setContentsMargins(left, top, right, bottom)
        layout2.addWidget(self.input_main_div_str,0,0,1,2) # row, column, rowSpan, columnSpan
        layout2.addWidget(self.input_height_div_str,1,0)
        layout2.addWidget(self.input_circ_div_str,1,1)
        layout2.addWidget(self.input_height_div,2,0)
        layout2.addWidget(self.input_circ_div,2,1)

        main_layout.addLayout(layout)
        main_layout.addLayout(layout2)
        main_layout.addWidget(self.input_start_num_str)
        main_layout.addWidget(self.input_start_num)
        main_layout.addWidget(self.input_num_orient_str)
        main_layout.addWidget(self._r_horiz_orient)
        main_layout.addWidget(self._r_vert_orient)
        main_layout.addStretch()

        self.stack4.setLayout(main_layout)

    def display(self,i):
        self.Stack.setCurrentIndex(i)

    def get_data(self):
        """
        Gather user input for geometry creation
        :return:
        """
        if self.Stack.currentIndex()==0:
            data={'geom_type':'line',
                'xs':self.line_xs.value(),
                   'ys':self.line_ys.value(),
                   'zs':self.line_zs.value(),
                   'xe':self.line_xe.value(),
                    'ye':self.line_ye.value(),
                   'ze':self.line_ze.value(),
                   'num_of_points':self.line_div.value(),
                  'start_num':self.line_start_num.value()
                   }
        if self.Stack.currentIndex()==1:
            data={'geom_type':'plane',
                  'plane_orient':self._r_plane_group.checkedButton().text(),
                'len1':self.plane_len1.value(),
                   'len2':self.plane_len2.value(),
                   'div1':self.plane_div1.value(),
                   'div2':self.plane_div2.value(),
                    'x_offset':self.plane_x_off.value(),
                   'y_offset':self.plane_y_off.value(),
                   'z_offset':self.plane_z_off.value(),
                  'start_num':self.plane_start_num.value()
                   }
        if self.Stack.currentIndex()==2:
            data={'geom_type':'box',
                'lenx':self.box_lenx.value(),
                  'leny':self.box_leny.value(),
                  'lenz':self.box_lenz.value(),
                   'divx':self.box_divx.value(),
                  'divy':self.box_divy.value(),
                  'divz':self.box_divz.value(),
                    'x_offset':self.box_x_off.value(),
                   'y_offset':self.box_y_off.value(),
                   'z_offset':self.box_z_off.value(),
                  'start_num':self.box_start_num.value()
                   }
        if self.Stack.currentIndex()==3:
            data={'geom_type':'cylinder',
                'radius':self.input_cyl_r.value(),
                   'height':self.input_cyl_h.value(),
                   'start_num':self.input_start_num.value(),
                   'num_orient':self._r_orient_group.checkedButton().text(),
                    'z_offset':self.input_cyl_z_off.value(),
                   'height_div':self.input_height_div.value(),
                   'circ_div':self.input_circ_div.value()
                   }
        return data

    @staticmethod
    def return_data(parent = None):
        dialog = dialog_geom_primitives(parent)
        result = dialog.exec_()
        input_data = dialog.get_data()
        return (result, input_data)



if __name__ == '__main__':
    import sys
    app = QtWidgets.QApplication(sys.argv)

    main_window = GeometryWidget()
    main_window.setGeometry(100, 100, 640, 480)
    main_window.show()

    sys.exit(app.exec_())
