
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
from OpenModal.fft_tools import PSD

def overload_check(data, min_overload_samples=3):
    """Check data for overload

    :param data: one or two (time, samples) dimensional array
    :param min_overload_samples: number of samples that need to be equal to max
                                 for overload
    :return: overload status
    """
    if data.ndim > 2:
        raise Exception('Number of dimensions of data should be 2 or less')

    def _overload_check(x):
        s = np.sort(np.abs(x))[::-1]
        over = s == np.max(s)
        if np.sum(over) >= min_overload_samples:
            return True
        else:
            return False

    if data.ndim == 2:
        over = [_overload_check(d) for d in data.T]
        return over
    else:
        over = _overload_check(data)
        return over


def double_hit_check(data, dt=1, limit=1e-3, plot_figure=False):
    """Check data for double-hit

    See: at the end of http://scholar.lib.vt.edu/ejournals/MODAL/ijaema_v7n2/trethewey/trethewey.pdf

    :param data: one or two (time, samples) dimensional array
    :param dt: time step
    :param limit: ratio of freq content od the double vs single hit
                  smaller number means more sensitivity
    :param plot_figure: plots the double psd of the data
    :return: double-hit status
    """
    if data.ndim > 2:
        raise Exception('Number of dimensions of data should be 2 or less!')

    def _double_hit_check(x):
        # first PSD
        W, fr = PSD(x, dt=dt)
        # second PSD: look for oscillations in PSD
        W2, fr2 = PSD(W, dt=fr[1])
        upto = int(0.01 * len(x))
        max_impact = np.max(W2[:upto])
        max_after_impact = np.max(W2[upto:])
        if plot_figure:
            import matplotlib.pyplot as plt
            plt.subplot(121)
            l = int(0.002*len(x))
            plt.plot(1000*dt*np.arange(l),  x[:l])
            plt.xlabel('t [ms]')
            plt.ylabel('F [N]')
            plt.subplot(122)
            plt.semilogy((W2/np.max(W2))[:5*upto])
            plt.axhline(limit, color='r')
            plt.axvline(upto, color='g')
            plt.xlabel('Double freq')
            plt.ylabel('')
            plt.show()

        if max_after_impact / max_impact > limit:
            return True
        else:
            return False

    if data.ndim == 2:
        double_hit = [_double_hit_check(d) for d in data.T]
        return double_hit
    else:
        double_hit = _double_hit_check(data)
        return double_hit
