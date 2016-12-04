
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


"""Module for creating FRF in frequency domain.

Classes:
    class FRF: It creates FRF
"""


import numpy as np

import matplotlib.pyplot as plt

from uff import UFF



class FRF:
    """It creates FRF and FRF matrix from modal parameters and M,K,C matrices.
    
    Use frf_mp to generate FRF from modal parameters.
    Use matrixMCK to generate FRF matrix from M, K and C matrix
    
    Arguments: 
        f_min - the low limit of frequency range 
        f_max - the high limit of frequency range
        f_res - frequency resolution
    """  
    def __init__(self, f_min, f_max, f_res):
        self.f_res = f_res
        self.f_min = f_min
        self.f_max = f_max
        self.freq = np.arange(f_min, f_max, self.f_res)
        self.om = np.array(2 * np.pi * self.freq)
    
        
    def frf_mp(self, A, nfreq, mi, residues='False', type='a'):
        """generates FRF from modal parameters  
    
        Arguments:
            A - Modal constants of the considering FRF.
            nfreq - natural frequencies in Hz
            mi - modal dampings
            residues - if 'True' the residues of lower and higher residues are taken into account
            type - type of FRF function: 
                                    -'d'- receptance
                                    -'v'- mobility
                                    -'a'- accelerance   
        """ 
        self.A = np.array(A)
        self.nom = np.array(2 * np.pi * nfreq)
        self.mi = np.array(mi)
        
        #calculation of a FRF
        self.H = np.zeros(len(self.freq), dtype=complex)
        if residues == 'True':
            for i in range(0, len(self.freq)):
                for k in range(0, len(self.nom)):
                    self.H[i] = self.H[i] + A[k + 1] / (self.nom[k] ** 2 - self.om[i] ** 2 + mi[k] * 1j * self.nom[k] ** 2)
                self.H[i] = self.H[i] * self.om[i] ** 2 + A[0] - A[-1] * self.om[i] ** 2
                
        if residues == 'False':
            for i in range(0, len(self.freq)):
                for k in range(0, len(self.nom)):
                    self.H[i] = self.H[i] + A[k] / (self.nom[k] ** 2 - self.om[i] ** 2 + mi[k] * 1j * self.nom[k] ** 2)
            
        return self.H
                    
    def matrixMKC(self, M, K, C): 
        """generates FRF matrix from M, K and C matrices  

        Arguments:
        M - mass matrix
        K - stiffness matrix 
        C - viscous damping matrix
        """   
        self.H = np.zeros((len(self.freq), len(M), len(M)), dtype=complex)
        for i in range(1, len(self.freq)):
            self.H[i, :, :] = np.linalg.inv(K - ((self.om[i]) ** 2) * M + 1.0j * (self.om[i])* C)
        return self.H
            
    

def test1():
    A = [ -1.44424272e+00 , 9.24661162e-01, 3.83639351e-01, -9.83447395e-02, \
       - 5.20727677e-01, -8.60266461e-01, -1.09721165e+00, -1.19019865e+00, \
       - 1.20079778e+00, 3.56776014e-08]
    mi = [ 0.00657129 , 0.00159183 , 0.00120527  , 0.00107329, 0.00104117 , 0.00103019, \
        0.00103257, 0.00108387]
    nf = [   53., 146.5, 287.5, 476., 713., 1000., 1339., 1729. ]
    A = np.array(A)
    mi = np.array(mi)
    nf = np.array(nf)
    MX = FRF(0, 2000, 0.5)
    MX.frf_mp(A, nf, mi, residues='True')
    
    
    uf = UFF(r'..\..\..\tests\data\beam.uff')
    uffdataset58 = uf.read_sets()       
    freq = uffdataset58[0]['x']
    H = np.zeros((len(uffdataset58[0]['data']), len(uffdataset58)), dtype='complex')
    for j in range(0, len(uffdataset58)):
        H[:, j] = uffdataset58[j]['data']
    
    print(freq[1], freq[-1])
    plt.semilogy(MX.freq, np.abs(MX.H))
    plt.semilogy(freq, np.abs(H[:, 1]))
    plt.show()

    
    
def test2():
    m1 = 3. ;m2 = 1. ;m3 = 2.
    k1 = 5e7;k2 = 5e7;k3 = 1.5e3
    M1 = np.zeros((3, 3)) ; K1 = np.zeros((3, 3))
    
    K1[0, 0] = k1; K1[0, 1] = K1[1, 0] = -k1;   K1[1, 1] = k1 + k2; K1[1, 2] = K1[2, 1] = -k2; K1[2, 2] = k2;    
    M1[0, 0] = m1; M1[1, 1] = m2; M1[2, 2] = m3;
    
    
    SDOF = FRF(0, 2000, 5)
    SDOF.matrixMKC(M1, K1, K1 * 0.001)
    plt.semilogy(SDOF.freq, np.abs(SDOF.H[:, 0, 0]))
    plt.show()        
    
 
    
if __name__ == '__main__':
    
    test1()
    test2()
    
    
 
    
    
    
    
    
    
