
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


'''
Created on 20. maj 2014

TODO: That mnums in the beginning of every function, thats bad!

TODO: Alot of refactoring.

TODO: Put tables in a dictionary, that way you have a nice overview
        of what is inside and also is much better :)


@author: Matjaz
'''
import time

import os

import itertools

from datetime import datetime

import pandas as pd

from pandas import ExcelWriter

from OpenModal.anim_tools import zyx_euler_to_rotation_matrix

import numpy as np
import pyuff
import OpenModal.utils as ut

# import _transformations as tr

# Uff fields definitions (human-readable).
types = dict()
types[15] = 'Geometry'
types[82] = 'Lines'
types[151] = 'Header'
types[2411] = 'Geometry'
types[164] = 'Units'
types[58] = 'Measurement'
types[55] = 'Analysis'
types[2420] = 'Coor. sys.'
types[18] = 'Coor. sys.'

# Function type definition.
FUNCTION_TYPE = dict()
FUNCTION_TYPE['General'] = 0 # also: unknown
FUNCTION_TYPE['Time Response'] = 1
FUNCTION_TYPE['Auto Spectrum'] = 2
FUNCTION_TYPE['Cross Spectrum'] = 3
FUNCTION_TYPE['Frequency Response Function'] = 4
FUNCTION_TYPE['Transmissibility'] = 5
FUNCTION_TYPE['Coherence'] = 6
FUNCTION_TYPE['Auto Correlation'] = 7
FUNCTION_TYPE['Cross Correlation'] = 8
FUNCTION_TYPE['Power Spectral Density (PSD)'] = 9
FUNCTION_TYPE['Energy Spectral Density (ESD)'] = 10
FUNCTION_TYPE['Probability Density Function'] = 11
FUNCTION_TYPE['Spectrum'] = 12
FUNCTION_TYPE['Cumulative Frequency Distribution'] = 13
FUNCTION_TYPE['Peaks Valley'] = 14
FUNCTION_TYPE['Stress/Cycles'] = 15
FUNCTION_TYPE['Strain/Cycles'] = 16
FUNCTION_TYPE['Orbit'] = 17
FUNCTION_TYPE['Mode Indicator Function'] = 18
FUNCTION_TYPE['Force Pattern'] = 19
FUNCTION_TYPE['Partial Power'] = 20
FUNCTION_TYPE['Partial Coherence'] = 21
FUNCTION_TYPE['Eigenvalue'] = 22
FUNCTION_TYPE['Eigenvector'] = 23
FUNCTION_TYPE['Shock Response Spectrum'] = 24
FUNCTION_TYPE['Finite Impulse Response Filter'] = 25
FUNCTION_TYPE['Multiple Coherence'] = 26
FUNCTION_TYPE['Order Function'] = 27
FUNCTION_TYPE['Phase Compensation'] = 28

# Specific data type for abscisa/ordinate
SPECIFIC_DATA_TYPE = dict()
SPECIFIC_DATA_TYPE['unknown'] = 0
SPECIFIC_DATA_TYPE['general'] = 1
SPECIFIC_DATA_TYPE['stress'] = 2
SPECIFIC_DATA_TYPE['strain'] = 3
SPECIFIC_DATA_TYPE['temperature'] = 5
SPECIFIC_DATA_TYPE['heat flux'] = 6
SPECIFIC_DATA_TYPE['displacement'] = 8
SPECIFIC_DATA_TYPE['reaction force'] = 9
SPECIFIC_DATA_TYPE['velocity'] = 11
SPECIFIC_DATA_TYPE['acceleration'] = 12
SPECIFIC_DATA_TYPE['excitation force'] = 13
SPECIFIC_DATA_TYPE['pressure'] = 15
SPECIFIC_DATA_TYPE['mass'] = 16
SPECIFIC_DATA_TYPE['time'] = 17
SPECIFIC_DATA_TYPE['frequency'] = 18
SPECIFIC_DATA_TYPE['rpm'] = 19
SPECIFIC_DATA_TYPE['order'] = 20
SPECIFIC_DATA_TYPE['sound pressure'] = 21
SPECIFIC_DATA_TYPE['sound intensity'] = 22
SPECIFIC_DATA_TYPE['sound power'] = 23



# TODO: Fast get and set. Check setting with enlargement.

class ModalData(object):
    """The data object holds all measurement, results and geometry data
    """
    def __init__(self):
        """
        Constructor
        """
        self.create_empty()


    def create_empty(self):
        """Create an empty data container."""
        # Tables
        self.tables = dict()

        # Holds the tables, populated by importing a uff file.
        # TODO: This is temporary? Maybe, maybe not, might be
        # a good idea to have some reference of imported data!
        self.uff_import_tables = dict()

        self.create_info_table()
        self.create_geometry_table()
        self.create_measurement_table()
        self.create_analysis_table()
        self.create_lines_table()
        self.create_elements_table()

        # Set model id
        self.model_id = 0

    def create_info_table(self):
        """Creates an empty info table."""
        self.tables['info'] = pd.DataFrame(columns=['model_id', 'model_name', 'description', 'units_code', 'length',
                                                    'force', 'temp', 'temp_offset'])

        # self.tables['info'] = pd.DataFrame(columns=['model_id', 'uffid', 'value'])

    def create_geometry_table(self):
        """Creates an empty geometry table."""
        self.tables['geometry'] = pd.DataFrame(columns=['model_id', 'uffid', 'node_nums',
                                                        'x', 'y', 'z', 'thx', 'thy', 'thz',
                                                        'disp_cs', 'def_cs',
                                                        'color','clr_r','clr_g','clr_b','clr_a',
                                                        'r','phi','cyl_thz'])

    def create_measurement_table(self):
        """Creates an empty measurement table."""
        self.tables['measurement_index'] = pd.DataFrame(columns=['model_id', 'measurement_id', 'uffid', 'field_type', 'excitation_type',
                                                                 'func_type', 'rsp_node', 'rsp_dir', 'ref_node',
                                                                 'ref_dir', 'abscissa_spec_data_type',
                                                                 'ordinate_spec_data_type', 'orddenom_spec_data_type', 'zero_padding'], dtype=int)

        self.tables['measurement_values'] = pd.DataFrame(columns=['model_id', 'measurement_id', 'frq', 'amp'])
        self.tables['measurement_values'].amp = self.tables['measurement_values'].amp.astype('complex')

        self.tables['measurement_values_td'] = pd.DataFrame(columns=['model_id', 'measurement_id', 'n_avg', 'x_axis',
                                                                     'excitation', 'response'])

    def create_analysis_table(self):
        """Creates an empty analysis table."""
        self.tables['analysis_index'] = pd.DataFrame(columns=['model_id', 'analysis_id', 'analysis_method', 'uffid',
                                                              'field_type', 'analysis_type', 'data_ch',
                                                              'spec_data_type', 'load_case', 'mode_n', 'eig', 'freq',
                                                              'freq_step_n', 'node_nums', 'rsp_node', 'rsp_dir',
                                                              'ref_node', 'ref_dir', 'data_type', 'ref_node', 'ref_dir',
                                                              'data_type', 'eig_real','eig_xi', 'spots'])

        self.tables['analysis_values'] = pd.DataFrame(columns=['model_id', 'analysis_id', 'analysis_method', 'mode_n',
                                                               'node_nums', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6'])

        self.tables['analysis_settings'] = pd.DataFrame(columns=['model_id', 'analysis_id', 'analysis_method',
                                                                 'f_min','f_max', 'nmax', 'err_fn', 'err_xi', ])

        self.tables['analysis_stabilisation'] = pd.DataFrame(columns=['model_id', 'analysis_id', 'analysis_method',
                                                                      'pos', 'size', 'pen_color', 'pen_width',
                                                                      'symbol', 'brush', 'damp'])

        self.tables['analysis_index'].eig = self.tables['analysis_index'].eig.astype('complex')

        self.tables['analysis_values'].r1 = self.tables['analysis_values'].r1.astype('complex')
        self.tables['analysis_values'].r2 = self.tables['analysis_values'].r2.astype('complex')
        self.tables['analysis_values'].r3 = self.tables['analysis_values'].r3.astype('complex')
        self.tables['analysis_values'].r4 = self.tables['analysis_values'].r4.astype('complex')
        self.tables['analysis_values'].r5 = self.tables['analysis_values'].r5.astype('complex')
        self.tables['analysis_values'].r6 = self.tables['analysis_values'].r6.astype('complex')

    def create_lines_table(self):
        """Creates an empty lines table."""
        self.tables['lines'] = pd.DataFrame(['model_id', 'uffid', 'id', 'field_type', 'trace_num',
                                              'color', 'n_nodes', 'trace_id', 'pos', 'node'])

    def create_elements_table(self):
        """Creates an empty elements table."""
        # TODO: Missing 'physical property table number' and 'material property ...'
        # TODO: Missing 'fe descriptor id', chosen from a list of 232(!) types!!?
        # TODO: Missing beam support.
        self.tables['elements_index'] = pd.DataFrame(columns=['model_id', 'element_id', 'element_descriptor', 'color',
                                                      'nr_of_nodes','clr_r','clr_g','clr_b','clr_a'])
        self.tables['elements_values'] = pd.DataFrame(columns=['model_id', 'element_id', 'node_id', 'node_pos'])


    def new_model(self, model_id=-1, entries=dict()):
        """Set new model id. Values can be set through entries dictionary, for each
        value left unset, default will be used."""
        if model_id == -1:
            # Create a new model_id. First check if table is empty.
            current_models = self.tables['info'].model_id
            if current_models.size == 0:
                model_id = 0
            else:
                model_id = current_models.max() + 1

        fields = {'db_app': 'ModalData', 'time_db_created': time.strftime("%d-%b-%y %H:%M:%S"),
                  'time_db_saved': time.strftime("%d-%b-%y %H:%M:%S"), 'program': 'OpenModal',
                  'model_name': 'DefaultName', 'description': 'DefaultDecription', 'units_code': 9,
                  'temp': 1, 'temp_mode': 1, 'temp_offset': 1, 'length': 1, 'force': 1,
                  'units_description': 'User unit system'}



        for key in entries:
            fields[key] = entries[key]

        # TODO: Check if model_id already exists.

        input = [model_id, fields['model_name'], fields['description'], fields['units_code'], fields['length'],
                 fields['force'], fields['temp'], fields['temp_offset']]

        new_model = pd.DataFrame([input], columns=['model_id', 'model_name', 'description', 'units_code', 'length',
                                                    'force', 'temp', 'temp_offset'])

        self.tables['info'] = pd.concat([self.tables['info'], new_model], ignore_index=True)

        return model_id

    def new_measurement(self, model_id, excitation_type, frequency, h, reference=[0, 0], response=[0, 0],
                        function_type='Frequency Response Function', abscissa='frequency', ordinate='acceleration',
                        denominator='excitation force', zero_padding=0, td_x_axis=np.array([]),
                        td_excitation=None, td_response=None):

        """Add a new measurement."""
        # Check if model id exists.
        if self.tables['info'].model_id.size == 0:
            raise ValueError
        elif not any(self.tables['info'].model_id == model_id):
            raise ValueError

        # Prepare a new measurement_id.
        if self.tables['measurement_index'].measurement_id.size == 0:
            measurement_id = 0
        else:
            measurement_id = self.tables['measurement_index'].measurement_id.max() + 1

        newentry_idx = pd.DataFrame([[model_id, measurement_id, excitation_type, FUNCTION_TYPE[function_type], response[0],
                                      response[1], reference[0], reference[1], SPECIFIC_DATA_TYPE[abscissa],
                                      SPECIFIC_DATA_TYPE[ordinate], SPECIFIC_DATA_TYPE[denominator], zero_padding]],
                                    columns=['model_id', 'measurement_id', 'excitation_type', 'func_type', 'rsp_node', 'rsp_dir',
                                             'ref_node', 'ref_dir', 'abscissa_spec_data_type',
                                             'ordinate_spec_data_type', 'orddenom_spec_data_type', 'zero_padding'])

        self.tables['measurement_index'] = pd.concat([ self.tables['measurement_index'],
                                                       newentry_idx], ignore_index=True)

        # Add entry with measured frf.
        newentry_val = pd.DataFrame(columns=['model_id', 'measurement_id', 'frq', 'amp'])
        newentry_val['frq'] = frequency
        newentry_val['amp'] = h
        newentry_val['model_id'] = model_id
        newentry_val['measurement_id'] = measurement_id


        self.tables['measurement_values'] = pd.concat([self.tables['measurement_values'],
                                                                 newentry_val], ignore_index=True)

        # if td_x_axis.size > 0:
        #     # TODO: Create it with size you already know. Should be faster?
        #     newentry_val_td = pd.DataFrame(columns=['model_id', 'measurement_id', 'x_axis', 'excitation', 'response'])
        #     newentry_val_td['x_axis'] = td_x_axis
        #     newentry_val_td['excitation'] = td_excitation
        #     newentry_val_td['response'] = td_response
        #     newentry_val_td['model_id'] = model_id
        #     newentry_val_td['measurement_id'] = measurement_id
        #
        #     self.tables['measurement_values_td'] = pd.concat([self.tables['measurement_values_td'], newentry_val_td],
        #                                                      ignore_index=True)

        if td_x_axis.size > 0:
            n_averages = len(td_response)
            i = 0
            # TODO: Optimize here.
            for td_excitation_i, td_response_i in zip(td_excitation, td_response):
            # TODO: Create it with size you already know. Should be faster?
                newentry_val_td = pd.DataFrame(columns=['model_id', 'measurement_id', 'n_avg',
                                                        'x_axis', 'excitation', 'response'])
                newentry_val_td['x_axis'] = td_x_axis
                newentry_val_td['excitation'] = td_excitation_i
                newentry_val_td['response'] = td_response_i
                newentry_val_td['model_id'] = model_id
                newentry_val_td['measurement_id'] = measurement_id
                newentry_val_td['n_avg'] = i
                i += 1

                self.tables['measurement_values_td'] = pd.concat([self.tables['measurement_values_td'], newentry_val_td],
                                                                 ignore_index=True)

    def remove_model(self, model_id):
        """Remove all data connected to the supplied model id."""
        try:
            el_idx = self.tables['elements_index']
            el_vals = self.tables['elements_values']
            elements_id = el_idx[el_idx.model_id == model_id].element_id
            self.tables['elements_values'] = self.tables['elements_values'][~el_vals.element_id.isin(elements_id)]
            self.tables['elements_index'] = self.tables['elements_index'][el_idx.model_id != model_id]
        except AttributeError:
            print('There is no element data to delete.')

        try:
            lines = self.tables['lines']
            self.tables['lines'] = self.tables['lines'][lines.model_id != model_id]
        except AttributeError:
            print('There is no line data to delete.')

        try:
            an_idx = self.tables['analysis_index']
            an_vals = self.tables['analysis_values']
            analysis_id = an_idx[an_idx.model_id == model_id].analysis_id
            self.tables['analysis_values'] = self.tables['analysis_values'][~an_vals.element_id.isin(analysis_id)]
            self.tables['analysis_index'] = self.tables['analysis_index'][an_idx.model_id != model_id]
        except AttributeError:
            print('There is no analysis data to delete.')

        try:
            me_idx = self.tables['measurement_index']
            me_vals = self.tables['measurement_values']
            me_vals_td = self.tables['measurement_values_td']
            measurement_id = me_idx[me_idx.model_id == model_id].measurement_id
            self.tables['measurement_values_td'] = self.tables['measurement_values_td'][~me_vals_td.measurement_id.isin(measurement_id)]
            self.tables['measurement_values'] = self.tables['measurement_values'][~me_vals.measurement_id.isin(measurement_id)]
            self.tables['measurement_index'] = self.tables['measurement_index'][me_idx.model_id != model_id]
        except AttributeError:
            print('There is no measurement data to delete.')

        try:
            geometry = self.tables['geometry']
            self.tables['geometry'] = self.tables['geometry'][geometry.model_id != model_id]
        except AttributeError:
            print('There is no geometry data to delete.')

        try:
            info = self.tables['info']
            self.tables['info'] = self.tables['info'][info.model_id != model_id]
        except AttributeError:
            print('There is no info data to delete.')


    def import_uff(self, fname):
        """Pull data from uff."""
        # Make sure you start with new model ids at the appropriate index.
        if self.tables['info'].model_id.size > 0:
            base_key = self.tables['info'].model_id.max() + 1
        else:
            base_key=0

        uffdata = ModalDataUff(fname, base_key=base_key)

        for key in self.tables.keys():
            if key in uffdata.tables:
                # uffdata.tables[key].model_id += 100
                self.tables[key] = pd.concat([self.tables[key], uffdata.tables[key]], ignore_index=True)
                self.uff_import_tables[key] = ''

        self.file_structure = uffdata.file_structure


    def export_to_uff(self, fname, model_ids=[], data_types=[], separate_files_flag=False):
        """Export data to uff."""
        model_ids = self.tables['info'].model_id.unique()
        if len(model_ids) == 0:
            model_ids = self.tables['info'].model_id.unique()

        if len(data_types) == 0:
            data_types = ['nodes', 'lines', 'elements', 'measurements', 'analyses']

        if len(model_ids) == 0:
            print('Warning: Empty tables. (No model_ids found).')
            return False

        t = datetime.now()
        folder_timestamp = 'OpenModal Export UFF -- {:%Y %d-%m %H-%M-%S}'.format(t)
        export_folder = os.path.join(fname, folder_timestamp)

        try:
            os.mkdir(export_folder)
        except:
            print('Warning: File exists. Try again later ...')
            return False


        for model_id in model_ids:
            # -- Write info.
            dfi = self.tables['info']
            dfi = dfi[dfi.model_id == model_id]

            # TODO: Do not overwrite this dfi
            model_name = dfi.model_name.values[0]

            if not separate_files_flag:
                uffwrite=pyuff.UFF(os.path.join(export_folder, '{0}_{1:.0f}.uff'.format(model_name, model_id)))

            if len(dfi) != 0:

                dset_info =  {'db_app': 'modaldata v1',
                              'model_name': dfi.model_name.values[0],
                              'description': dfi.description.values[0],
                              'program': 'Open Modal'}
                dset_units = {'units_code': dfi.units_code.values[0],
                              # TODO: Maybe implement other data.
                              # 'units_description': dfi.units_description,
                              # 'temp_mode': dfi.temp_mode,
                              'length': dfi.length.values[0],
                              'force': dfi.force.values[0],
                              'temp': dfi.temp.values[0],
                              'temp_offset': dfi.temp_offset.values[0]}

                # for key in dset_info.keys():
                #     dset_info[key] = dset_info[key].value.values[0]
                dset_info['type'] = 151

                # for key in dset_units.keys():
                #     dset_units[key] = dset_units[key].value.values[0]
                dset_units['type'] = 164

                if separate_files_flag:
                    uffwrite=pyuff.UFF(os.path.join(export_folder, '{0}_{1:.0f}_info.uff'.format(model_name, model_id)))

                uffwrite._write_set(dset_info, mode='add')
                uffwrite._write_set(dset_units, mode='add')

            # -- Write Geometry.
            if 'nodes' in data_types:
                dfg = self.tables['geometry']
                #dfg = dfg[dfg.model_id==model_id]

                #drop nan lines defined in geometry
                model_id_mask=dfg.model_id==model_id
                nan_mask = dfg[['node_nums','x', 'y', 'z','thz', 'thy', 'thx' , 'model_id']].notnull().all(axis=1)
                comb_mask = model_id_mask & nan_mask
                dfg = dfg[comb_mask]

                if len(dfg) != 0:

                    # .. First the coordinate systems. Mind the order of angles (ZYX)
                    size = len(dfg)
                    local_cs = np.zeros((size * 4, 3), dtype=float)
                    th_angles = dfg[['thz', 'thy', 'thx']].values

                    for i in range(size):
                        #local_cs[i*4:i*4+3, :] = ut.zyx_euler_to_rotation_matrix(th_angles[i, :])
                        local_cs[i*4:i*4+3, :] = zyx_euler_to_rotation_matrix(th_angles[i, :]*np.pi/180.)
                        local_cs[i*4+3, :] = 0.0

                    dset_cs = {'local_cs': local_cs, 'nodes': dfg[['node_nums']].values, 'type': 2420}
                    uffwrite._write_set(dset_cs, mode='add')

                    # .. Then points.
                    dset_geometry = {'grid_global': dfg[['node_nums', 'x', 'y', 'z']].values,
                                     'export_cs_number': 0,
                                     'cs_color': 8,
                                     'type': 2411}


                    if separate_files_flag:
                        uffwrite=pyuff.UFF(os.path.join(export_folder, '{0}_{1:.0f}_nodes.uff'.format(model_name, model_id)))
                    uffwrite._write_set(dset_geometry, mode='add')


            # -- Write Measurements.
            if 'measurements' in data_types:
                dfi = self.tables['measurement_index']
                dfi = dfi[dfi.model_id == model_id]
                dfi.field_type = 58

                if len(dfi) != 0:
                    dfv = self.tables['measurement_values']
                    dfv = dfv[dfv.model_id == model_id]

                    for id, measurement in dfi.iterrows():
                        data = dfv[dfv.measurement_id == measurement.measurement_id]
                        dsets={'type': measurement['field_type'],
                               'func_type': measurement['func_type'],
                               'data': data['amp'].values.astype('complex'),
                               'x': data['frq'].values,
                               'rsp_node': measurement['rsp_node'],
                               'rsp_dir': measurement['rsp_dir'],
                               'ref_node': measurement['ref_node'],
                               'ref_dir': measurement['ref_dir'],
                               'rsp_ent_name':model_name, 'ref_ent_name':model_name}
                        # TODO: Make rsp_ent_name and ref_ent_name fields in measurement_index table.

                        if pd.isnull(measurement['abscissa_spec_data_type']):
                            dsets['abscissa_spec_data_type'] = 0
                        else:
                            dsets['abscissa_spec_data_type'] = measurement['abscissa_spec_data_type']

                        if pd.isnull(measurement['ordinate_spec_data_type']):
                            dsets['ordinate_spec_data_type'] = 0
                        else:
                            dsets['ordinate_spec_data_type'] = measurement['ordinate_spec_data_type']

                        if pd.isnull(measurement['orddenom_spec_data_type']):
                            dsets['orddenom_spec_data_type'] = 0
                        else:
                            dsets['orddenom_spec_data_type'] = measurement['orddenom_spec_data_type']

                        if separate_files_flag:
                            uffwrite=pyuff.UFF(os.path.join(export_folder, '{0}_{1:.0f}_measurements.uff'.format(model_name, model_id)))

                        uffwrite._write_set(dsets, mode='add')


    def export_to_csv(self, fname, model_ids=[], data_types=[]):
        """Export data to uff."""
        if len(model_ids) == 0:
            model_ids = self.tables['info'].model_id.unique()

        if len(data_types) == 0:
            data_types = ['nodes', 'lines', 'elements', 'measurements', 'analyses']

            if len(model_ids) == 0:
                print('Warning: Empty tables. (No model_ids found).')
                return False

        t = datetime.now()
        folder_timestamp = 'OpenModal Export CSV -- {:%Y %d-%m %H-%M-%S}'.format(t)
        export_folder = os.path.join(fname, folder_timestamp)

        try:
            os.mkdir(export_folder)
        except:
            print('Warning: File exists. Try again later ...')
            return False

        for model_id in model_ids:
            # -- Write info.
            dfi = self.tables['info']
            dfi = dfi[dfi.model_id == model_id]

            model_name = '{0}_{1:.0f}'.format(dfi.model_name.values[0], model_id)
            model_dir = os.path.join(export_folder, model_name)
            os.mkdir(model_dir)

            df_ = self.tables['info']
            df_[df_.model_id == model_id].to_csv(os.path.join(model_dir, 'info.csv'))

            if 'nodes' in data_types:
                df_ = self.tables['geometry']
                df_[df_.model_id == model_id].to_csv(os.path.join(model_dir, 'geometry.csv'))

            # -- Special treatment for measurements
            if 'measurements' in data_types:
                measurements_dir = os.path.join(model_dir, 'measurements')
                os.mkdir(measurements_dir)

                df_ = self.tables['measurement_index']
                df_[df_.model_id == model_id].to_csv(os.path.join(measurements_dir, 'measurements_index.csv'))

                df_ = self.tables['measurement_values']
                grouped_measurements = df_[df_.model_id == model_id].groupby('measurement_id')

                for id, measurement in grouped_measurements:
                    measurement['amp_real'] = measurement.amp.real
                    measurement['amp_imag'] = measurement.amp.imag
                    measurement[['frq', 'amp_real', 'amp_imag']].to_csv(os.path.join(measurements_dir,
                                                                                     'measurement_{0:.0f}.csv'.format(id)),
                                                                        index=False)



class ModalDataUff(object):
    '''
    Reads the uff file and populates the following pandas tables:
    -- ModalData.measurement_index : index of all measurements from field 58
    -- ModalData.geometry          : index of all points with CS from fields 2411 and 15
    -- ModalData.info              : info about measurements
    
    Based on the position of field in the uff file, uffid is assigned to each field in the following
    maner: first field, uffid = 0, second field, uffid = 1 and so on. Columns are named based on keys
    from the UFF class if possible. Fields uffid and field_type (type of field, eg. 58) are added.
    
    Geometry table combines nodes and their respective CSs, column names are altered.
    '''

    def __init__(self, fname='../../unvread/data/shield.uff', base_key=0):
        '''
        Constructor
        
        '''
        self.uff_object = pyuff.UFF(fname)

        # Start above base_key.
        self.base_key = base_key

        self.uff_types = self.uff_object.get_set_types()
        # print(self.uff_types)

        # Models
        self.models = dict()

        # Tables
        self.tables = dict()

        # Coordinate-system tables
        self.localcs = pd.DataFrame(columns=['model_id', 'uffidcs', 'node_nums', 'x1', 'x2', 'x3',
                                             'y1', 'y2', 'y3',
                                             'z1', 'z2', 'z3'])

        self.localeul = pd.DataFrame(columns=['model_id', 'uffidcs', 'node_nums', 'thx', 'thy', 'thz'])

        # File structure.
        self.file_structure = ['%5d %-10s' % (field, types[field]) for field in self.uff_types]

        self.create_model()


    def create_model(self):
        """Scans the uff file and creates a model from
        geometries and data, which is then populated. The models
        are grouped based on the field 151!"""
        # -- Scan geometries, each geometry is one model.
        mnums = list(np.nonzero(self.uff_types==151)[0])


        if len(mnums) == 0:
            mnums = list(np.nonzero(self.uff_types==164)[0])
            # -- What if there is no geometry? Only one model then I guess ...

        if len(mnums) == 0:
            print('Warning: There is no INFO or UNITS field!')
            self.models[0] = range(len(self.uff_types))
            # .. TODO: You have to pass this warning on.
        else:
            # .. Define intervals, by sequential order, for each model.
            for model_id, num in enumerate(mnums):
                if model_id == (len(mnums)-1):
                    self.models[model_id] = range(num, len(self.uff_types))
                else:
                    # .. Last model has special treatment ([x:] instead of [x:y])
                    self.models[model_id] = range(num, mnums[model_id+1])

        for model_id, model in self.models.items():
            self.populate_model(model_id+self.base_key, model)

        # print(self.models)
        # print(self.uff_types)


    def populate_model(self, model_id, model):
        """Read all data for each model."""
        model = list(model)

        self.gen_measurement_table(model_id, model)
        self.gen_geometry_table(model_id, model)
        self.gen_analysis_table(model_id, model)
        self.gen_lines_table(model_id, model)
        self.gen_info_table(model_id, model)

        # .. TODO: Here is the place to check for connections between
        #       fields, other than by sequential order. Check if LMS
        #       writes anything. (It does not!)

    def gen_measurement_table(self, model_id, model):
        """Read measurements."""
        mnums = np.nonzero(self.uff_types[model] == 58)[0]
        mnums += model[0]
            
        if len(mnums) == 0:
            return False
        
        mlist = []
        #dlist = pd.DataFrame()
        
        # .. Create field list.
        sdata = self.uff_object.read_sets(mnums[0])
        fields = ['model_id', 'measurement_id', 'uffid', 'field_type']
        fields.extend([key for key in sdata.keys() if not ('x' in key or 'data' in key)])        

        concat_list = []
        for mnum in list(mnums):
            dlist_ = pd.DataFrame()
            
            sdata = self.uff_object.read_sets(mnum)
            
            # .. Setup a new line in measurement index table.
            line = [model_id, mnum, mnum, 58]
            line.extend([sdata[key] for key in fields if not ('uffid' in key or 'field_type' in key or 'model_id' in key or 'measurement_id' in key)])
            mlist.append(line)

            # TODO: Uredi podporo za kompleksne vrednosti tukaj. NE štima še čist!
            dlist_['frq'] = sdata['x']
            dlist_['amp'] = sdata['data']
            dlist_['amp'] = dlist_['amp'].astype('complex')
            dlist_['amp'] = sdata['data']
            dlist_['uffid'] = mnum
            dlist_['measurement_id'] = mnum
            dlist_['model_id'] = model_id

            concat_list.append(dlist_)

        dlist = pd.concat(concat_list, ignore_index=True)
        concat_list = []

        if 'measurement_index' in self.tables:
            self.tables['measurement_index'] = pd.concat([self.tables['measurement_index'], pd.DataFrame(mlist, columns=fields)], ignore_index=True)
            self.tables['measurement_values'] = pd.concat([self.tables['measurement_values'], dlist], ignore_index=True)
        else:
            self.tables['measurement_index'] = pd.DataFrame(mlist, columns=fields)
            self.tables['measurement_values'] = dlist

        return True
    
    def getlocalcs(self, model_id, model):
        '''Read cs fields and convert all to euler angels.'''

        mnums = np.nonzero(self.uff_types[model]==2420)[0]
        # mnums.extend(list(np.nonzero(self.uff_types==18)[0]))
        mnums.sort()

        mnums += model[0]

        if len(mnums) == 0:
            return False

        # So ... the cs come in different flavours. One is simply the three
        #   vectors defining the axes.
        # self.localcs = pd.DataFrame(columns=['model_id', 'uffidcs', 'node_nums', 'x1', 'x2', 'x3',
        #                                      'y1', 'y2', 'y3',
        #                                      'z1', 'z2', 'z3'])

        # ... another one is the three euler angles, using axes z, y' and x''. This is
        #       what LMS test lab uses internally. Perhaps there is a uff field with
        #       this data but i havent searched yet.
        # self.localeul = pd.DataFrame(columns=['model_id', 'uffidcs', 'node_nums', 'thx', 'thy', 'thz'])

        # ... what is left is a cumbersome definition (data set #18) with the point of origin,
        #       a point on the x axis and then another point on the xz plane :S
        # Am thinking about just converting this one directly, no sense in creating another pandas
        #   table -- who will use this definition?

        
        mlist = []
        for mnum in mnums:
            sdata = self.uff_object.read_sets(mnum)
            
            leu = pd.DataFrame(columns=['model_id', 'uffidcs', 'node_nums', 'thx', 'thy', 'thz'])
            lcs = pd.DataFrame(columns=['model_id', 'uffidcs', 'node_nums', 'x1','x2','x3',
                                             'y1','y2','y3',
                                             'z1','z2','z3'])

            # # So the wors case scenario is we have a #18 field. It may be
            # #   a good idea to first calculate local coordinate axes.
            # if sdata['type'] == 18:
            #     # x-axis
            #     x = np.linalg.norm(sdata['x_point']-sdata['ref_o'])
            #
            #     # y-axis



            lcs['node_nums'] = sdata['CS_sys_labels']
            leu['node_nums'] = sdata['CS_sys_labels']
            
            # .. First calculate euler angles.
            #     (see http://nghiaho.com/?page_id=846)
            thx = []
            thy = []
            thz = []
            for r in sdata['CS_matrices']:
                thx.append(-np.arctan2(r[2,1],r[2,2])) # added minus so that behaviour is consistent with LMS
                thy.append(np.arctan2(-r[2,0], np.sqrt(r[2,1]**2+r[2,2]**2)))
                thz.append(np.arctan2(r[1,0], r[0,0]))

                
            leu['thx'] = np.asarray(thx)*180./np.pi
            leu['thy'] = np.asarray(thy)*180./np.pi
            leu['thz'] = np.asarray(thz)*180./np.pi
            
            # .. Also save local cs.
            arr = np.array(sdata['CS_matrices']).ravel()
            lcs['x1'] = arr[::9]
            lcs['x2'] = arr[1::9]
            lcs['x3'] = arr[2::9]
            lcs['y1'] = arr[3::9]
            lcs['y2'] = arr[4::9]
            lcs['y3'] = arr[5::9]
            lcs['z1'] = arr[6::9]
            lcs['z2'] = arr[7::9]
            lcs['z3'] = arr[8::9]
            
            lcs['uffidcs'] = mnum
            leu['uffidcs'] = mnum

            lcs['model_id'] = model_id
            leu['model_id'] = model_id
            
            self.localcs = self.localcs.append(lcs)
            self.localeul = self.localeul.append(leu)
            
            return True
            

    def gen_geometry_table(self, model_id, model):
        '''Read geometry.'''
        mnums = list(np.nonzero(self.uff_types[model]==2411)[0])
        mnums.extend(list(np.nonzero(self.uff_types[model]==15)[0]))
        mnums.sort()

        mnums = np.array(mnums)
        mnums += model[0]
        
        if len(mnums) == 0:
            return False
        
        mlist = []
        dlist = pd.DataFrame(columns=['model_id', 'uffid', 'node_nums', 'x', 'y', 'z', 'disp_cs', 'def_cs', 'color'])
        
        for mnum in list(mnums):
            sdata = self.uff_object.read_sets(mnum)
            
            # TODO: line below is out of place?
            mlist.append([mnum, sdata['type']])
            
            dlistt = pd.DataFrame()
            
            dlistt['x'] = sdata['x']
            dlistt['y'] = sdata['y']
            dlistt['z'] = sdata['z']
            dlistt['node_nums'] = sdata['node_nums']
            dlistt['disp_cs'] = sdata['disp_cs']
            dlistt['def_cs'] = sdata['def_cs']
            dlistt['color'] = sdata['color']
            dlistt['uffid'] = mnum
            dlistt['model_id'] = model_id
            
            dlist = dlist.append(dlistt, ignore_index=True)
            

        dlist['node_nums'] = dlist['node_nums'].astype(int)
        dlist['color'] = dlist['color'].astype(int)
        dlist['def_cs'] = dlist['def_cs'].astype(int)
        dlist['disp_cs'] = dlist['disp_cs'].astype(int)

        # TODO: I dont think i like the way the getlocalcs is initiated and then used.
        cspresent = self.getlocalcs(model_id, model)

        # TODO: Leave this for the end, when all models are scaned? Or maybe not!!
        if cspresent:
            dlist = pd.merge(dlist, self.localeul, on=['node_nums', 'model_id'])[['model_id', 'uffid', 'node_nums', 'x', 'y', 'z',
                                                                                                  'thx', 'thy', 'thz']].sort(['uffid'])
#             self.geometry = pd.merge(self.geometry, self.localeul, on='node_nums')[['uffid', 'nodenums', 'x', 'y', 'z',
#                                                                            'thx', 'thy', 'thz']].sort(['mnum'])
        else:
            dlist = dlist[['model_id', 'uffid', 'node_nums', 'x', 'y', 'z']]
            dlist['thx'] = None
            dlist['thy'] = None
            dlist['thz'] = None


        if 'geometry' in self.tables:
            self.tables['geometry'] = pd.concat([self.tables['geometry'], dlist], ignore_index=True)
        else:
            self.tables['geometry'] = dlist

        return True
        
    def gen_info_table(self, model_id, model):
        """Read info."""
        # TODO: Update here.
        mnums_151 = np.array(np.nonzero(self.uff_types[model]==151)[0])
        mnums_151 += model[0]
        mnums_164 = np.array(np.nonzero(self.uff_types[model]==164)[0])
        mnums_164 += model[0]

        # mnums = list(np.nonzero(self.uff_types[model]==151)[0])
        # mnums.extend(list(np.nonzero(self.uff_types[model]==164)[0]))
        # mnums.sort()
        #
        # mnums = np.array(mnums)
        # mnums += model[0]


        # TODO: Implement the handling of missing fields. For now, both must be present. Which makes sense in a way.
        if (len(mnums_151) == 0) or (len(mnums_164) == 0):
            # -- If no info table is present, generate a default entry,
            #  similar to what ModalData.new_model(...) does. See above.
            fields = {'db_app': 'ModalData', 'time_db_created': time.strftime("%d-%b-%y %H:%M:%S"),
                      'time_db_saved': time.strftime("%d-%b-%y %H:%M:%S"), 'program': 'OpenModal',
                      'model_name': 'Model-{}'.format(int(model_id)), 'description': 'DefaultDecription', 'units_code': 9,
                      'temp': 1, 'temp_mode': 1, 'temp_offset': 1, 'length': 1, 'force': 1,
                      'units_description': 'User unit system'}

            mlist = [[model_id, fields['model_name'], fields['description'], fields['units_code'], fields['length'],
                     fields['force'], fields['temp'], fields['temp_offset']]]

        else:
            mlist = []
            #
            # self.tables['info'] = pd.DataFrame(columns=['model_id', 'model_name', 'units_code', 'length',
            #                                             'force', 'temp', 'temp_offset'])

            for mnum_151, mnum_164 in zip(mnums_151, mnums_164):
                sdata_151 = self.uff_object.read_sets(mnum_151)
                sdata_164 = self.uff_object.read_sets(mnum_164)
                # Join the data and create one new line for info table.
                mlist.append([model_id, sdata_151['model_name'], sdata_151['description'], sdata_164['units_code'],
                              sdata_164['length'], sdata_164['force'],  sdata_164['temp'],  sdata_164['temp_offset']])

            # for mnum in mnums:
            #     sdata = self.uff_object.read_sets(mnum)
            #     for key, val in sdata.items():
            #         mlist.append([model_id, mnum, key, val])


        if 'info' in self.tables:
            self.tables['info'] = pd.concat([self.tables['info'],
                                             pd.DataFrame(mlist,
                                                          columns=['model_id', 'model_name', 'description', 'units_code',
                                                                   'length', 'force', 'temp', 'temp_offset'])],
                                                          ignore_index=True)
        else:
            self.tables['info'] = pd.DataFrame(mlist, columns=['model_id', 'model_name', 'description', 'units_code',
                                                                   'length', 'force', 'temp', 'temp_offset'])

        return True
    
    def gen_analysis_table(self, model_id, model):
        '''Read analysis data.'''
        mnums = np.nonzero(self.uff_types[model] == 55)[0]

        mnums += model[0]

        if len(mnums) == 0:
            # self.info = None
            return False
        
        mlist = []
        
        # Columns.
        sdata = self.uff_object.read_sets(mnums[0])
        cols = ['model_id', 'uffid', 'field_type']
        cols.extend([key for key in sdata if not ('r1' in key or 'r2' in key or 'r3' in key or 'node_nums' in key)])
        
        # Table for holding arrays of data.
        analysis_values = pd.DataFrame(columns=['model_id', 'uffid', 'ref_node', 'ref_dir', 'rsp_node', 'rsp_dir',
                                                'node_nums', 'r1', 'r2', 'r3'])

        concat_list = [analysis_values, ]
        for mnum in mnums:
            sdata = self.uff_object.read_sets(mnum)
            
            # Index values.
            line = [model_id, mnum, 55]
            line.extend([sdata[key] for key in cols if not ('model_id' in key or 'uffid' in key or 'field_type' in key)])
            mlist.append(line)
            
            # Array values.
            tmp_df = pd.DataFrame()
            tmp_df['node_nums'] = sdata['node_nums']
            tmp_df['r1'] = sdata['r1']
            tmp_df['r2'] = sdata['r2']
            tmp_df['r3'] = sdata['r3']
            tmp_df['model_id'] = model_id
            tmp_df['uffid'] = mnum

            concat_list.append(tmp_df)
            
        analysis_values = pd.concat(concat_list, ignore_index=True)
        concat_list = []

        if 'analysis_values' in self.tables:
            self.tables['analysis_values'] = pd.concat([self.tables['analysis_values'], analysis_values], ignore_index=True)
            self.tables['analysis_index'] = pd.concat([self.tables['analysis_index'], pd.DataFrame(mlist, columns=cols)])
        else:
            self.tables['analysis_values'] = analysis_values
            self.tables['analysis_index'] = pd.DataFrame(mlist, columns=cols)

        return True
        
    def gen_lines_table(self, model_id, model):
        """Read line data."""
        # .. Splits list on a value (0).
        def isplit(iterable, spliters):
            return [list(g) for k, g in itertools.groupby(iterable,lambda x:x in spliters) if not k]

        
        mnums = np.nonzero(self.uff_types[model] == 82)[0]
        mnums += model[0]
        
        if len(mnums) == 0:
            # self.lines = None
            return False
        
        # .. Each line is for one node, trace_id connects nodes for one element, pos indicates
        #    the order of nodes.
        cols = ['model_id', 'uffid', 'id', 'field_type', 'trace_num', 'color', 'n_nodes', 'trace_id', 'pos', 'node']
        lines = pd.DataFrame(columns=cols)
        trace_id = 0

        concat_list = [lines, ]
        for mnum in mnums:
            sdata = self.uff_object.read_sets(mnum)
            
            elements = isplit(list(sdata['lines']), [0.0])
            
            for element in elements:
                tmp_df = pd.DataFrame(columns=cols)
                tmp_df['node'] = element
                tmp_df['pos'] = range(len(element))
                tmp_df['trace_id'] = trace_id
                trace_id += 1
                
                tmp_df['uffid'] = mnum
                tmp_df['model_id'] = model_id
                tmp_df['id'] = sdata['id']
                tmp_df['field_type'] = 82
                tmp_df['trace_num'] = sdata['trace_num']
                tmp_df['color'] = sdata['color']
                tmp_df['n_nodes'] = len(element)

                concat_list.append(tmp_df)
                
            lines = pd.concat(concat_list, ignore_index=True)
            concat_list = []

        if 'lines' in self.tables:
            self.tables['lines'] = pd.concat([self.tables['lines'], lines], ignore_index=True)
        else:
            self.tables['lines'] = lines

        return True
        
if __name__ == '__main__':
    # Initialize the object - creates empty tables that can be filled.
    obj = ModalData()

    # Create new model and remember the ID. Additionally, a dictionary can be
    # provided with info values -- see docstring for ModalData.new_model().
    obj.new_model(7)

    # Fill/change tables. By hand for now.
    # ...

    # Here a uff file is imported to get some data.
    obj.import_uff(r'sampledata\shield_short.unv')

    # Export to uff. Data is appended, so make sure that the file does not exist.
    obj.export_to_uff('test_www.unv')