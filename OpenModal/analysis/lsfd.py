
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


def lsfd(lambdak, f, frf):
    """
    LSFD (Least-Squares Frequency domain) method is used in order
    to determine the residues and mode shapes from complex natural frquencies
    and the measured frequency response functions.

    :param lambdak: a vector of selected complex natural frequencies
    :param f: frequecy vector
    :param frf: frequency response functions
    :return: reconstructed FRF, modal constant(residue), lower residual, upper residual
    """

    ni = frf.shape[0]  # number of references
    no = frf.shape[1]  # number of responses
    n = frf.shape[2]   # length of frequency vector
    nmodes = lambdak.shape[0]  # number of modes

    omega = 2 * np.pi * f  # angular frequency

    # Factors in the freqeuncy response function
    b = 1 / np.subtract.outer(1j * omega, lambdak).T
    c = 1 / np.subtract.outer(1j * omega, np.conj(lambdak)).T

    # Separate complex data to real and imaginary part
    hr = frf.real
    hi = frf.imag
    br = b.real
    bi = b.imag
    cr = c.real
    ci = c.imag

    # Stack the data together in order to obtain 2D matrix
    hri = np.dstack((hr, hi))
    bri = np.hstack((br+cr, bi+ci))
    cri = np.hstack((-bi+ci, br-cr))

    ur_multiplyer = np.ones(n)
    ur_zeros = np.zeros(n)
    lr_multiplyer = -1/(omega**2)

    urr = np.hstack((ur_multiplyer, ur_zeros))
    uri = np.hstack((ur_zeros, ur_multiplyer))
    lrr = np.hstack((lr_multiplyer, ur_zeros))
    lri = np.hstack((ur_zeros, lr_multiplyer))

    bcri = np.vstack((bri, cri, urr, uri, lrr, lri))

    # Reshape 3D array to 2D for least squares coputation
    hri = hri.reshape(ni*no, 2*n)

    # Compute the modal constants (residuals) and upper and lower residuals
    uv, _, _, _ = np.linalg.lstsq(bcri.T,hri.T)

    # Reshape 2D results to 3D
    uv = uv.T.reshape(ni, no, 2*nmodes+4)

    u = uv[:, :, :nmodes]
    v = uv[:, :, nmodes:-4]
    urr = uv[:, :, -4]
    uri = uv[:, :, -3]
    lrr = uv[:, :, -2]
    lri = uv[:, :, -1]

    a = u + 1j * v  # Modal constant (residue)
    ur = urr + 1j * uri  # Upper residual
    lr = lrr + 1j * lri  # Lower residual

    # Reconstructed FRF matrix
    h = np.dot(uv, bcri)
    h = h[:, :, :n] + 1j * h[:, :, n:]

    return h, a, lr, ur
