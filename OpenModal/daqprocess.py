
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
import numpy as np
import time
import RingBuffer as RingBuffer
import DAQTask as DAQTask
import multiprocessing as mp

_DIRECTIONS = ['scalar', '+x', '+y', '+z', '-x', '-y', '-z']
_DIRECTIONS_NR = [0, 1, 2, 3, -1, -2 - 3]

def direction_dict():
    dir_dict = {a: b for a, b in zip(_DIRECTIONS, _DIRECTIONS_NR)}
    return dir_dict

class MeasurementProcess(object):
    """Impact measurement handler.

        :param task_name: task name for the daq
        :param samples_per_channel: number of samples per channel.
                                    if 'auto' then: samples_per_channel=sampling_rate
        :param exc_channel: the number of excitation channel - necessary for triggering
        :param channel_delay: list of channel delays (lasers typical have a time delay close to 1ms)
        :param fft_len: the length of the FFT, if 'auto' then the freq length matches the time length
        :param trigger_level: amplitude level at which to trigger.
        :param pre_trigger_samples: how many samples should be pre-triggered
    """
    def __init__(self, task_name=None, samples_per_channel='auto',
                 channel_delay=[0., 0.], exc_channel=0,
                 fft_len='auto', trigger_level=5, pre_trigger_samples=10):
        """Constructor. Only the defaults are passed in at initialization. This starts the separate thread (which takes
        some time) and waits for the user. When the preferences are setup this same parameters are reloaded. At the
        moment, this is done from the parent script using Impact.__dict__."""
        super(MeasurementProcess, self).__init__()

        self.key_list = dict(excitation_type=None, task_name=None, samples_per_channel='auto',
                             channel_delay=[0., 0.], exc_channel=0,
                             fft_len='auto', trigger_level=5, pre_trigger_samples=10, n_averages=8)

        self.parameters = dict()

        # Trigger, keeps the thread alive.
        self.live_flag = mp.Value('b', False)

        self.setup_measurement_parameters(locals())

    def setup_measurement_parameters(self, parameters_dict):
        """Load parameters, not in __init__ but later. The object is initialized early, before the parameters are known,
        to reduce waiting time. Get the settings dictionary but only load what you need (written in self.key_list)."""
        # Setup parameters. Defaults taken from self.key_list when not available.
        for key in self.key_list.keys():
            if key in parameters_dict:
                self.__setattr__(key, parameters_dict[key])
                # Also prepare a dict with those same values
            else:
                self.__setattr__(key, self.key_list[key])

    def start_process(self):
        """Start a separate measurement process, do not start collecting the data just yet (run_measurement)."""
        # . Prepare separate measurement process.

        # Trigger, keeps the thread alive.
        # self.live_flag = mp.Value('b', True)
        self.live_flag.value = True

        # .. Trigger, starts the measurement - shared variable.
        self.run_flag = mp.Value('b', False)

        # .. Trigger, signals the signal level trigger was tripped. This trigger is picked up in the parent app.
        self.triggered = mp.Value('b', False)

        # Pipe to send parameters to the separate thread.
        self.properties_out, self.properties_in = mp.Pipe(False)

        # Pipe to send sampling_rate through. Later maybe also other data.
        self.task_info_out, self.task_info_in = mp.Pipe(False)

        # Start the thread. Pipe end and shared variables are passed.
        self.process = mp.Process(target=ThreadedDAQ, args=(self.live_flag, self.run_flag, self.properties_out,
                                                            self.task_info_in, self.triggered))
        self.process.start()

    def stop_process(self, timeout=2):
        """Stop the process."""
        if self.run_flag.value:
            self.stop_measurement()

        if self.live_flag.value:
            self.live_flag.value = False

        # Close the pipes.
        self.properties_out.close()
        self.properties_in.close()
        self.task_info_in.close()
        self.task_info_out.close()

        self.process.join(timeout)

    def run_measurement(self):
        """Start measuring."""
        if self.run_flag.value:
            print('Process already running.')
        elif not self.run_flag.value:
            # First push fresh arguments to the separate process.
            pdict = dict(excitation_type=self.excitation_type, task_name=self.task_name,
                         samples_per_channel=self.samples_per_channel,
                         exc_channel=self.exc_channel,
                         channel_delay=self.channel_delay,
                         fft_len=self.fft_len, trigger_level=self.trigger_level,
                         pre_trigger_samples=self.pre_trigger_samples,
                         n_averages=self.n_averages)

            # Reinitialize pipes beforehand (pipes are closed each time the measurement is stopped).
            self.process_measured_data_out, self.process_measured_data_in = mp.Pipe(False)
            self.process_random_chunk_out, self.process_random_chunk_in = mp.Pipe(False)

            pdict['measured_data_pipe'] = self.process_measured_data_in
            pdict['random_chunk_pipe'] = self.process_random_chunk_in

            # Actually send the data over the pipe.
            self.properties_in.send(pdict)

            # Send a start signal to the process object.
            self.run_flag.value = True

    def stop_measurement(self):
        """Stop measuring."""
        if not self.run_flag.value:
            # Check if the process should already be stopped.
            raise Exception('Process already stopped.')
        elif self.run_flag.value:
            # Stop it and close the pipes. Both ends of the pipes should be closed at the same time, like below.
            self.run_flag.value = False
            self.triggered.value = False
            self.process_measured_data_in.close()
            self.process_measured_data_out.close()
            self.process_random_chunk_in.close()
            self.process_random_chunk_out.close()


class ThreadedDAQ(object):
    """Code that runs in a separate thread, getting data from the hardware.
    """
    def __init__(self, live_flag, run_flag, properties, task_info, trigger, measured_data=None, task=None, exc_channel=None,
                 trigger_level=None, pre_trigger_samples=None, n_averages=None):
        """Constructor."""
        super().__init__()

        self.properties = properties
        self.live_flag = live_flag
        self.run_flag = run_flag
        self.measured_data = measured_data
        self.random_chunk = None
        self.task_info = task_info
        self.exc_channel = exc_channel
        self.trigger_level = trigger_level
        self.pre_trigger_samples = pre_trigger_samples
        self.n_averages = n_averages

        self.triggered = trigger
        # self.triggered = False

        self.wait()

    def wait(self):
        """Wait for start signal."""
        while self.live_flag.value:
            if self.run_flag.value:
                self.inject_properties(self.properties.recv())
                # self.measurement_continuous()
                if self.type == 'impulse':
                    self.measurement_triggered()
                elif self.type == 'random' or self.type == 'oma':
                    self.measurement_continuous()

            time.sleep(0.01)

    def inject_properties(self, properties):
        """Get fresh arguments to the function before starting the measurement."""
        self.type = properties['excitation_type']
        self.task = DAQTask.DAQTask(properties['task_name'])
        self.sampling_rate = self.task.sample_rate
        self.task_info.send(self.sampling_rate)
        self.channel_list = self.task.channel_list
        self.samples_per_channel = self.task.samples_per_ch
        self.number_of_channels = self.task.number_of_ch
        self.exc_channel = properties['exc_channel']
        self.trigger_level = properties['trigger_level']
        self.pre_trigger_samples = properties['pre_trigger_samples']
        if properties['samples_per_channel'] is 'auto':
            self.samples_per_channel = self.task.samples_per_ch
        else:
            self.samples_per_channel = properties['samples_per_channel']
        self.samples_left_to_acquire = self.samples_per_channel

        # Reinitialize pipe always -- it is closed when measurement is stopped.
        self.measured_data = properties['measured_data_pipe']
        self.random_chunk = properties['random_chunk_pipe']

        self.ring_buffer = RingBuffer.RingBuffer(self.number_of_channels, self.samples_per_channel)

    def _add_data_if_triggered(self, data):
        # If trigger level crossed ...
        _trigger = np.abs(data[self.exc_channel]) > self.trigger_level
        if np.any(_trigger) and not self.internal_trigger:
            trigger_index = np.where(_trigger)[0][0]
            start = trigger_index - self.pre_trigger_samples
            self.samples_left_to_acquire+=start
            self.ring_buffer.extend(data, self.samples_left_to_acquire)
            self.samples_left_to_acquire = self.samples_left_to_acquire - data[0].size
            self.internal_trigger = True
        elif self.internal_trigger:
            self.ring_buffer.extend(data, self.samples_left_to_acquire)
            self.samples_left_to_acquire = self.samples_left_to_acquire - data[0].size
        else:
            self.ring_buffer.extend(data)

    def measurement_continuous(self):
        """Continuous measurement."""
        samples_left_local = self.samples_left_to_acquire
        while True:
            # TODO: Optimize below.
            if not self.run_flag.value:
                # self.measured_data.close()
                self.task.clear_task(False)
                # self.task = None
                break
            else:
                _data = self.task.acquire_base()
                self.ring_buffer.extend(_data, self.samples_left_to_acquire)
                # self.ring_buffer.extend(_data, self.samples_left_to_acquire)
                samples_left_local -= _data[0].size


                # TODO: Why this try/excepty? It always throws an error? Problems with sync between processes probably.
                try:
                    self.measured_data.send(self.ring_buffer.get())
                    if samples_left_local <= 0:
                        self.triggered.value = True
                        samples_left_local = self.samples_left_to_acquire
                        self.random_chunk.send(self.ring_buffer.get())
                        self.ring_buffer.clear()
                except:
                    print('DAQ Except')
                    if not self.run_flag.value:
                        pass
                    else:
                        raise Exception



    def measurement_triggered(self, trigger=100):
        """Continuous measurement."""
        # Run continuously.
        self.internal_trigger = False
        while True:
            # Stop from within.

            # Check if stop condition, then do some cleanup and break out of loop.
            if not self.run_flag.value:
                # self.measured_data.close()
                self.task.clear_task(False)
                self.task = None
                break
            # TODO: Check what is happening with the triggers.
            elif self.samples_left_to_acquire < 0:
                if self.internal_trigger:
                    self.triggered.value = True
                    # self.internal_trigger = False
            else:
                # Otherwise, do the measurement and watch for trigger.
                data = self.task.acquire_base()
                self._add_data_if_triggered(data)

                try:
                    self.measured_data.send(self.ring_buffer.get())
                except:
                    if not self.run_flag.value:
                        pass
                    else:
                        raise Exception

                # if self.samples_left_to_acquire == 0:
                #     break

    def measurement_nsamples(self, n=1000):
        """Measure N number of samples."""
        # TODO: This doesn't work obviously.
        while True:
            if not self.run_flag.value:
                self.measured_data.close()
                self.task.clear_task(False)
                self.task = None
                break
            else:
                _data = self.task.acquire_base()
                self.ring_buffer.extend(_data)
                try:
                    self.measured_data.send(self.ring_buffer.get())
                except:
                    if not self.run_flag.value:
                        pass
                    else:
                        raise Exception

def test_ring_buffer():
    tt = ThreadedDAQ(live_flag=mp.Value('b', False), run_flag=mp.Value('b', True), properties=None, task_info='OpenModal Impact_', trigger=False)
    tt.samples_per_channel=10
    tt.number_of_channels=2
    tt.trigger_level=3.5
    tt.pre_trigger_samples=5
    tt.exc_channel=0
    tt.ring_buffer = RingBuffer.RingBuffer(tt.number_of_channels, tt.samples_per_channel)
    tt.samples_left_to_acquire=tt.samples_per_channel
    tt.internal_trigger=False

    _=np.arange(tt.samples_per_channel)
    data=np.array([_, _+0.1])
    tt._add_data_if_triggered(data)
    print(tt.ring_buffer.get())
    print(tt.samples_left_to_acquire)
    _+=len(_)
    data=np.array([_, _+0.1])
    tt._add_data_if_triggered(data)
    print(tt.ring_buffer.get())
    print(tt.samples_left_to_acquire)



if __name__ == '__main__':
    test_ring_buffer()

