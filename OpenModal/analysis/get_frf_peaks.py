""" Searches for peaks of the FRF represented by h

    History:
         -mar 2013: janko.slavic@fs.uni-lj.si
"""

import numpy as np

def get_frf_peaks(f, h, freq_min_spacing=10):
    '''Searches for peaks of the FRF represented by h
        
       Keyword arguments:
        f      -- frequency vector
        h      -- Frequency response vector (can be complex)
        freq_min_spacing -- minimum spacing between two peaks (default 10)        
        
       Note: units of f and freq_min_spacing are arbitrary, but need to be the same.
    '''
    df = f[1] - f[0]
    i_min_spacing = np.int(freq_min_spacing / df)

    peak_candidate = np.zeros(h.size - 2 * i_min_spacing - 2)
    peak_candidate[:] = True
    for spacing in range(i_min_spacing):
        h_b = np.abs(h[spacing:-2 * i_min_spacing + spacing - 2])  #before
        h_c = np.abs(h[i_min_spacing:-i_min_spacing - 2])   #central
        h_a = np.abs(h[i_min_spacing + spacing + 1:-i_min_spacing + spacing - 1])   #after
        peak_candidate = np.logical_and(peak_candidate, np.logical_and(h_c > h_b, h_c > h_a))
    
    ind = np.argwhere(peak_candidate == True)
    return ind.reshape(ind.size) + i_min_spacing#correction for central