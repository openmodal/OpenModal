
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


# -*- coding: UTF-8 -*-
"""Class for 2D buffer array. Based on this code: http://scimusing.wordpress.com/2013/10/25/ring-buffers-in-pythonnumpy/

Classes:
    class RingBuffer: Buffer for 2D array.

Info:
    @author: janko.slavic@fs.uni-lj.si, 2014
"""
import numpy as np


class RingBuffer():
    """A 2D ring buffer using numpy arrays"""

    def __init__(self, channels, samples):
        self.data = np.zeros((channels, samples), dtype='float')
        self.index = 0

    def clear(self):
        """Clear buffer."""
        self.data = np.zeros_like(self.data)
        self.index = 0

    def extend(self, x, add_samples='all'):
        """adds array x to ring buffer"""
        if x[0].size==0:
            return
        if add_samples!='all':
            if add_samples<=0:
                return
            if add_samples<x[0].size:
                x=x[:,:add_samples]
        x_index = (self.index + np.arange(x[0].size)) % self.data[0].size
        self.data[:, x_index] = x
        self.index = x_index[-1] + 1

    def get(self,length='all'):
        """Returns the first-in-first-out data in the ring buffer"""
        idx = (self.index + np.arange(self.data[0].size)) % self.data[0].size
        if length=='all':
            return self.data[:, idx]
        else:
            return self.data[:, idx[:length]]


def ringbuff_numpy_test():
    samples = 10
    channels = 2
    ringbuff = RingBuffer(channels, samples)
    ringbuff.extend(np.array([[],[]], dtype='float'))  # write

    for i in range(40):
        ringbuff.extend(1 + i + np.zeros((channels, 2), dtype='float'))  # write
        print(ringbuff.get())  # read

if __name__ == "__main__":
    ringbuff_numpy_test()