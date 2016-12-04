
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


"""Returns measured accelerance, mobility and receptance of a free-free beam (15mm x 30mm x 500mm).

   Measured at 11 points.
 
    History:
         -2013: janko.slavic@fs.uni-lj.si

"""
import numpy as np
import matplotlib.pyplot as plt
import pyuff

from OpenModal.fft_tools import convert_frf


def get_measured_accelerance(show=False):
    uf = pyuff.UFF(r'paket.uff')
    uffdataset58 = uf.read_sets()      
    freq = uffdataset58[0]
    H = np.zeros((len(uffdataset58[0]['data']), len(uffdataset58)), dtype='complex')
    for j in range(0, len(uffdataset58)):
        H[:, j] = uffdataset58[j]['data']
    if show:
        plt.semilogy(freq,np.abs(H[:,:]))
        plt.show()
    return freq, H

def get_measured_mobility(show=False):
    freq, H = get_measured_accelerance(show=False)
    omega = 2*np.pi*freq
    H = convert_frf(H, omega, inputFRFtype = 'a', outputFRFtype = 'v')
    if show:
        plt.semilogy(freq,np.abs(H[:,:]))
        plt.show()
    return freq, H

def get_measured_receptance(show=False):
    freq, H = get_measured_accelerance(show=False)
    omega = 2*np.pi*freq
    H = convert_frf(H, omega, inputFRFtype = 'a', outputFRFtype = 'd')
    if show:
        plt.semilogy(freq,np.abs(H[:,:]))
        plt.show()
    return freq, H

if __name__ == '__main__':
    get_measured_accelerance(show=True)
    #get_measured_mobility(show=True)
    #get_measured_receptance(show=True)