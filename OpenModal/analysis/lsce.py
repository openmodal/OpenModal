
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
from OpenModal.analysis.utility_functions import prime_factors


def lsce(frf, f, low_lim, nmax, dt, input_frf_type ='d', additional_timepoints=0,
         reconstruction='LSFD'):
    """ The Least-Squares Complex Exponential method (LSCE), introduced
    in [1], is the extension of the Complex Exponential method (CE) to
    a global procedure. It is therefore a SIMO method, processing
    simultaneously several IRFs obtained by exciting a structure at one
    single point and measuring the responses at several locations. With
    such a procedure, a consistent set of global parameters (natural
    frequencies and damping factors) is obtained, thus overcoming the
    variations obtained in the results for those parameters when
    applying the CE method on different IRFs.

    Literature:
    [1] Brown, D. L., Allemang, R. J. Zimmermann, R., Mergeay, M.,
        "Parameter Estimation Techniques For Modal Analysis"
        SAE Technical Paper Series, No. 790221, 1979
    [2] Ewins, D.J .; Modal Testing: Theory, practice and application,
        second edition. Reasearch Studies Press, John Wiley & Sons, 2000.
    [3] N. M. M. Maia, J. M. M. Silva, J. He, N. A. J. Lieven, R. M.
        Lin, G. W. Skingle, W. To, and A. P. V Urgueira. Theoretical
        and Experimental Modal Analysis. Reasearch Studio Press
        Ltd., 1997.
    [4] Kerschen, G., Golinval, J.-C., Experimental Modal Analysis,
        http://www.ltas-vis.ulg.ac.be/cmsms/uploads/File/Mvibr_notes.pdf

     :param frf: frequency response function array - receptance
     :param f: starting frequency
     :param low_lim: lower limit of the frf/f
     :param nmax: the maximal order of the polynomial
     :param dt: time sampling interval
     :param additional_timepoints - normed additional time points (default is
            0% added time points, max. is 1 - all time points (100%) taken into
            computation)
    :return: list of complex eigenfrequencies
    """

    no = frf.shape[0]  # number of outputs
    l = frf.shape[1]  # length of receptance
    nf = 2*(l-low_lim-1)  # number of DFT frequencies (nf >> n)

    irf = np.fft.irfft(frf[:, low_lim:], n=nf, axis=-1)  # Impulse response function

    sr_list = []
    for n in range(1, nmax+1):
        nt = int(2 * n + additional_timepoints * (irf.shape[1] - 4 * n))  # number of time points for computation

        h = np.zeros((nt * no, 2 * n), dtype ='double')  # the [h]  (time-response) matrix
        hh = np.zeros(nt*no, dtype ='double')  # {h'} vector, size (2N)x1

        for j in range(0, nt):
            for k in range(0, no):
                h[j + k*2 * n, :] = irf[k, j:j + 2 * n]  # adding values to [h] matrix
                hh[j + k * 2 * n] = irf[k, (2 * n) + j]  # adding values to {h'} vector

        # the computation of the autoregressive coefficients matrix
        beta = np.dot(np.linalg.pinv(h), -hh)
        sr = np.roots(np.append(beta, 1)[::-1])     # the roots of the polynomial
        sr = (np.log(sr)/dt).astype(complex)       # the complex natural frequency
        sr += 2 * np.pi * f * 1j  # for f_min different than 0 Hz
        sr_list.append(sr)

    if reconstruction == 'LSFD':
        return sr_list
    # elif reconstruction == 'LSCE':
    #     return fr, xi, sr, vr, irf
    else:
        raise Exception('The reconstruction type can be either LSFD or LSCE.')


# def lsce_reconstruction(n, f, sr, vr, irf, two_sided_frf = False):
#     """
#     Reconstruction of the least-squares complex exponential (CE) method.
#
#     :param n: number of degrees of freedom
#     :param f: frequency vector [Hz]
#     :param sr: the complex natural frequency
#     :param vr: the roots of the polynomial
#     :param irf: impulse response function vector
#     :return: residues and reconstructed FRFs
#
#     """
#     if two_sided_frf == False:
#         dt = 1/(len(f)*2*(f[1]-f[0]))  # time step size
#     else:
#         dt = 1/(len(f)*(f[1]-f[0]))  # time step size
#
#     v = np.zeros((2*n, 2*n), dtype = 'complex')
#     for l in range(0, 2*n):
#         for k in range(0, 2*n):
#             v[k, l] = vr[l]**k
#
#     hhh = np.zeros((2*n*len(irf)), dtype ='double') # {h''} vector
#     for j in range(0, 2*n):
#         for k in range(0, len(irf)):
#             hhh[j+ k*2*n] = irf[k, j]
#
#     a = np.zeros((len(irf), 2*n), dtype = 'complex')
#     for i in range(0, len(irf)):
#         a[i, :] = np.linalg.solve(v, -hhh[i*2*n:(i+1)*2*n])  # the computation
#                                                              # of residues
#     h = np.zeros(np.shape(irf))  # reconstructed irf
#
#     for i in range(0, len(irf)):
#         for jk in range(0, np.shape(irf)[1]):
#             h[i, jk] = np.real(np.sum(a[i,:]*np.exp(sr*jk*dt)))
#
#     return a, h


def test_lsce():
    from OpenModal.analysis.utility_functions import complex_freq_to_freq_and_damp

    """    Test of the Least-Squares Complex Exponential Method    """
    from OpenModal.analysis.get_simulated_sample import get_simulated_receptance
    import matplotlib.pyplot as plt
    
    f, frf, modal_sim, eta_sim, f0_sim = get_simulated_receptance(df_Hz=1,
            f_start=0, f_end=5001, measured_points=8, show=False, real_mode=False)

    low_lim = 100
    nf = (2*(len(f)-low_lim-1))

    while max(prime_factors(nf)) > 5:
        f = f[:-1]
        frf = frf[:, :-1]
        nf = (2*(len(f)-low_lim-1))


    df = (f[1] - f[0])
    nf = 2*(len(f)-low_lim-1)
    ts = 1 / (nf * df)  # sampling period

    n = 12
    low_lim = 100

    sr = lsce(frf, f[low_lim], low_lim, n, ts, additional_timepoints=0, reconstruction='LSFD')

    fr, xi = complex_freq_to_freq_and_damp(sr[-2])

    print("fr\n", fr)
    print("xi\n", xi)

    # A, h = lsce_reconstruction(n, f, sr, vr, irf, two_sided_frf=False)
    #
    # plt.Figure()
    # fig, figure = plt.subplots(len(irf),2)
    # for i in range(0, len(irf)):
    #     figure[i, 0].plot(np.abs(np.fft.rfft(irf[i, :])))
    #     figure[i, 0].plot(np.abs(np.fft.rfft(h[i, :])))
    #     figure[i, 0].semilogy()
    #     figure[i, 0].set_xlabel('$f$ [Hz]')
    #     figure[i, 0].set_ylabel('Magnitude [dB]')
    #
    #     figure[i, 1].plot(-180+np.abs(np.angle(np.fft.rfft(irf[i, :])))*180/np.pi)
    #     figure[i, 1].plot(-np.abs(np.angle(np.fft.rfft(h[i, :])))*180/np.pi)
    #     figure[i, 1].set_xlabel('$f$ [Hz]')
    #     figure[i, 1].set_ylabel('$Phase$ [deg]')
    # plt.show()

if __name__ == '__main__':
    test_lsce()