
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


"""Module for handling keys used in OpenModal.

    Typical use:
         keys['abscissa_axis_units_lab']['3']

    'key': {
        '3': '',    # acronym up to 3 characters
        '15': '',   # short description up to 15 characters
        'desc': ''  # full description
    }

"""

keys = {
    'abscissa_axis_units_lab': {
        '3': 'x',
        '15': 'x axis units',
        'desc': 'label for the units on the abscissa',
    },

    'abscissa_force_unit_exp': {
        '3': 'exp',
        '15': 'unit exponent',
        'desc': 'exponent for the force unit on the abscissa',
    },

    'abscissa_inc': {
        '3': 'inc',
        '15': 'x axis incr.',
        'desc': 'abscissa increment; 0 if spacing uneven',
    },

    'abscissa_len_unit_exp': {
        '3': 'exp',
        '15': 'x axis unit exp',
        'desc': 'exponent for the length unit on the abscissa',
    },

    'abscissa_min': {
        '3': 'min',
        '15': 'x axis minimum',
        'desc': 'abscissa minimum',
    },

    'abscissa_spacing': {
        '3': 'spa',
        '15': 'x axis spacing',
        'desc': 'abscissa spacing; 0=uneven, 1=even',
    },

    'abscissa_spec_data_type': {
        '3': 'typ',
        '15': 'x axis type',
        'desc': 'abscissa specific data type',
    },

    'abscissa_temp_unit_exp': {
        '3': 'exp',
        '15': 'x axis unit exp',
        'desc': 'exponent for the temperature unit on the abscissa',
    },

    'analysis_id': {
        '3': 'aid',
        '15': 'analysis ID',
        'desc': 'Analysis ID is used to distinguish between different analyses done in analysis tab.',
    },

    'analysis_type': {
        '3': 'typ',
        '15': 'analysis type',
        'desc': 'analysis type number; currently only normal mode (2), complex eigenvalue first order (displacement) (3), frequency response and (5) and complex eigenvalue second order (velocity) (7) are supported',
    },

    'binary': {
        '3': 'bin',
        '15': 'Binary/ASCII',
        'desc': '1 for Binary, 0 for ASCII format type',
    },

    'byte_ordering': {
        '3': 'byt',
        '15': 'byte ordering',
        'desc': 'byte ordering',
    },

    'cmif': {
        '3': 'MIF',
        '15': 'CMIF',
        'desc': 'The Complex Mode Indicator Function',
    },

    'color': {
        '3': 'col',
        '15': 'color',
        'desc': 'color number',
    },

    'cyl_thz': {
        '3': 'thz',
        '15': 'x to y',
        'desc': 'first Euler rotation', #for cylindrical coordinate system
    },

    'damp_err': {
        '3': 'err',
        '15': 'damp. err.',
        'desc': 'Damping error',
    },

    'data': {
        '3': 'dat',
        '15': 'data',
        'desc': 'data array',
    },

    'data_ch': {
        '3': 'dat',
        '15': 'data char. nr.',
        'desc': 'data-characteristic number',
    },

    'data_type': {
        '3': 'typ',
        '15': 'data type',
        'desc': 'data type number; 2 = real data, 5 = complex data',
    },

    'date_db_created': {
        '3': 'crt',
        '15': 'date DB created',
        'desc': 'date database created',
    },

    'date_db_saved': {
        '3': 'sav',
        '15': 'date DB saved',
        'desc': 'date database saved',
    },

    'date_file_written': {
        '3': 'wrt',
        '15': 'file written',
        'desc': 'date file was written',
    },

    'db_app': {
        '3': 'nam',
        '15': 'DB app name',
        'desc': 'name of the application that created the database',
    },

    'def_cs': {
        '3': 'cs',
        '15': 'def. cs numbers ',
        'desc': 'n deformation cs numbers',
    },  # what is this? (Blaz)

    'description': {
        '3': 'des',
        '15': 'description',
        'desc': 'description of the model',
    },

    'disp_cs': {
        '3': 'cs',
        '15': 'disp cs numbers',
        'desc': 'n displacement cs numbers',
    },  # what is this? (Blaz)

    'eig': {
        '3': 'eig',
        '15': 'eigen frequency',
        'desc': 'eigen frequency (complex number); applicable to analysis types 3 and 7 only',
    },
    'eig_real': {
        '3': 'ere',
        '15': 'eigen freq [Hz]',
        'desc': 'real part of eigen frequency; applicable to analysis types 3 and 7 only',
    },
    'eig_xi': {
        '3': 'exi',
        '15': 'damping factor [/]',
        'desc': 'damping factor; applicable to analysis types 3 and 7 only',
    },
    'element_descriptor': {
        '3': 'eds',
        '15': 'element type',
        'desc': 'description of element type',
    },

    'element_id': {
        '3': 'eid',
        '15': 'element id',
        'desc': 'id number of an element',
    },

    'file_type': {
        '3': 'typ',
        '15': 'file type',
        'desc': 'file type string',
    },

    'force': {
        '3': 'for',
        '15': 'force',
        'desc': 'force factor',
    },

    'fp_format': {
        '3': 'fp',
        '15': 'fp format',
        'desc': 'floating-point format',
    },

    'freq': {
        '3': 'fre',
        '15': 'frequency',
        'desc': 'frequency (Hz); applicable to analysis types 2 and 5 only',
    },

    'freq_err': {
        '3': 'err',
        '15': 'freq. err.',
        'desc': 'frequency error',
    },


    'freq_max': {
        '3': 'max',
        '15': 'max. freq.',
        'desc': 'maximal frequency',
    },


    'freq_min': {
        '3': 'min',
        '15': 'min. freq.',
        'desc': 'Minimal frequency',
    },



    'freq_step_n': {
        '3': 'stp',
        '15': 'freq. step nr.',
        'desc': 'frequency step number; applicable to analysis type 5 only',
    },

    'frf': {
        '3': 'FRF',
        '15': 'FRF',
        'desc': 'Frequency Response Function',
    },

    'func_type': {
        '3': 'fun',
        '15': 'function type',
        'desc': 'function type; only 1, 2, 3, 4 and 6 are supported',
    },

    'id': {
        '3': 'id',
        '15': 'id',
        'desc': 'id string',
    },

    'id1': {
        '3': 'id1',
        '15': 'id1',
        'desc': 'id1 string',
    },

    'id2': {
        '3': 'id2',
        '15': 'id2',
        'desc': 'id2 string',
    },

    'id3': {
        '3': 'id3',
        '15': 'id3',
        'desc': 'id3 string',
    },

    'id4': {
        '3': 'id4',
        '15': 'id4',
        'desc': 'id4 string',
    },

    'id5': {
        '3': 'id5',
        '15': 'id5',
        'desc': 'id5 string',
    },

    'length': {
        '3': 'len',
        '15': 'length',
        'desc': 'length factor',
    },

    'lines': {
        '3': 'lin',
        '15': 'line numbers',
        'desc': 'list of n line numbers',
    },

    'load_case': {
        '3': 'loa',
        '15': 'load case',
        'desc': 'load case number',
    },

    'load_case_id': {
        '3': 'loa',
        '15': 'load case id',
        'desc': 'id number for the load case',
    },

    'max_order': {
        '3': 'max',
        '15': 'max. order',
        'desc': 'maximum model order',
    },

    'modal_a': {
        '3': 'mod',
        '15': 'modal a',
        'desc': 'modal-a (complex number); applicable to analysis types 3 and 7 only',
    },

    'modal_b': {
        '3': 'mod',
        '15': 'modal b',
        'desc': 'modal-b (complex number); applicable to analysis types 3 and 7 only',
    },

    'modal_damp_his': {
        '3': 'dmp',
        '15': 'modal damp. his',
        'desc': 'modal hysteretic damping ratio; applicable to analysis type 2 only',
    },

    'modal_damp_vis': {
        '3': 'dmp',
        '15': 'modal damp vis',
        'desc': 'modal viscous damping ratio; applicable to analysis type 2 only',
    },

    'modal_m': {
        '3': 'mod',
        '15': 'modal mass',
        'desc': 'modal mass; applicable to analysis type 2 only',
    },

    'mode_n': {
        '3': 'mod',
        '15': 'mode number',
        'desc': 'mode number; applicable to analysis types 2, 3 and 7 only',
    },

    'model_id': {
        '3': 'mid',
        '15': 'model ID',
        'desc': 'id number of the model',
    },

    'model_name': {
        '3': 'mod',
        '15': 'model name',
        'desc': 'the name of the model',
    },

    'model_type': {
        '3': 'mod',
        '15': 'model type',
        'desc': 'model type number',
    },

    'n_ascii_lines': {
        '3': 'nr',
        '15': 'ascii lines nr',
        'desc': 'number of ascii lines',
    },

    'n_bytes': {
        '3': 'nr',
        '15': 'nr of bytes',
        'desc': 'number of bytes',
    },

    'n_data_per_node': {
        '3': 'nr',
        '15': 'nr of data',
        'desc': 'number of data per node (DOFs)',
    },

    'n_nodes': {
        '3': 'nr',
        '15': 'nr of nodes',
        'desc': 'number of nodes',
    },

    'nr_of_nodes': {
        '3': 'nrn',
        '15': 'node count',
        'desc': 'number of nodes per element',
    },

    'node_nums': {
        '3': 'nr',
        '15': 'node nums',
        'desc': 'node numbers',
    },

    'num_pts': {
        '3': 'pts',
        '15': 'nr of pts',
        'desc': 'number of data pairs for uneven abscissa or number of data values for even abscissa',
    },

    'ord_data_type': {
        '3': 'typ',
        '15': 'ord data type',
        'desc': 'ordinate data type',
    },

    'orddenom_axis_units_lab': {
        '3': 'y',
        '15': 'y axis units',
        'desc': 'label for the units on the ordinate denominator',
    },

    'orddenom_force_unit_exp': {
        '3': 'exp',
        '15': 'unit exponent',
        'desc': 'exponent for the force unit on the ordinate denominator',
    },

    'orddenom_len_unit_exp': {
        '3': 'exp',
        '15': 'y axis unit exp',
        'desc': 'exponent for the length unit on the ordinate denominator',
    },

    'orddenom_spec_data_type': {
        '3': 'typ',
        '15': 'y axis type',
        'desc': 'ordinate denominator specific data type',
    },

    'orddenom_temp_unit_exp': {
        '3': 'exp',
        '15': 'y axis unit exp',
        'desc': 'exponent for the temperature unit on the ordinate denominator',
    },

    'ordinate_axis_units_lab': {
        '3': 'y',
        '15': 'y axis units',
        'desc': 'label for the units on the ordinate',
    },

    'ordinate_force_unit_exp': {
        '3': 'exp',
        '15': 'unit exponent',
        'desc': 'exponent for the force unit on the ordinate',
    },

    'ordinate_len_unit_exp': {
        '3': 'exp',
        '15': 'unit exponent',
        'desc': 'exponent for the length unit on the ordinate',
    },

    'ordinate_spec_data_type': {
        '3': 'typ',
        '15': 'y axis type',
        'desc': 'ordinate specific data type',
    },

    'ordinate_temp_unit_exp': {
        '3': 'exp',
        '15': 'unit exponent',
        'desc': 'exponent for the temperature unit on the ordinate',
    },

    'phi': {
        '3': 'phi',
        '15': 'phi',
        'desc': 'phi coordinate of cylindrical coordinate system',
    },

    'program': {
        '3': 'pro',
        '15': 'program',
        'desc': 'name of the program',
    },

    'r': {
        '3': 'r',
        '15': 'r',
        'desc': 'r coordinate of cylindrical coordinate system',
    },

    'r1': {
        '3': 'r1',
        '15': 'r1',
        'desc': 'response array for each DOF; when response is complex only r1 through r3 will be used',
    },

    'ref_dir': {
        '3': 'ref',
        '15': 'ref dir',
        'desc': 'reference direction number',
    },

    'ref_ent_name': {
        '3': 'ref',
        '15': 'ref ent name',
        'desc': 'entity name for the reference',
    },

    'ref_node': {
        '3': 'ref',
        '15': 'ref node',
        'desc': 'reference node number',
    },

    'rsp_dir': {
        '3': 'rsp',
        '15': 'rsp dir',
        'desc': 'response direction number',
    },

    'rsp_ent_name': {
        '3': 'rsp',
        '15': 'rsp ent name',
        'desc': 'entity name for the response',
    },

    'rsp_node': {
        '3': 'rsp',
        '15': 'rsp node',
        'desc': 'response node number',
    },

    'spec_data_type': {
        '3': 'spe',
        '15': 'spec data type',
        'desc': 'specific data type number',
    },

    'sum': {
        '3': 'SUM',
        '15': 'sum of elements',
        'desc': 'sum of elements',
    },

    'temp': {
        '3': 'tem',
        '15': 'temp',
        'desc': 'temperature factor',
    },

    'temp_mode': {
        '3': 'tem',
        '15': 'temp_mode',
        'desc': 'temperature mode number',
    },

    'temp_offset': {
        '3': 'tem',
        '15': 'temp offset',
        'desc': 'temperature-offset factor',
    },

    'thx': {
        '3': 'thx',
        '15': 'y to z',
        'desc': 'third Euler rotation',
    },

    'thy': {
        '3': 'thy',
        '15': 'x to z',
        'desc': 'second Euler rotation',
    },

    'thz': {
        '3': 'thz',
        '15': 'x to y',
        'desc': 'first Euler rotation',
    },

    'time_db_created': {
        '3': 'tim',
        '15': 'time DB created',
        'desc': 'time database was created',
    },

    'time_db_saved': {
        '3': 'tim',
        '15': 'time DB saved',
        'desc': 'time database was saved',
    },

    'time_file_written': {
        '3': 'tim',
        '15': 'time file writt',
        'desc': 'time file was written',
    },

    'trace_num': {
        '3': 'tra',
        '15': 'trace nr',
        'desc': 'number of the trace',
    },

    'type': {
        '3': 'typ',
        '15': 'type',
        'desc': 'type number = 55',
    },

    'uffid': {
        '3': 'ufd',
        '15': 'uff id',
        'desc': 'identification number of uff dataset',
    },

    'units_code': {
        '3': 'uni',
        '15': 'units code',
        'desc': 'units code number',
    },

    'units_description': {
        '3': 'uni',
        '15': 'units descr.',
        'desc': 'units description',
    },

    'ver_num': {
        '3': 'ver',
        '15': 'version',
        'desc': 'version number',
    },

    'version_db1': {
        '3': 'ver',
        '15': 'version DB1 str',
        'desc': 'version string 1 of the database',
    },

    'version_db2': {
        '3': 'ver',
        '15': 'version DB2 str',
        'desc': 'version string 2 of the database',
    },

    'x': {
        '3': 'x',
        '15': 'x',
        'desc': 'abscissa array',
    },

    'y': {
        '3': 'y',
        '15': 'y',
        'desc': 'y-coordinates of the n nodes',
    },

    'z': {
        '3': 'z',
        '15': 'z',
        'desc': 'z-coordinates of the n nodes',
    },

    'z_axis_axis_units_lab': {
        '3': 'z',
        '15': 'z axis units',
        'desc': 'label for the units on the z axis',
    },

    'z_axis_force_unit_exp': {
        '3': 'exp',
        '15': 'unit exponent',
        'desc': 'exponent for the force unit on the z axis',
    },

    'z_axis_len_unit_exp': {
        '3': 'exp',
        '15': 'unit exponent',
        'desc': 'exponent for the length unit on the z axis',
    },

    'z_axis_spec_data_type': {
        '3': 'typ',
        '15': 'z axis type',
        'desc': 'z-axis specific data type',
    },

    'z_axis_temp_unit_exp': {
        '3': 'exp',
        '15': 'unit exponent',
        'desc': 'exponent for the temperature unit on the z axis',
    },

    'z_axis_value': {
        '3': 'val',
        '15': 'z axis value',
        'desc': 'z axis value',
    },
}

if __name__ == '__main__':
    for k, v in keys.items():
        print(k, v)
