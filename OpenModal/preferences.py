
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


__author__ = 'Matjaz'
DEFAULTS = dict()
DEFAULTS['excitation_type'] = 'impulse'
DEFAULTS['channel_types'] = ['f'] + ['a']*13
# TODO: Implement auto! (MAX value taken)
DEFAULTS['samples_per_channel'] = 10000
DEFAULTS['nodes'] = [0,0]
DEFAULTS['directions'] = ['+x']*13
DEFAULTS['trigger_level'] = 5
DEFAULTS['pre_trigger_samples'] = 30
DEFAULTS['exc_channel'] = 0
DEFAULTS['resp_channels'] = [1]*13
DEFAULTS['exc_window'] = 'Force:0.01'
DEFAULTS['resp_window'] = 'Exponential:0.01'
DEFAULTS['channel_delay'] = [0.]*14
DEFAULTS['weighting'] = 'None'
DEFAULTS['n_averages'] = 10
DEFAULTS['fft_len'] = 'auto'
DEFAULTS['pre_trigger_samples'] = 30
DEFAULTS['zero_padding'] = 0
DEFAULTS['save_time_history'] = False
DEFAULTS['roving_type'] = 'Ref. node'
DEFAULTS['selected_model_id'] = 1