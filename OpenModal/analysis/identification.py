#!/usr/bin/python
# -*- coding: latin-1 -*-
"""Module which tests identification methods for estimation of modal 
    parameters from FRF measurements

    Identification methods:
         -frfmax: natural frequency identification
         -ewins:  Ewins Gleeson's identification method
         -Circle-fitting method for viscous and histeretic damping
         -rational fraction polynmials, orthogonal_polynomials: 
          for obtain orthogonal polynomials which is required 
                      for rotational fraction polynomial identification method
         -Rational_Fraction_Polynomial: Rational fraction polynomial identification method
         -reconstruction: reconstruction of a FRF
         -ce: The Complex Exponential method
         -lsce: The Leas-Squares Complex Exponential Method
     
     Stabulisation charts:
         -stabilisation
         
    TODO: research a sign effect of  mass normalized modal shapes (sign of identified and calculated 
    modal shape are in some case different)
    TODO: improve the method FRFmax
    
    History:
         -may 2014: stabilisation, blaz.starc@fs.uni-lj.si
         -apr 2014: updated from python 2.7 to python 3.4, blaz.starc@fs.uni-lj.si
         -apr 2014: added test_ce, test_lsce; made seperate files for ce, ce_r, convert_frf, ewins, frfmax, 
                    get_frf_peaks, get_measured_accelerance, get_simulated_receptance, lsce, lsce_r, 
                    orthogonal_polynomials, Rational_Fraction_Polynomial, reconstruction; added _XTOL as a
                    variable to circle_fit : blaz.starc@fs.uni-lj.si
         -apr 2013: reconstruction, tadej.kranjc@ladisk.si 
         -mar 2013: get_simulated_receptance, reconstruction added to tests, added get_frf_peaks function and other small tweaks: janko.slavic@fs.uni-lj.si
         -feb 2013: Rational_Fraction_Polynomial and orthogonal_polynomials: uros.proso@fs.uni-lj.si
         -jan 2013: Circle-fitting method, martin.cesnik@fs.uni-lj.si
         -2012: ewins, tadej.kranjc@ladisk.si.  
"""

from OpenModal.analysis.ce import test_ce
from OpenModal.analysis.lsce import test_lsce
from OpenModal.analysis.ewins import test_ewins
from OpenModal.analysis.circle_fit import test_circle_fit_visc
from OpenModal.analysis.circle_fit import test_circle_fit_hist
from OpenModal.analysis.rfp import test_rfp
from OpenModal.analysis.stabilisation import test_ce_stabilisation

if __name__ == '__main__':
    test_ewins()
    test_circle_fit_hist()
    test_circle_fit_visc()
    test_rfp()
    test_ce()
    test_lsce()
    test_ce_stabilisation()
