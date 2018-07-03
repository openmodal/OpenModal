
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


""" Stabilisation chart

Stabilisation charts are needed in various modal identification methods
in order to determine the real modal parameters.

History: - may 2014: stabilisation, stabilisation_plot, 
           stabilisation_test, redundant_values: Blaz Starc,
           blaz.starc@fs.uni-lj.si
"""

import numpy as np
import matplotlib.pyplot as plt
import pyqtgraph as pg

from OpenModal.analysis.get_simulated_sample import get_simulated_receptance
from OpenModal.analysis.utility_functions import complex_freq_to_freq_and_damp



def stabilisation(sr, nmax, err_fn, err_xi):
    """
    A function that computes the stabilisation matrices needed for the
    stabilisation chart. The computation is focused on comparison of
    eigenfrequencies and damping ratios in the present step 
    (N-th model order) with the previous step ((N-1)-th model order). 
    
    :param sr: list of lists of complex natrual frequencies
    :param n: maximum number of degrees of freedom
    :param err_fn: relative error in frequency
    :param err_xi: relative error in damping

    :return fn_temp eigenfrequencies matrix
    :return xi_temp: updated damping matrix
    :return test_fn: updated eigenfrequencies stabilisation test matrix
    :return test_xi: updated damping stabilisation test matrix
    
    @author: Blaz Starc
    @contact: blaz.starc@fs.uni-lj.si
    """

    # TODO: check this later for optimisation # this doffers by LSCE and LSCF
    fn_temp = np.zeros((2*nmax, nmax), dtype = 'double')
    xi_temp = np.zeros((2*nmax, nmax), dtype = 'double')
    test_fn = np.zeros((2*nmax, nmax), dtype = 'int')
    test_xi = np.zeros((2*nmax, nmax), dtype = 'int')

    for nr, n in enumerate(range(nmax)):
        fn, xi = complex_freq_to_freq_and_damp(sr[nr])
        fn, xi = redundant_values(fn, xi, 1e-3) # elimination of conjugate values in
                                                # order to decrease computation time
        if n == 1:
            # first step
            fn_temp[0:len(fn), 0:1] = fn
            xi_temp[0:len(fn), 0:1] = xi

        else:
            # Matrix test is created for comparison between present(N-th) and
            # previous (N-1-th) data (eigenfrequencies). If the value equals:
            # --> 1, the data is within relative tolerance err_fn
            # --> 0, the data is outside the relative tolerance err_fn
            fn_test = np.zeros((len(fn), len(fn_temp[:, n - 1])), dtype ='int')
            for i in range(0, len(fn)):
                for j in range(0, len(fn_temp[0:2*(n), n-1])):
                    if fn_temp[j, n-2] ==  0:
                        fn_test[i,j] = 0
                    else:
                        if np.abs((fn[i] - fn_temp[j, n-2])/fn_temp[j, n-2]) < err_fn:
                            fn_test[i,j] = 1
                        else: fn_test[i,j] = 0

            for i in range(0, len(fn)):
                test_fn[i, n - 1] = np.sum(fn_test[i, :]) # all rows are summed together

            # The same procedure as for eigenfrequencies is applied for damping
            xi_test = np.zeros((len(xi), len(xi_temp[:, n - 1])), dtype ='int')
            for i in range(0, len(xi)):
                for j in range(0, len(xi_temp[0:2*(n), n-1])):
                    if xi_temp[j, n-2]==0:
                        xi_test[i,j] = 0
                    else:
                        if np.abs((xi[i] - xi_temp[j, n-2])/xi_temp[j, n-2]) < err_xi:
                            xi_test[i,j] = 1
                        else: xi_test[i,j] = 0
            for i in range(0, len(xi)):
                test_xi[i, n - 1] = np.sum(xi_test[i, :])

            # If the frequency/damping values corresponded to the previous iteration,
            # a mean of the two values is computed, otherwise the value stays the same
            for i in range(0, len(fn)):
                for j in range(0, len(fn_temp[0:2*(n), n-1])):
                    if fn_test[i,j] == 1:
                        fn_temp[i, n - 1] = (fn[i] + fn_temp[j, n - 2]) / 2
                    elif fn_test[i,j] == 0:
                        fn_temp[i, n - 1] = fn[i]
            for i in range(0, len(fn)):
                for j in range(0, len(fn_temp[0:2*(n), n-1])):
                    if xi_test[i,j] == 1:
                        xi_temp[i, n - 1] = (xi[i] + xi_temp[j, n - 2]) / 2
                    elif xi_test[i,j] == 0:
                        xi_temp[i, n - 1] = xi[i]

    return fn_temp, xi_temp, test_fn, test_xi


def stabilisation_plot_pyqtgraph(test_fn, test_xi, fn_temp, xi_temp):
    """
    A function which shows te stabilisation chart and returns the
    stabiliesed eigenfrquencies and damping ratios.

    Input:
        test_fn - test matrix giving information about the
                  eigenfrequencies stabilisation
        test_xi - test matrix giving information about the
                  damping stabilisation
        fn_temp - eigenfrequencies matrix
        xi_temp - damping matrix
        Nmax    - highest model order
        f       - frequency vector
        FRF     - frequency response function (for plotting)

    Output:
        spots - spots for plotting in stabilisation chart

    @author: Blaz Starc
    @contact: blaz.starc@fs.uni-lj.si
    """
    a=np.argwhere((test_fn > 0) & (test_xi == 0))  # stable eigenfrequencues, unstable damping ratios
    b=np.argwhere((test_fn > 0) & (test_xi > 0))  # stable eigenfrequencies, stable damping ratios
    c=np.argwhere((test_fn == 0) & (test_xi == 0))  # unstable eigenfrequencues, unstable damping ratios
    d=np.argwhere((test_fn == 0) & (test_xi > 0))  # unstable eigenfrequencues, stable damping ratios

    spots = []
    xi = []

    for i in range(0,len(a)):
            spots.append({'pos': (fn_temp[a[i, 0], a[i, 1]], 1+a[i, 1]), 'size': 10,
                      'pen': {'color': 'w', 'width': 0.3}, 'symbol': 'd', 'brush': 'y'})
            xi.append(xi_temp[a[i, 0], a[i, 1]])


    # for i in range(0, len(c)):
    #         spots.append({'pos': (fn_temp[c[i, 0], c[i, 1]], 1+c[i, 1]), 'size': 8,
    #                       'pen': {'color': 'w', 'width': 0.3}, 'symbol': 't', 'brush': 'g'})
    # for i in range(0, len(d)):
    #         spots.append({'pos': (fn_temp[d[i, 0], d[i, 1]], 1+d[i, 1]), 'size': 8,
    #                       'pen': {'color': 'w', 'width': 0.3}, 'symbol': 's', 'brush': 'b'})

    for i in range(0, len(b)):
            spots.append({'pos': (fn_temp[b[i, 0], b[i, 1]], 1+b[i, 1]), 'size': 15,
                          'pen': {'color': 'w', 'width': 0.3}, 'symbol': '+', 'brush': 'r'})
            xi.append(xi_temp[b[i, 0], b[i, 1]])

    return spots, xi

def stabilisation_plot(test_fn, test_xi, fn_temp, xi_temp, Nmax, f, FRF):
    """
    A function which shows te stabilisation chart and returns the
    stabiliesed eigenfrquencies and damping ratios.

    Input:
        test_fn - test matrix giving information about the
                  eigenfrequencies stabilisation
        test_xi - test matrix giving information about the
                  damping stabilisation
        fn_temp - eigenfrequencies matrix
        xi_temp - damping matrix
        Nmax    - highest model order
        f       - frequency vector
        FRF     - frequency response function (for plotting)

    Output:
        stable_fn - stable eigenfrequencies values
        stable_xi - stable damping values

    @author: Blaz Starc
    @contact: blaz.starc@fs.uni-lj.si
    """
    a=np.argwhere((test_fn>0) & (test_xi==0)) # stable eigenfrequencues, unstable damping ratios
    b=np.argwhere((test_fn>0) & (test_xi>0) ) # stable eigenfrequencies, stable damping ratios
    c=np.argwhere((test_fn==0) & (test_xi==0)) # unstable eigenfrequencues, unstable damping ratios
    d=np.argwhere((test_fn==0) & (test_xi>0)) # unstable eigenfrequencues, stable damping ratios

    #import matplotlib.pyplot as plt
    plt.figure()
    for i in range(0,len(a)):
        p1=plt.scatter(fn_temp[a[i,0], a[i,1]], 1+a[i,1], s=80, c='b', marker='x')
    for i in range(0,len(b)):
        p2=plt.scatter(fn_temp[b[i,0], b[i,1]] ,1+b[i,1], s=100, c='r', marker='+')
    for i in range(0,len(c)):
        p3=plt.scatter(fn_temp[c[i,0], c[i,1]], 1+c[i,1], s=80, c='g', marker='1')
    for i in range(0,len(d)):
        p4=plt.scatter(fn_temp[d[i,0], d[i,1]], 1+d[i,1], s=80, c='m', marker='4')
    plt.plot(f, np.abs(FRF)/np.max(np.abs(FRF))*(0.8*Nmax))
    plt.xlabel('Frequency [Hz]')
    plt.ylabel('Model order')
    plt.xlim([np.min(f),np.max(f)])
    plt.ylim([-0.5, Nmax+1])
    #plt.legend([p1, p2, p3, p4], ["stable eignfr., unstable damp.",
    #                              "stable eignfr., stable damp.",
    #                              "unstable eignfr., unstable damp.",
    #                              "unstable eignfr., stable damp."])
    plt.show()
    stable_fn = np.zeros(len(b), dtype='double')
    stable_xi = np.zeros(len(b), dtype='double')
    for i in range(0,len(b)):
        stable_fn[i] = fn_temp[b[i,0],b[i,1]]
        stable_xi[i] = xi_temp[b[i,0],b[i,1]]

    return stable_fn, stable_xi

def redundant_values(omega, xi, prec):
    """
This function supresses the redundant values of frequency and damping
vectors, which are the consequence of conjugate values

Input:
    omega - eiqenfrquencies vector
    xi - damping ratios vector
    prec - absoulute precision in order to distinguish between two values

@author: Blaz Starc
@contact: blaz.starc@fs.uni-lj.si
"""
    N = len(omega)
    test_omega = np.zeros((N,N), dtype='int')
    for i in range(1,N):
        for j in range(0,i):
            if np.abs((omega[i] - omega[j])) < prec:
                test_omega[i,j] = 1
            else: test_omega[i,j] = 0
    test = np.zeros(N, dtype = 'int')
    for i in range(0,N):
        test[i] = np.sum(test_omega[i,:])
    
    omega_mod = omega[np.argwhere(test<1)]
    xi_mod = xi[np.argwhere(test<1)]
    return omega_mod, xi_mod


def test_stabilisation():
    from OpenModal.analysis.lscf import lscf
    from OpenModal.analysis.utility_functions import prime_factors

    """    Test of the Complex Exponential Method and stabilisation   """
    f, frf, modal_sim, eta_sim, f0_sim = get_simulated_receptance(
        df_Hz=1, f_start=0, f_end=5001, measured_points=8, show=False, real_mode=False)

    low_lim = 0
    nf = (2 * (len(f) - 1))
    print(nf)
    while max(prime_factors(nf)) > 5:
        f = f[:-1]
        frf = frf[:, :-1]
        nf = (2 * (len(f) - 1))
    print(nf)

    df = (f[1] - f[0])
    nf = 2 * (len(f) - 1)
    ts = 1 / (nf * df)  # sampling period

    nmax = 30
    sr = lscf(frf, low_lim, nmax, ts, weighing_type='Unity', reconstruction='LSFD')
    # N = np.zeros(nmax, dtype = 'int')
    
    err_fn = 0.001
    err_xi = 0.005

    fn_temp,xi_temp, test_fn, test_xi= stabilisation(sr, nmax, err_fn, err_xi)
    
    stable_fn, stable_xi = stabilisation_plot(test_fn, test_xi, fn_temp, xi_temp, nmax, f, frf.T)
    # print(fn_temp)


if __name__ == '__main__':
    test_stabilisation()