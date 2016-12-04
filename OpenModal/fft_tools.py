
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


""" Tools to work wit fft data. Especially, frequency response functions

History:
    -May 2015: code clean up and added separate testing
    -Jul 2014: FRF dimensions changed from frf[frequency,sample] to frf[sample, frequency], PEP cleaning, Janko Slavic
    -May 2014: cleaning and polishing of the code, Janko Slavic
    -Apr 2014: convert_frf, Blaz Starc

@author: Janko Slavic, Blaz Starc
    @contact: janko.slavic@fs.uni-lj.si, blaz.starc@fs.uni-lj.si

"""

import numpy as np

_FRF_TYPES = {'a': 2, 'v': 1, 'd': 0}  # accelerance, mobility, receptance

def multiply(ffts, m):
    """Multiplies ffts*m. ffts can be a single fft or an array of ffts.

    :param ffts: array of fft data
    :param m: multiplication vector
    :return: multiplied array of fft data
    """
    out = np.zeros_like(ffts, dtype='complex')
    if len(np.shape(ffts)) == 2:  # list of
        n = np.shape(ffts)[0]  # number of frfs
        for j in range(n):
            out[j, :] = ffts[j, :] * m
    else:
        out[:] = ffts[:] * m

    return out


def frequency_integration(ffts, omega, order=1):
    """Integrates ffts (one or many) in the frequency domain.

    :param ffts: [rad/s] : angular frequency vector
    :param omega: angular frequency
    :param order: order of integration
    :return: integrated array of fft data
    """
    return multiply(ffts, np.power(-1.j / omega, order))


def frequency_derivation(ffts, omega, order=1):
    """Derivates ffts (one or many) in the frequency domain.

    :param ffts: array of fft data
    :param omega: [rad/s] angular frequency vector
    :param order: order of derivation
    :return: derivated array of fft data
    """
    return multiply(ffts, np.power(1.j * omega, order))

def convert_frf(input_frfs, omega, input_frf_type, output_frf_type):
    """ Converting the frf accelerance/mobility/receptance

    The most general case is when `input_frfs` is of shape:
       `nr_inputs` * `nr_outputs` * `frf_len`

    :param input_frfs:  frequency response function vector (of dim 1, 2 or 3)
    :param omega: [rad/s] angular frequency vector
    :param input_frf_type: 'd' receptance, 'v' mobility, 'a' accelerance (of dim 0, 1, 2)
    :param output_frf_type: 'd' receptance, 'v' mobility, 'a' accelerance (of dim 0, 1, 2)
    :return: frequency response function vector (of dim 1, 2 or 3)
    """
    # put all data to 3D frf type (nr_inputs * nr_outputs * frf_len)
    ini_shape = input_frfs.shape
    if 1 <=len(ini_shape) > 3 :
        raise Exception('Input frf should be if dimension 3 or smaller')
    elif len(ini_shape) == 2:
        input_frfs = np.expand_dims(input_frfs, axis=0)

        if type(input_frf_type) == str:
            input_frf_type = [ini_shape[0]*[input_frf_type]]
        else:
            input_frf_type = [input_frf_type]

        if type(output_frf_type) == str:
            output_frf_type = [ini_shape[0]*[output_frf_type]]
        else:
            output_frf_type = [output_frf_type]
    elif len(ini_shape) == 1:
        input_frfs = np.expand_dims(np.expand_dims(input_frfs, axis=0), axis=0)
        input_frf_type = [[input_frf_type]]
        output_frf_type = [[output_frf_type]]

    # reshaping of frfs
    (nr_inputs, nr_outputs, frf_len) = input_frfs.shape
    nr_frfs = nr_inputs * nr_outputs
    input_frfs = input_frfs.reshape(nr_frfs,-1)

    # reshaping of input and output frf types
    input_frf_type = np.asarray(input_frf_type)
    output_frf_type = np.asarray(output_frf_type)
    if len(input_frf_type.shape) != 2 or len(output_frf_type.shape) !=2:
        raise Exception('Input and output frf type should be of dimension 2.')
    input_frf_type = input_frf_type.flatten()
    output_frf_type = output_frf_type.flatten()
    if len(input_frf_type) != nr_frfs or len(output_frf_type) != nr_frfs:
        raise Exception('Input and output frf type length should correspond to the number frfs.')

    try:
        input_frf_type = [_FRF_TYPES[_] for _ in input_frf_type]
        output_frf_type = [_FRF_TYPES[_] for _ in output_frf_type]
    except:
        raise('Only frf types: d, v and a are supported.')

    # do the conversion
    output_frfs = np.zeros_like(input_frfs)
    for i in range(nr_frfs):
        order = output_frf_type[i] - input_frf_type[i]
        if (order > 2) or (order <-2):
            raise Exception('FRF conversion not supported.')
        output_frfs[i, :] = frequency_derivation(input_frfs[i, :], omega, order=order)

    #reshape back to original shape
    if len(ini_shape) == 3:
        return output_frfs.reshape((nr_inputs, nr_outputs, -1))
    elif len(ini_shape) == 2:
        return output_frfs.reshape((nr_outputs, -1))
    elif len(ini_shape) == 1:
        return output_frfs[0]


def correct_time_delay(fft, w, time_delay):
    """
    Corrects the ``fft`` with regards to the ``time_delay``.

    :param fft: fft array
    :param w: angular frequency [rad/s]
    :param time_delay: time dalay in seconds
    :return: corrected fft array
    """
    return fft / (np.exp(1j * w * time_delay))


def PSD(x, dt=1):
    """ Power spectral density
    :param x: time domain data
    :param dt: delta time
    :return: PSD, freq
    """
    X = np.fft.rfft(x)
    freq = np.fft.rfftfreq(len(x), d=dt)
    X = 2 * dt * np.abs(X.conj() * X / len(x))

    return X, freq


def fft_adjusted_lower_limit(x, lim, nr):
    """
    Compute the fft of complex matrix x with adjusted summation limits:

        y(j) = sum[k=-n-1, -n-2, ... , -low_lim-1, low_lim, low_lim+1, ... n-2,
                   n-1] x[k] * exp(-sqrt(-1)*j*k* 2*pi/n),
        j = -n-1, -n-2, ..., -low_limit-1, low_limit, low_limit+1, ... n-2, n-1

    :param x: Single-sided complex array to Fourier transform.
    :param lim: lower limit index of the array x.
    :param nr: number of points of interest
    :return: Fourier transformed two-sided array x with adjusted lower limit.
             Retruns [0, -1, -2, ..., -nr+1] and [0, 1, 2, ... , nr-1] values.

    """
    nf = 2 * (len(x) - lim) - 1

    n = np.arange(-nr + 1, nr)

    a = np.fft.fft(x, n=nf).real[n]
    b = np.fft.fft(x[:lim], n=nf).real[n]
    c = x[lim].conj() * np.exp(1j * 2 * np.pi * n * lim / nf)

    res = 2 * (a - b) - c

    return res[:nr][::-1], res[nr - 1:]


def check_fft_for_speed(data_length, exception_if_prime_above=20):
    """To avoid slow FFT, raises an exception if largest prime above `exception_if_prime_above`.

    See: http://stackoverflow.com/questions/23287/largest-prime-factor-of-a-number/

    :param data_length: length of data for frf
    :param exception_if_prime_above: raise exception if the largest prime number is above
    :return: none
    """

    def prime_factors(n):
        """Returns all prime factors of a positive integer

        See: http://stackoverflow.com/questions/23287/largest-prime-factor-of-a-number/412942#412942

        :param n: lenght
        :return: array of prime numbers
        """
        factors = []
        d = 2
        while n > 1:
            while n % d == 0:
                factors.append(d)
                n /= d
            d += 1
            if d * d > n:
                if n > 1:
                    factors.append(n)
                break
        return factors

    if np.max(prime_factors(data_length)) > exception_if_prime_above:
        raise Exception('Change the number of time/frequency points or the FFT will run slow.')


def irfft_adjusted_lower_limit(x, low_lim, indices):
    """
    Compute the ifft of real matrix x with adjusted summation limits:

        y(j) = sum[k=-n-2, ... , -low_lim-1, low_lim, low_lim+1, ... n-2,
                   n-1] x[k] * exp(sqrt(-1)*j*k* 2*pi/n),
        j =-n-2, ..., -low_limit-1, low_limit, low_limit+1, ... n-2, n-1

    :param x: Single-sided real array to Fourier transform.
    :param low_lim: lower limit index of the array x.
    :param indices: list of indices of interest
    :return: Fourier transformed two-sided array x with adjusted lower limit.
             Retruns values.
    """

    nf = 2 * (x.shape[1] - 1)
    a = (np.fft.irfft(x, n=nf)[:, indices]) * nf
    b = (np.fft.irfft(x[:, :low_lim], n=nf)[:, indices]) * nf
    return a - b


if __name__ == '__main__':
    plot_figure = False
    # check_fft_for_speed(4) #fast
    # check_fft_for_speed(59612) #slow
