
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


#!/usr/bin/python
"""Returns simulated receptance of 3DOF system.
 
    History:
         -mar 2013: janko.slavic@fs.uni-lj.si

"""
import numpy as np

def get_simulated_receptance(df_Hz=1, f_start=0, f_end=2000, measured_points=8, show=False, real_mode=False):
    '''Returns simulated receptance of 3DOF system.
    
    Keyword arguments:
    df_Hz=1  -- frequency resolution in Hz (default 1)
    f_start  -- start frequency (default 0)
    f_end    -- end frequency (default 2000)
    measured_points  -- number of measured points (default 8)
    show     -- show simulated receptance (default False)        
    '''
    C = np.array([0.5 + 0.001j, 0.2 + 0.005j, 0.05 + 0.001j], dtype='complex')     # mode residue
    
    if real_mode:
        C = np.real(C)
    
    eta = np.asarray([3e-3, 5e-3, 4e-3])                      # damping loss factor
    df = df_Hz                                                # freq resolution
    D = 1e-8 * (1 + 1.j)                                      # residual of missing modes
    
    f = np.arange(f_start, f_end, step=df) # frequency range
    
    f0 = np.asarray([320.05, 850, 1680])
    w0 = f0 * 2 * np.pi     #to rad/s
    w = f * 2 * np.pi
    
    n = w.size              #number of samples
    N = measured_points     #number of measured points
    M = eta.size            #number of modes

    modes = np.zeros([M, N])
    for mode, m in zip(modes, range(M)):
        mode[:] = np.sin((m + 1) * np.pi * (0.5 + np.arange(N)) / (N))
        mode[:] = mode - np.mean(mode)
    if show:
        plt.plot(np.transpose(modes))
        plt.show()
    modal_constants = modes * np.transpose(np.asarray([C]))
        
    alpha = np.zeros([N, n], dtype='complex')
    for al, modes_at_pos in zip(alpha, np.transpose(modes)):
        for c, e, w0_, m, mode_at_pos in zip(C, eta, w0, range(M), modes_at_pos):
            c = c * (mode_at_pos)
            al[:] = al + c / (w0_ ** 2 - w ** 2 + 1.j * e * w0_ ** 2)    
    if show:
        fig, [ax1, ax2] = plt.subplots(2, 1, sharex=True, figsize=(12, 10))
        ax1.plot(f, 20 * np.log10(np.abs(np.transpose(alpha)))) 
        ax2.plot(f, 180 / np.pi * (np.angle(np.transpose(alpha))))
        
        ax1.set_ylabel('Frequency [Hz]')
        ax1.set_ylabel('Magn [dB]')
        ax2.set_ylabel('Angle [deg]')
        
        plt.show()
    
    return f, alpha, modal_constants, eta, f0

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    get_simulated_receptance(show=True)