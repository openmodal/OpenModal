
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
from OpenModal.analysis.get_simulated_sample import get_simulated_receptance
from OpenModal.fft_tools import irfft_adjusted_lower_limit
from OpenModal.analysis.utility_functions import toeplitz, prime_factors, complex_freq_to_freq_and_damp


def lscf(frf, low_lim, n, dt, weighing_type='Unity', reconstruction='LSFD'):
    """
    LSCF - Least-Squares Complex frequency domain method

    The LSCF method is an frequency-domain Linear Least Squares
    estimator optimized  for modal parameter estimation. The choice of
    the most important algorithm characteristics is based on the
    results in [1] (Section 5.3.3.) and can be summarized as:

        - Formulation: the normal equations [1]
          (Eq. 5.26: [sum(Tk - Sk.H * Rk^-1 * Sk)]*ThetaA=D*ThetaA = 0)
          are constructed for the common denominator discrete-time
          model in the Z-domain. Consequently, by looping over the
          outputs and inputs, the submatrices Rk, Sk, and Tk are
          formulated through the use of the FFT algorithm as Toeplitz
          structured (n+1) square matrices. Using complex coefficients,
          the FRF data within the frequency band of interest (FRF-zoom)
          is projected in the Z-domain in the interval of [0, 2*pi] in
          order to improve numerical conditioning. (In the case that
          real coefficients are used, the data is projected in the
          interval of [0, pi].) The projecting on an interval that does
          not completely describe the unity circle, say [0, alpha*2*pi]
          where alpha is typically 0.9-0.95. Deliberately over-modeling
          is best applied to cope with discontinuities. This is
          justified by the use of a discrete time model in the Z-domain,
          which is much more robust for a high order of the transfer
          function polynomials.

        - Solver: the normal equations can be solved for the
          denominator coefficients ThetaA by computing the Least-Squares
          (LS) or mixed Total-Least-Squares (TLS) solution. The inverse
          of the square matrix D for the LS solution is computed by
          means of a pseudo inverse operation for reasons of numerical
          stability, while the mixed LS-TLS solution is computed using
          an SVD (Singular Value Decomposition).

    Literature:
        [1] Verboven, P., Frequency-domain System Identification for
            Modal Analysis, Ph. D. thesis, Mechanical Engineering Dept.
            (WERK), Vrije Universiteit Brussel, Brussel, (Belgium),
            May 2002, (http://mech.vub.ac.be/avrg/PhD/thesis_PV_web.pdf)

        [2] Verboven, P., Guillaume, P., Cauberghe, B., Parloo, E. and
            Vanlanduit S., Stabilization Charts and Uncertainty Bounds
            For Frequency-Domain Linear Least Squares Estimators, Vrije
            Universiteit Brussel(VUB), Mechanical Engineering Dept.
            (WERK), Acoustic and Vibration Research Group (AVRG),
            Pleinlaan 2, B-1050 Brussels, Belgium,
            e-mail: Peter.Verboven@vub.ac.be, url:
            (http://sem-proceedings.com/21i/sem.org-IMAC-XXI-Conf-s02p01
            -Stabilization-Charts-Uncertainty-Bounds-Frequency-Domain-
            Linear-Least.pdf)
        [3] P. Guillaume, P. Verboven, S. Vanlanduit, H. Van der
            Auweraer, B. Peeters, A Poly-Reference Implementation of the
            Least-Squares Complex Frequency-Domain Estimator, Vrije
            Universiteit Brussel, LMS International

    :param frf: frequency response function - receptance
    :param low_lim: lower limit of the frf
    :param n: the order of the polynomial
    :param dt: time sampling interval
    :param weighing_type: weighing type (TO BE UPDATED)
    :param reconstruction: type of reconstruction - LSFD or LSCF
    :return: eigenfrequencies and the corresponding damping
    """

    n *= 2  # the poles should be complex conjugate, therefore we expect even polynomial order

    nr = frf.shape[0]  # (number of inputs) * (number of outputs)

    l = frf.shape[1]  # length of receptance

    nf = 2*(l-1)  # number of DFT frequencies (nf >> n)

    indices_s = np.arange(-n, n+1)
    indices_t = np.arange(n+1)
    # Selection of the weighting function

    # Least-Squares (LS) Formulation based on Normal Matrix
    sk = -irfft_adjusted_lower_limit(frf, low_lim, indices_s)
    t = irfft_adjusted_lower_limit(frf.real**2 + frf.imag**2,
                                  low_lim, indices_t)
    r = -(np.fft.irfft(np.ones(low_lim), n=nf))[indices_t]*nf
    r[0] += nf

    s = []
    for i in range(nr):
        s.append(toeplitz(sk[i, n:], sk[i, :n+1][::-1]))
    t = toeplitz(np.sum(t[:, :n+1], axis=0))
    r = toeplitz(r)

    sr_list = []
    for j in range(2, n+1, 2):
        d = 0
        for i in range(nr):
            rinv = np.linalg.inv(r[:j+1, :j+1])
            snew = s[i][:j+1, :j+1]
            d -= np.dot(np.dot(snew[:j+1, :j+1].T, rinv), snew[:j+1, :j+1])   # sum
        d += t[:j+1, :j+1]

        a0an1 = np.linalg.solve(-d[0:j, 0:j], d[0:j, j])
        sr = np.roots(np.append(a0an1, 1)[::-1])  # the numerator coefficients
        sr = -np.log(sr) / dt  # Z-domain (for discrete-time domain model)
        sr_list.append(sr)

    if reconstruction == 'LSFD':
        return sr_list
#     elif reconstruction == 'LSCF':
#         omegaf = np.exp(-1j * omega * ts)  # generalized transform variable in Z-domain
#         return fr, xi, r, s, theta_a, omegaf, ni, no, n, omega
    else:
        raise Exception('The reconstruction type can be either LSFD or LSCF.')


def test_lsfd():
    f, frf, modal_sim, eta_sim, f0_sim = get_simulated_receptance(
        df_Hz=1, f_start=0, f_end=5001, measured_points=8, show=False, real_mode=False)

    low_lim = 1500
    nf = (2*(len(f)-1))

    while max(prime_factors(nf)) > 5:
        f = f[:-1]
        frf = frf[:, :-1]
        nf = (2*(len(f)-1))

    df = (f[1] - f[0])
    nf = 2*(len(f)-1)
    ts = 1 / (nf * df)  # sampling period

    sr = lscf(frf, low_lim, 6, ts, weighing_type='Unity', reconstruction='LSFD')
    fr, xi = complex_freq_to_freq_and_damp(sr[-1])
    print('Eigenfrequencies\n', fr)
    print('Damping factors\n', xi)

if __name__ == '__main__':
    # test_lscf()
    test_lsfd()
