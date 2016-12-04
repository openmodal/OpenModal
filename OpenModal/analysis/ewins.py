
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


""" Ewins-Gleeson Identification method

Identifies modal shapes and modal damping from FRF measurements.

This method demands (needs) optional points. This optional points are 
the same for all the FRF measurements.
    
This method was presented in: Ewins, D.J. and Gleeson, P. T.: A method
for modal identification of lightly damped structures

Functions:
    - ewins
    - reconstruction
    - test_ewins

History:- april 2014: added convert_frf to ewins, reconstruction, 
          Blaz Starc, blaz.starc@fs.uni-lj.si,
        - april 2013: reconstruction, Tadej Kranjc, 
           tadej.kranjc@ladisk.si  
        - 2012: ewins, test_ewins: Tadej Kranjc, 
           tadej.kranjc@ladisk.si
         
"""
import numpy as np

from OpenModal.analysis.get_frf_peaks import get_frf_peaks
from OpenModal.fft_tools import convert_frf


def ewins(freq, H, nf='None', residues=False, type='d', o_fr=0):
    """ 
    Arguments:
        - freq - frequency vector
        - H - a row or a column of FRF matrix 
        - o_fr - list of optionally chosen frequencies in Hz. If it is 
                not set, optional points  are set automatically and are 
                near the natural frequencies (10 points higher than 
                natural frequencies)
        - nf - natural frequencies [Hz]
        -ref - index of reference node
        - residues - if 1 residues of lower and higher residues are 
                     taken into account 
                   - if 0 residues of lower and higher residues are 
                     not taken into account
                   
        - type - type of FRF function: 
                                    -'d'- receptance
                                    -'v'- mobility
                                    -'a'- accelerance
    """
    om = freq * 2 * np.pi 
    H2 = convert_frf(H, om, type, outputFRFtype = 'a') # converts FRF to accalerance                                                                      
 
    
    if nf != 'None':  
        ind = (np.round(nf / (freq[2] - freq[1])))
        ind = np.array(ind, dtype=int)
        
    if ind == 'None':
        print ('***ERROR***Natural frequencies are not defined')
        quit()
        
    #determination of N points which are chosen optionally

    if o_fr == 0 and residues == True:
        ind_opt = np.zeros((len(ind) + 2), dtype='int')
        ind_opt[0] = 20
        ind_opt[1:-1] = ind + 20
        ind_opt[-1] = len(freq) - 20
        
    if o_fr == 0 and residues == False:
        ind_opt = np.zeros((len(ind)), dtype='int')
        ind_opt = ind + 10
        
    if o_fr != 0:
        ind_opt = (np.round(o_fr / (freq[2] - freq[1])))
        ind_opt = np.array(ind_opt, dtype=int)
      
    #matrix of modal damping
    
    mi = np.zeros((len(ind), len(H2[0, :])))
    Real = np.real(H2[:, 0])
    #self.Imag=np.imag(self.FRF[:,0])
    
    R = np.zeros((len(ind_opt), len(ind_opt)))
    A_ref = np.zeros((len(ind_opt), len(H2[0, :]))) #modal constant of FRF
    FI = np.zeros((len(ind_opt), len(H2[0, :])), dtype=complex)    #mass normalized modal 
    #vector 

    R[:, 0] = np.ones(len(ind_opt))
           
    for jj in range (0, len(ind_opt)):
        R[jj, -1] = -(om[ind_opt[jj]]) ** 2
                 
        if residues == True:
            R[jj, 1:-1] = (om[ind_opt[jj]]) ** 2 / ((om[ind[:]]) ** 2 - (om[ind_opt[jj]]) ** 2)
        if residues == False:
            R[jj, :] = (om[ind_opt[jj]]) ** 2 / ((om[ind[:]]) ** 2 - (om[ind_opt[jj]]) ** 2)
                
    R = np.linalg.inv(R)
    
    for j in range (0, len(H2[:, 0])):
        Re_pt = np.real(H2[j, ind_opt])
        Re_pt = np.matrix(Re_pt)       
        
        C = np.dot(R, Re_pt.transpose()) #modal constant of one FRF
        A_ref[:, j] = -C.flatten()   #modal constant of all FRFs
        
    
        if residues == True:
            mi[:, j] = np.abs(C[1:-1].transpose()) / (np.abs(H2[j, ind[:]])) #modal damping        
            
        if residues == False:
            mi[:, j] = np.abs(C[:].transpose()) / (np.abs(H2[j, ind[:]])) #modal damping
    
#    for kk in range(0, len(ind_opt)):
#        FI[kk, :] = -A_ref[kk, :] / np.sqrt(np.abs(A_ref[kk, refPT]))   #calculation of 
#        #normalized modal vector
        
    if residues == True:            
        #return FI[1:-1, :], mi
        return A_ref, mi

    if residues == False:            
        return A_ref, mi
    
def reconstruction(freq, nfreq, A, d, damping='hysteretic', type='a', residues=False, LR=0, UR=0):
    """generates a FRF from modal parameters. 
    
    There is option to consider the upper and lower residues (Ewins, D.J.
    and Gleeson, P. T.: A method for modal identification of lightly 
    damped structures) 
    
    #TODO:  check the correctness of the viscous damping reconstruction
    
    Arguments:
        A - Modal constants of the considering FRF.
        nfreq - natural frequencies in Hz
        c - damping loss factor or damping ratio
        damp - type of damping:
                                 -'hysteretic'
                                 -'viscous'
        LR - lower residue
        UR - upper residue
        
        residues - if 'True' the residues of lower and higher residues 
                   are taken into account.  The lower and upper residues 
                   are first and last component of A, respectively.
        type - type of FRF function: 
                                -'d'- receptance
                                -'v'- mobility
                                -'a'- accelerance   
    """ 
    
    
    A = np.array(A, dtype='complex')
    d=np.array(d)
    om = np.array(2 * np.pi * freq)
    nom = np.array(2 * np.pi * nfreq)
    
    #in the case of single mode the 1D arrays have to be created
    if A.shape==():
        A_=A; d_=d  ; nom_=nom
        A=np.zeros((1),dtype='complex'); d=np.zeros(1) ; nom=np.zeros(1)
        A[0]=A_ ; d[0]=d_
        nom[0]=nom_
    
    if residues:
        LR = np.array(LR)
        UR = np.array(UR)
        
    H = np.zeros(len(freq), dtype=complex)

    if damping == 'hysteretic':
        #calculation of a FRF
        for i in range(0, len(freq)):
            for k in range(0, len(nom)):
                H[i] = H[i] + A[k] / (nom[k] ** 2 - om[i] ** 2 + d[k] * 1j * nom[k] ** 2)
            
        if residues: 
            for i in range(1, len(freq)):
                H[i] = H[i] + LR / om[i] ** 2 - UR
                            
    if damping == 'viscous':
        H = np.zeros(len(freq), dtype=complex)
        for i in range(0, len(freq)):
            for k in range(0, len(nom)):
                H[i]=H[i]+ A[k] / (nom[k] ** 2 - om[i] ** 2 + 2.j * om[i] * nom[k] * d[k])
    
    H = convert_frf(H, om, 'd' ,type)  
    return H

def test_ewins():
    import matplotlib.pyplot as plt
    from OpenModal.analysis.get_simulated_sample import get_simulated_receptance
    
    residues = True
    
    freq, H, MC, eta, D = get_simulated_receptance(
        df_Hz=1, f_start=0, f_end=2000, measured_points=10, show=False, real_mode=True)
    #freq, H = get_measured_accelerance()
    
    #identification of natural frequencies
    ind_nf = get_frf_peaks(freq, H[1, :], freq_min_spacing=10)
     
    #identification of modal constants and damping
    A, mi = ewins(freq, H, freq[ind_nf], type='d', residues=residues)  
    
    #reconstruction
    Nfrf = 4  #serial number of compared FRF
    H_rec = reconstruction(freq, freq[ind_nf], A[1:-1, Nfrf], mi[:, Nfrf], 
                           residues=residues, type='d', LR=A[0, Nfrf], UR=A[-1, Nfrf])
    H_rec = reconstruction(freq, freq[ind_nf], A[1:-1, Nfrf]  , mi[:, Nfrf], 
                           residues=True, type='d', LR=A[0, Nfrf], UR=A[-1, Nfrf])
    
    #comparison of original and reconstructed FRF
     
    fig, [ax1, ax2] = plt.subplots(2, 1, sharex=True, figsize=(12, 10))
    ax1.semilogy(freq, np.abs(H[Nfrf, :]))
    ax1.semilogy(freq, np.abs(H_rec)) 
    ax2.plot(freq, 180 / np.pi * (np.angle(H[Nfrf, :])))
    ax2.plot(freq, 180 / np.pi * (np.angle(H_rec)))
    ax1.set_ylabel('Frequency [Hz]')
    ax1.set_ylabel('Magn [m s$^{-2}$ N$^{-1}$]')
    ax2.set_ylabel('Angle [deg]')
    plt.show()
 
    
    if residues:
        plt.plot(range(0, len(A[1, :])), np.real(A[1:-1]).T, 'r')
    else:
        plt.plot(range(0, len(A[0, :])), A, 'r')
    plt.plot(range(0, len(MC[0, :])), MC.T)
    plt.xlabel('Point')
    plt.ylabel('Modal constant')
    plt.show
    
if __name__ == '__main__':
    test_ewins()