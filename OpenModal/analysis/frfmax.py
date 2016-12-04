
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

from OpenModal.analysis.utility_functions import myfunc


def frfmax(H1, freq, threshold=10):
    """frfmax(self,H1,threshold) calculates natural frequencies from H1

    It picks all the FRF magnitude peaks, which are over the threshold setting. If a magnitude point is
    higher than two neighbor's points it is assumed as a peak. The problem of this method 
    is, that it picks also the peaks which are a consequence of a noise.    
    
    Arguments:
        H1 - FRF from which natural frequencies are identified.
        threshold - Only peaks, which are over the threshold are identified from FRF measurement
        peak 
    """  
    peak = np.vectorize(myfunc) #vectorization of myfunc 
    ed = np.zeros(len(H1))    #ed is magnitude of FRF
    ed = np.abs(H1)
  

    ed[ed < threshold] = 0  #values of FRF below the threshold are zeroed out.
    ec = peak(ed[1:len(ed) - 2], ed[2:len(ed) - 1], ed[3:len(ed)]) #returns ones at index where NF 
    #are, elsewhere returns zeros.
    
    
    
    nor = sum(ec) #sum of array ec is number of NF
    ec = ec * range(0, len(ec))  #by multiplying with list of index we get array of  index where NF are 
    ec = np.sort(ec) #sorting of array
    ind = ec[-nor:] #last nonzero elements are index of NF
    ind += 2    #two is added because 'myfunc' checks middle variable 'd'

    nf = np.array(freq[ind])
    return nf