
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


"""
Some functions that will probably be used in different places,
such as euler/direction vector conversion.
"""

import numpy as np
import pandas as pd


def zyx_euler_to_rotation_matrix(th):
    """Convert the ZYX order (the one LMS uses) Euler
        angles to rotation matrix. Angles are given
        in radians.

        Note:
            Actually Tait-Bryant angles.
        """
    # -- Calculate sine and cosine values first.
    sz, sy, sx = [np.sin(value) for value in th]
    cz, cy, cx = [np.cos(value) for value in th]

    # -- Create and populate the rotation matrix.
    rotation_matrix = np.zeros((3, 3), dtype=float)

    rotation_matrix[0, 0] = cy * cz
    rotation_matrix[0, 1] = cz * sx * sy - cx * sz
    rotation_matrix[0, 2] = cx * cz * sy + sx * sz
    rotation_matrix[1, 0] = cy * sz
    rotation_matrix[1, 1] = cx * cz + sx * sy * sz
    rotation_matrix[1, 2] = -cz * sx + cx * sy * sz
    rotation_matrix[2, 0] = -sy
    rotation_matrix[2, 1] = cy * sx
    rotation_matrix[2, 2] = cx * cy

    return rotation_matrix


def get_unique_rows(array):
    """
    Return unique rows of a numpy array.
    :param array: NumPy array
    :return: Array of unique rows
    """
    b = np.ascontiguousarray(array).view(np.dtype((np.void, array.dtype.itemsize * array.shape[1])))
    return np.unique(b).view(array.dtype).reshape(-1, array.shape[1])


def unique_row_indices(a):
    """
    Assign unique row indices of an Nx2 array a.
    :param a: (N, 2) array
    :return: an (N,) array containing unique row indices
    :return: number of unique rows
    """
    a = a[:, 0] + 1j*a[:, 1]
    a = a.astype(complex)
    unique, inv = np.unique(a, return_inverse=True)
    return inv, len(unique)


def get_frf_from_mdd(measurement_values, measurement_index):
    """
    Creates a 3D FRF array from the mdd file.

    The dimensions of the new array are (number of inputs, number of outputs, length of data)

    :param measurement_values: measurement values table of the mdd file
    :param measurement_index: measurement index table of the mdd file
    :return: FRF array
    """
    # Get unique row indices from reference nodes and reference directions
    inputs, ni = unique_row_indices(measurement_index.loc[:, ['ref_node', 'ref_dir']].values)

    # Get unique row indices from response nodes and response directions
    outputs, no = unique_row_indices(measurement_index.loc[:, ['rsp_node', 'rsp_dir']].values)

    # FRF length
    if measurement_index.shape[0] > 0:
        frf_len = np.sum(measurement_values.loc[:, 'measurement_id'] == measurement_index.iloc[0].loc['measurement_id'])
        f = measurement_values.loc[:, 'frq'][
            measurement_values.loc[:, 'measurement_id'] == 0].values
    else:
        frf_len = 0
        f = None

    # Create the 3D frf array
    frf = np.empty((ni, no, frf_len), dtype=complex)
    for i, meas_id in enumerate(measurement_index.loc[:, 'measurement_id']):
        frf[inputs[i], outputs[i]] = measurement_values.loc[:, 'amp'][
            measurement_values.loc[:, 'measurement_id'] == meas_id]

    return frf, f


def get_frf_type(num_denom_type):
    """
    Get frf type from reference and response types. The supported frf types are:
    - accelerance
    - mobility
    - receptance

    :param num_denom_type: a numpy array containing response and reference
    type in columns. The type is defined according to Universal File Format.
    :return : a pandas dataframe with frf types
    """

    frf_type = pd.DataFrame(np.nan*np.zeros(num_denom_type.shape[0]), columns=['frf_type'], dtype=str)

    if frf_type.shape[0] > 0:
        for i, row in enumerate(num_denom_type):
            num_type = row[0]
            denom_type = row[1]

            if num_type == 12 and denom_type == 13:
                frf_type.loc[i, 'frf_type'] = 'a'
            elif num_type == 11 and denom_type == 13:
                frf_type[i].loc[i, 'frf_type'] = 'v'
            elif num_type == 8 and denom_type == 13:
                frf_type[i].loc[i, 'frf_type'] = 'd'

            # raise Exception('FRF type not recognised. Currently supported FRF types are: '
            #                 'accelerance, mobility and receptance.')
    else:
        pass

    return frf_type
