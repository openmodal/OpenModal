
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


import numpy as np
import pandas as pd


def add_reconstruction_to_mdd(modaldata, model_id, lambdak, modal_constants, method, analysis_id, save_points):
    """
    Add the data from reconstruction to the mdd object.

    :param modaldata: mdd object
    :param model_id: model id
    :param lambdak: complex eigenvector
    :param modal_constants: modal constants
    :param method: analysis method ('lsce', 'lscf')
    :param analysis_id: analysis id
    :return: updated mdd object
    """

    # get selected rows
    selected_rows = modaldata.tables['measurement_index'].loc[:, 'model_id'] == model_id

    # delete old data for the selected index
    delete_old_data_model_id = modaldata.tables['analysis_index'].loc[:, 'model_id'] == model_id
    delete_old_data_analysis_id = modaldata.tables['analysis_index'].loc[:, 'analysis_id'] == analysis_id

    delete_old_data = delete_old_data_model_id & delete_old_data_analysis_id

    modaldata.tables['analysis_index'] = modaldata.tables['analysis_index'][~delete_old_data]

    # number of selected modes
    nmodes = len(lambdak)

    # modal_constants = modal_constants

    # Fill the anlysis_index DataFrame
    df_new = pd.DataFrame(np.nan * np.empty((nmodes, modaldata.tables['analysis_index'].shape[1])),
                          columns=modaldata.tables['analysis_index'].columns)
    df_new.loc[:, 'eig'] = lambdak
    df_new.loc[:, 'analysis_id'] = analysis_id
    df_new.loc[:, 'model_id'] = model_id * np.ones(nmodes)
    df_new.loc[:, 'analysis_method'] = method

    mode_n = np.arange(nmodes) + 1
    df_new.loc[:, 'mode_n'] = mode_n
    df_new.loc[:, 'spots'] = save_points

    uffid_start = np.max(modaldata.tables['analysis_index'].loc[:, 'uffid'])
    uffid_start = 0 if np.isnan(uffid_start) else uffid_start
    uffid = np.arange(nmodes) + 1 + uffid_start  # TODO: this should be deleted, when Miha commits the changes to animation.py
    df_new.loc[:, 'uffid'] = uffid  # TODO: this should be deleted, when Miha commits the changes to animation.py

    modaldata.tables['analysis_index'] = modaldata.tables['analysis_index'].append(df_new,
                                                                                   ignore_index=True)
    # delete any previous analysis data
    rows_to_delete_model_id = modaldata.tables['analysis_values'].loc[:, 'model_id'] == model_id
    rows_to_delete_analysis_id = modaldata.tables['analysis_values'].loc[:, 'analysis_id'] == analysis_id

    rows_to_delete = rows_to_delete_model_id & rows_to_delete_analysis_id

    modaldata.tables['analysis_values'] = modaldata.tables['analysis_values'][~rows_to_delete]

    # Determines wheather to animate reference or response nodes
    display_rsp_or_ref = determine_display_points(modaldata)

    # get the information about which index corresponds to translational movement: x, y or z
    xref = modaldata.tables['measurement_index'][selected_rows].loc[:, display_rsp_or_ref[1]] == 1
    yref = modaldata.tables['measurement_index'][selected_rows].loc[:, display_rsp_or_ref[1]] == 2
    zref = modaldata.tables['measurement_index'][selected_rows].loc[:, display_rsp_or_ref[1]] == 3

    xref = np.tile(xref, nmodes)
    yref = np.tile(yref, nmodes)
    zref = np.tile(zref, nmodes)

    # get the information about which index corresponds to rotational movement: xy, xz or yz
    xyref = modaldata.tables['measurement_index'][selected_rows].loc[:, display_rsp_or_ref[1]] == 4
    xzref = modaldata.tables['measurement_index'][selected_rows].loc[:, display_rsp_or_ref[1]] == 5
    yzref = modaldata.tables['measurement_index'][selected_rows].loc[:, display_rsp_or_ref[1]] == 6

    xyref = np.tile(xyref, nmodes)
    xzref = np.tile(xzref, nmodes)
    yzref = np.tile(yzref, nmodes)

    # chose the value for the reference (to compute the modal shapes)
    # index = np.unravel_index(np.argmax(np.sum(np.abs(modal_constants), axis=2)),
    #                          dims=modal_constants.shape[:2])  # TODO: maybe max min would be better
    # reference = np.sqrt(modal_constants[index])  # Modal constant `a` with largest value is choosen due to division.
    #
    # # Computation of eigenvectors
    # r = modal_constants / reference

    r = modal_constants

    # Table for converting measurement index to analysis index
    ref_rsp = modaldata.tables['measurement_index'][selected_rows].loc[:, ['ref_node', 'ref_dir', 'rsp_node', 'rsp_dir']]
    node_nums = measurement_index_to_analysis_index(ref_rsp, display_rsp_or_ref[:2])

    # Repeat the node_nums according to the number of references
    rsp = display_rsp_or_ref[3]
    rsp = np.tile(rsp, display_rsp_or_ref[2])

    node_nums = pd.concat([node_nums]*display_rsp_or_ref[2])
    # node_nums['node'] = rsp
    # node_nums['dir'] = rsp.imag

    # Total number of measured points
    nr_of_data = node_nums.shape[0]

    # Fill the analysis_values DataFrame
    df_new = pd.DataFrame(np.nan * np.empty((nr_of_data * nmodes, modaldata.tables['analysis_values'].shape[1])),
                          columns=modaldata.tables['analysis_values'].columns)

    df_new.loc[:, 'model_id'] = np.tile(model_id, nr_of_data * nmodes)

    df_new.loc[:, 'analysis_id'] = analysis_id

    df_new.loc[:, 'analysis_method'] = method

    df_new.loc[:, 'r1'] = np.zeros(nr_of_data * nmodes, dtype=complex)
    df_new.loc[:, 'r2'] = np.zeros(nr_of_data * nmodes, dtype=complex)
    df_new.loc[:, 'r3'] = np.zeros(nr_of_data * nmodes, dtype=complex)

    df_new.loc[:, 'r4'] = np.zeros(nr_of_data * nmodes, dtype=complex)
    df_new.loc[:, 'r5'] = np.zeros(nr_of_data * nmodes, dtype=complex)
    df_new.loc[:, 'r6'] = np.zeros(nr_of_data * nmodes, dtype=complex)

    eigenvector = r.T.reshape(-1)

    df_new.loc[np.tile(node_nums.loc[:, 'r1'].values, nmodes), 'r1'] = eigenvector[xref]
    df_new.loc[np.tile(node_nums.loc[:, 'r2'].values, nmodes), 'r2'] = eigenvector[yref]
    df_new.loc[np.tile(node_nums.loc[:, 'r3'].values, nmodes), 'r3'] = eigenvector[zref]
    df_new.loc[np.tile(node_nums.loc[:, 'r4'].values, nmodes), 'r4'] = eigenvector[xyref]
    df_new.loc[np.tile(node_nums.loc[:, 'r5'].values, nmodes), 'r5'] = eigenvector[xzref]
    df_new.loc[np.tile(node_nums.loc[:, 'r6'].values, nmodes), 'r6'] = eigenvector[yzref]

    df_new.loc[:, 'node_nums'] = np.tile(node_nums.index.values, nmodes)
    # df_new.loc[:, 'node_nums'].unique()
    # df_new.loc[:, 'node'] = np.tile(node_nums['node'].values, nmodes)
    # df_new.loc[:, 'dir'] = node_nums['dir'].values
    # df_new.loc[:, ['ref_node', 'ref_dir', 'rsp_node', 'rsp_dir']] = np.concatenate([ref_rsp.values]*nmodes)

    uffid = np.repeat(uffid, len(node_nums))  # TODO: this should be deleted, when Miha commits the changes to animation.py

    df_new.loc[:, 'uffid'] = uffid  # TODO: this should be deleted, when Miha commits the changes to animation.py

    df_new.loc[:, 'mode_n'] = np.repeat(mode_n, len(node_nums))

    test = df_new.loc[:, ['node_nums', 'mode_n', 'r1', 'r2', 'r3', 'r4', 'r5', 'r6']]

    test['r1c'] = test.r1.values.imag
    test['r2c'] = test.r2.values.imag
    test['r3c'] = test.r3.values.imag
    test['r4c'] = test.r4.values.imag
    test['r5c'] = test.r5.values.imag
    test['r6c'] = test.r6.values.imag

    test.r1 = test.r1.values.real
    test.r2 = test.r2.values.real
    test.r3 = test.r3.values.real
    test.r4 = test.r4.values.real
    test.r5 = test.r5.values.real
    test.r6 = test.r6.values.real

    test = test.groupby(['node_nums', 'mode_n']).sum()

    test.r1 = test.r1 + 1j * test.r1c
    test.r2 = test.r2 + 1j * test.r2c
    test.r3 = test.r3 + 1j * test.r3c
    test.r4 = test.r4 + 1j * test.r4c
    test.r5 = test.r5 + 1j * test.r5c
    test.r6 = test.r6 + 1j * test.r6c

    test = test.loc[:, ['r1', 'r2', 'r3', 'r4', 'r5', 'r6']]

    test = test.reset_index()

    test['model_id'] = model_id
    test['analysis_id'] = analysis_id
    test['analysis_method'] = method

    modaldata.tables['analysis_values'] = modaldata.tables['analysis_values'].append(test,
                                                                                     ignore_index=True)
    return modaldata


def determine_display_points(modaldata_object):
    """
    Determines wheter to display reference or respnse nodes
    :param modaldata_object: modaldata_object
    :return: A tuple containing two strings and the number of references.
    """
    nodes = modaldata_object.tables['measurement_index'].loc[:, ['ref_node', 'ref_dir', 'rsp_node', 'rsp_dir']]
    nodes = nodes.astype(int)

    ref = np.unique(nodes.loc[:, 'ref_node'] + 1j * nodes.loc[:, 'ref_dir'])
    rsp = np.unique(nodes.loc[:, 'rsp_node'] + 1j * nodes.loc[:, 'rsp_dir'])

    if len(rsp) > len(ref):
        return 'rsp_node', 'rsp_dir', len(ref), np.unique(nodes.loc[:, 'rsp_node'])
    else:
        return 'ref_node', 'ref_dir', len(rsp), np.unique(nodes.loc[:, 'ref_node'])


def measurement_index_to_analysis_index(ref_and_rsp_node, display_ref_rsp):
    """
    Transforms measurement indices (from measurement_index table) into analysis
    indices. This transforms the (node number, direction) column description
    into 2D shape, with columns as modal vectors (r1, r2, r3, r4, r5, r6) and
    rows as node numbers.

    :param ref_and_rsp_node: pandas DataFrame containing ref_node, ref_dir,
                             rsp_node and rsp_dir
    :param display_ref_rsp: Tuple for determining whether reference or
                            response nodes should be animated
                            (e. g. ('ref_node', 'ref_dir'))
    :return: 2D boolean arra9y.
    """
    df = pd.DataFrame(index=ref_and_rsp_node.loc[:, display_ref_rsp[0]].unique(), columns=np.arange(1, 7))
    df.iloc[:, :] = np.zeros_like(df, dtype=bool)

    # prepare indices
    indices = ref_and_rsp_node.loc[:, display_ref_rsp].values
    indices = indices[:, 0] + 1j * indices[:, 1]

    for i in indices:
        df.loc[i.real, i.imag] = True

    df.columns = ['r1', 'r2', 'r3', 'r4', 'r5', 'r6']

    return df


def save_analysis_settings(settings, model_id, analysis_id, method='lscf', f_min=1, f_max=100, nmax=30, err_fn=1e-2,
                           err_xi=5e-2):
    """
        Saves analysis settings to mdd file.

        :param settings: modaldata.tables['analysis_settings']
        :param model_id: model id
        :param analysis_id: analysis id
        :param method: identification method
        :param f_min: minimum frequency
        :param f_max: maximum frequency
        :param nmax: maximal model order used by the identification method
        :param err_fn: allowed natural frequency error in stabilisation diagrams
        :param err_xi: damping error in stabilisation diagrams
        :return: updated analysis settings data-table
        """

    save = [[model_id, analysis_id, method, f_min, f_max, nmax, err_fn, err_xi]]

    select_model_id = settings.loc[:, 'model_id'] == model_id
    select_analysis_id = settings.loc[:, 'analysis_id'] == analysis_id

    select_model = select_model_id & select_analysis_id

    if sum(select_model) == 1:
        settings[select_model] = save
    else:
        settings = settings.append(pd.DataFrame(save, columns=settings.columns), ignore_index=True)

    return settings


def save_stabilisation_spots(analysis_stabilisation, data):
    """
    Saves stabilisation spots data

    :param analysis_stabilisation: analysis_stabilisation mdd table
    :param data: [model_id, analysis_id, method, pos, size,
                  pen_color, pen_width, symbol, brush, damp]
    :return: updated analysis_stabilisation mdd table
    """

    model_id = data[0][0]
    analysis_id = data[0][1]
    # analysis_method = data[0][2]  # only needed when loading

    select_model_id = analysis_stabilisation.loc[:, 'model_id'] == model_id
    select_analysis_id = analysis_stabilisation.loc[:, 'analysis_id'] == analysis_id

    delete_old_data = select_model_id & select_analysis_id

    analysis_stabilisation = analysis_stabilisation[~delete_old_data]

    data = pd.DataFrame(data, columns=analysis_stabilisation.columns)
    data.loc[:, ['model_id', 'analysis_id']] = data.loc[:, ['model_id', 'analysis_id']].astype(int)
    data.loc[:, ['size', 'pen_width', 'damp']] = data.loc[:, ['size', 'pen_width', 'damp']].astype(float)
    data.loc[:, 'pos'] = [complex(i) for i in (data.loc[:, 'pos'])]

    analysis_stabilisation = analysis_stabilisation.append(data, ignore_index=True)

    return analysis_stabilisation
