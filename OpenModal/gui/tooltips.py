
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


tooltips = dict()

tooltips['impulse_excitation'] = 'Measure using impulse excitation, such as impact hammer.'
tooltips['random_excitation'] = 'Measure using broadband random excitation, usually done with shaker equipement.'
tooltips['OMA_excitation'] = 'Operational modal analysis type of measurement, taking advantage of operational vibration.'
tooltips['signal_selection'] = 'Select a DAQmx task, prepared using NI MAX.'
tooltips['nimax'] = 'Run National Instruments Measurement and Automation Explorer; create a measurement task.'
tooltips['window_length'] = 'Length of a window, relevant for frequency analysis (FFT) and plot range.'
tooltips['zero_padding'] = 'Add zeros to signal, for improved frequency resolution.'
tooltips['excitation_window'] = 'Type of excitation window.'
tooltips['excitation_window_percent'] = 'Takes the part of the original window, where the amplitude is above x% (force window only).'
tooltips['response_window'] = 'Type/shape of response window.'
tooltips['response_window_percent'] = 'Takes the part of the original window, where the amplitude is above x% (force window only).'
tooltips['averaging_type'] = 'Averaging strategy to use.'
tooltips['averaging_number'] = 'Number of windows to average over, to obtain the final result.'
tooltips['save_time_history'] = '''Save time history alongside the calculated results (FRFs). Parameters pertaining to
frequency-domain transformation can be changed later on.'''
tooltips['trigger_level'] = 'Amplitude level, which is considered an impulse.'
tooltips['pre_trigger_samples'] = 'The number of samples to be added, before the trigger occurence.'
tooltips['test_run'] = 'Run acquisition to test the preferences.'
tooltips['toggle_PSD'] = 'Toggle between time-history and power-spectral density plot.'