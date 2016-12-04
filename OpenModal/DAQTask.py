
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
"""Module for working with DAQ tasks.

Classes:
    class DAQTask: Handles NI DAQ tasks.

Info:
    @author: janko.slavic@fs.uni-lj.si, martin.cesnik@fs.uni-lj.si 2011-2014
"""
from PyDAQmx import *
import numpy as np
import time
from math import floor, acos
# from scipy.signal import chirp


def get_daq_tasks():
    """ Returns the tasks defined in the NI-DAQmx.

        Returns:
        task_lost : task names
    """
    buffer_size = 20000
    tasks = ctypes.create_string_buffer(buffer_size)
    DAQmxGetSysTasks(tasks, buffer_size)
    task_list = list(map(bytes.strip, tasks.value.split(b',')))
    return task_list

class DAQTask(Task):
    """Handling NI DAQmx task

    Define tasks (Input or Output) in the NI Measurement and Automation Explorer and
    call it with: DAQTask(b'Task name').


    Parameters
    ----------
    task_name: name of the NI Measurement and Automation Explorer task.


    data: acquired or generated data
    done: task done status
    sample_rate: sample rate
    number_of_ch: number of channels
    channel_list: channel names
    number_of_dev: number of devices
    samples_per_ch: how many samples per channel should be acquired
    real_generated_frequency_Hz: the exact sine frequency that is generated
    phase_start: start phase (used when generating signal)
    frequency_start_Hz: start frequency (used when generating signal)
    amplitude_start: start amplitude (used when generating signal)
    cycle_time_s: cycle time when generating signal (real cycle time can be different)

    """

    def __init__(self, task_name, time_out=20):
        """Initialises DAQTask class.

            Parameters
            ----------
            task_name : name of the NI Measurement and Automation Explorer task.
        """
        Task.__init__(self)
        # Declaration of variable passed by reference
        self.time_out = time_out
        self.data = np.array([])
        self.samples_written = 0
        self.done = 0
        self.real_generated_frequency_Hz = 0.
        self.phase_start = 0.
        self.frequency_start_Hz = 0.
        self.amplitude_start = 0.
        self.cycle_time_s = 1.
        _number_of_ch = uInt32()
        _number_of_dev = uInt32()
        _sample_rate = float64()

        self.overload = False

        # number of channels
        DAQmxLoadTask(task_name, byref(self.taskHandle))
        self.GetTaskNumChans(byref(_number_of_ch))
        self.number_of_ch = _number_of_ch.value

        # channel names
        buffer_size = 100
        channels = ctypes.create_string_buffer(buffer_size)
        self.GetTaskChannels(channels, buffer_size)
        self.channel_list = list(map(bytes.strip, channels.value.split(b',')))

        # number of devices
        self.GetTaskNumDevices(byref(_number_of_dev))
        self.number_of_dev = _number_of_dev.value

        # number of samples per ch
        _samples_per_ch = uInt64()
        self.GetSampQuantSampPerChan(byref(_samples_per_ch))
        self.samples_per_ch = _samples_per_ch.value

        # sample rate
        self.GetSampClkRate(byref(_sample_rate))
        self.sample_rate = _sample_rate.value

        # handling continuous measurements
        self.data_residual = None

    def acquire_base(self):
        """Acquires the data from the task.

        Parameters
        ----------
            None

        Returns
        -------
            data : measured values.

        Raises
        ------
            Nothing.
        """
        # allocate data variable
        le = self.samples_per_ch * self.number_of_ch
        data = np.zeros(le, dtype=numpy.float64)
        samples_per_ch = int32()
        #acquire
        self.ReadAnalogF64(DAQmx_Val_Auto, self.time_out, DAQmx_Val_GroupByChannel, data, le, byref(samples_per_ch),
                           None)
        samples_per_ch = samples_per_ch.value
        le = samples_per_ch * self.number_of_ch
        done = bool32()
        #check if the task is done
        self.IsTaskDone(byref(done))
        self.done = done.value
        if self.done == 1:
            self.ClearTask()
        # reshape the data
        data = data[:le].reshape(self.number_of_ch, samples_per_ch)

        #self._update_overload_status()

        return data

    def _update_overload_status(self):
        _overload = bool32()
        self.GetReadOverloadedChansExist(byref(_overload))

        if _overload.value:
            self.overload = True
        else:
            self.overload = False


    def _append_data(self, data):
        """Appends acquired data to self.data.

        Parameters
        ----------
            data : acquired data

        Returns
        -------
            data_ready : True if self.data is full.

        Raises
        ------
            Nothing.
        """

        data_ready = False
        if self.data is None:
            if self.data_residual is None:
                self.data = data
            else:
                self.data = self.data_residual
                self.data = np.concatenate((self.data, data), axis=1)
                self.data_residual = None
        else:
            self.data = np.concatenate((self.data, data), axis=1)

        [_, samples_per_ch] = np.shape(self.data)

        if samples_per_ch > self.samples_per_ch:  # more samples then required
            self.data_residual = self.data[:, self.samples_per_ch:]
            self.data = self.data[:, :self.samples_per_ch]
            data_ready = True

        return data_ready

    def acquire(self, time_out=10., wait_4_all_samples=True, acquire_sleep='auto'):
        """Acquires the data from the task.

        Attributes:
        time_out: maximal waiting time for the measured data to be available
        wait_4_all_samples: return when all samples are acquired
        acquire_sleep: sleep time in seconds between acquisitions in continuous mode

        Returns:
            Nothing.

        Raises:
            Nothing.
        """
        self.time_out = time_out

        self.data = None

        if acquire_sleep == 'auto':
            acquire_sleep = 0.1 * self.samples_per_ch / self.sample_rate

        data = self.acquire_base()
        self._append_data(data)

        if not self.done:
            while wait_4_all_samples:
                data = self.acquire_base()
                wait_4_all_samples = not self._append_data(data)
                time.sleep(acquire_sleep)

    def generate(self, data, clear_task=True):
        """Generate data to the Task

        Parameters
        ----------
            data : the data that should be generated to the task
            clear_task : should the task be cleared at the end

        Returns
        -------
            Nothing.

        Raises
        ------
            Nothing.
        """

        self.data = data
        _samples_written = int32()
        self.WriteAnalogF64(self.data.size, 1, float64(-1), DAQmx_Val_GroupByChannel, self.data,
                            byref(_samples_written), None)
        # DAQmxStartTask(self._task);
        self.samples_written = _samples_written.value
        _done = bool32()
        #DAQmxIsTaskDone(self._task,byref(_done))
        self.done = _done.value
        if clear_task:
            self.WaitUntilTaskDone(10.)
            self.ClearTask()

    def generate_sine(self, frequency_Hz=10., amplitude=1, cycle_time_s=1,
                      clear_task=False):
        """Generate a sine with the defined frequency.

        The generated sine is continuous and the frequency_Hz defines the exact length generated data.

        Parameters
        ----------
            frequency_Hz : the goal frequency; the generated frequency can slightly differ
            amplitude : the amplitude of the sine wave
            cycle_time_s : the cycle time in seconds to be generated
            clear_task : if the task should be cleared after data is send out.

        Returns
        -------
            Nothing.

        Raises
        ------
            Nothing.
        """
        points_cycle = int(round(cycle_time_s * self.sample_rate))  # points of the cycle
        k = int(floor(points_cycle / (
            self.sample_rate / frequency_Hz)))  # how many closed oscillations are there in the cycle time
        points = int(round(k * self.sample_rate / frequency_Hz))  # number of points to generate for closed sine

        self.real_generated_frequency_Hz = k * self.sample_rate / points
        # prepare phase data
        x = np.linspace(-k * np.pi, k * np.pi, points)[
            :-1]  #one point is removed because it is the same as the first of the next cycle
        data = np.array(amplitude * np.sin(x), dtype=numpy.float64)
        self.generate(data, clear_task=clear_task)

    # def generate_chirp(self, frequency_end_Hz=None, amplitude_end=None, method='logarithmic',
    #                    prolog_zeros=0, clear_task=False, nonlinearity_check=False):
    #     """Generate a sine chirp.
    #
    #     The generated chirp starts with the frequency_start_Hz and amplitude_start defined as class
    #     attributes (or previous end).
    #
    #     Parameters
    #     ----------
    #     frequency_end_Hz : the frequency at the end
    #     amplitude_end : amplitude at the end
    #     method : {'linear', 'quadratic', 'logarithmic', 'hyperbolic'}, optional
    #              Kind of frequency sweep.  If not given, `linear` is assumed.
    #              See scipy.signal.chirp notes.
    #     prolog_zeros : number of zeros output before the chirp (usually for delay reasons)
    #     clear_task : if the task should be cleared after data is send out.
    #     nonlinearity_check : if True, two chirps are generated: first with full amplitude and the second with half amplitude
    #
    #     Returns
    #     ----------
    #     Nothing.
    #
    #     Raises
    #     ----------
    #     Nothing.
    #     """
    #
    #     if frequency_end_Hz is None:
    #         frequency_end_Hz = self.frequency_start_Hz
    #     if amplitude_end is None:
    #         amplitude_end = self.amplitude_start
    #
    #     # get remainder
    #     self.phase_start %= 2 * np.pi
    #
    #     # samples per cycle
    #     points_cycle = int(round(self.cycle_time_s * self.sample_rate))
    #
    #     # get time array
    #     t = 1. / self.sample_rate * np.arange(points_cycle)
    #     t1 = t[-1]
    #
    #     # get data
    #     data = chirp(t, self.frequency_start_Hz, t1, frequency_end_Hz, method=method,
    #                  phi=180 * self.phase_start / np.pi)
    #     self.frequency_start_Hz = frequency_end_Hz
    #     self.phase_start = acos(data[-1])
    #
    #     # amplitude
    #     amp = np.linspace(self.amplitude_start, amplitude_end, points_cycle)
    #     self.amplitude_start = amp[-1]
    #
    #     data = np.array(amp * data, dtype=numpy.float64)
    #     if prolog_zeros > 0:
    #         zeros = np.zeros(prolog_zeros, dtype=numpy.float64)
    #         data = np.append(zeros, data, axis=1)
    #     if nonlinearity_check:
    #         data = np.append(data, 0.5 * data, axis=1)
    #
    #     self.generate(data, clear_task=clear_task)

    def generate_random(self, amplitude=1):
        """Generate a random noise

        The generated noise has given amplitude.

        Parameters
        ----------
            amplitude: amplitude of the random noise

        Returns
        -------
            Nothing.

        Raises
        ------
            Nothing.
        """
        data = np.random.random([self.samples_per_ch]) - amplitude / 2

        self.generate(data, clear_task=False)

    def clear_task(self, wait_until_done=True):
        """Clears the task


        Parameters
        ----------
            wait_until_done : wait until the task is done to clear it

        Returns
        -------
            Nothing.

        Raises
        ------
            Nothing.
        """
        if wait_until_done:
            self.WaitUntilTaskDone(10.)
        self.ClearTask()


def acquire_N_samples_example(show=False):
    import matplotlib.pyplot as plt

    t = DAQTask(b'input N samples')  # Set Acquisition Mode to: "N Samples"
    # samples to read 25,6k, rate 25,6kHz
    print('Number of channels %d ' % t.number_of_ch)
    print('Sample click rate %d ' % t.sample_rate)
    t.acquire()
    if show:
        dt = 1. / t.sample_rate
        _time = np.arange(t.samples_per_ch) * dt
        if t.number_of_ch == 1:
            plt.plot(_time, t.data[0])
        else:
            for i in numpy.arange(t.number_of_ch):
                plt.plot(_time[1:-1:10], t.data[i, 1:-1:10])
        plt.show()


def acquire_cont_example(show=False):
    import matplotlib.pyplot as plt

    t = DAQTask(b'input continuous simulated')  # Set Acquisition Mode to: "Continuous Samples"
    print('Number of channels %d ' % t.number_of_ch)
    print('Sample click rate %d ' % t.sample_rate)
    t.acquire()
    print("Samples acquired [%d,%d] " % t.data.shape)
    if show:
        dt = 1. / t.sample_rate
        _time = np.arange(len(t.data[0])) * dt
        if t.number_of_ch == 1:
            plt.plot(_time, t.data[0])
        else:
            for i in numpy.arange(t.number_of_ch):
                plt.plot(_time[1:-1:10], t.data[i, 1:-1:10])
        plt.show()


def constant_sine_example():
    rr = np.arange(45., 49., .25)

    for fr in rr:
        t = DAQTask(b'output')  # Task should be "Continuous"
        t.generate_sine(frequency_Hz=fr, amplitude=4, cycle_time_s=1)
        print("fr=%g, real=%g, diff=%g" % (fr, t.real_generated_frequency_Hz, fr - t.real_generated_frequency_Hz))
        time.sleep(3)
        t.clear_task(wait_until_done=False)
        t.__del__()


def random_example():
    t = DAQTask(b'output')  # Set Generation Mode to: "Continuous Samples"
    t.cycle_time_s = 0.5
    amplitude = 1.  # + 0.1*np.asarray(range(50))
    while 1:
        t.generate_random(amplitude)

    t.clear_task(wait_until_done=False)


def random_cont_output_and_cont_input(wait_4_all_samples=True):
    import matplotlib.pyplot as plt
    # output
    o = DAQTask(b'output')  #Set Generation Mode to: "Continuous Samples"
    data = np.random.random([o.samples_per_ch])
    o.generate(data, clear_task=False)  #the output will run until task cleared
    #input
    i = DAQTask(b'input continuous')  #Set Acquisition Mode to: "Continuous Samples"
    print("Number of channels %d " % i.number_of_ch)
    print("Sample click rate %d " % i.sample_rate)
    #figure
    t = np.arange(i.samples_per_ch) * 1. / i.sample_rate
    plt.ion()
    fig = plt.figure()
    ax = fig.add_subplot(111)
    line1, = ax.plot(t, np.zeros(i.samples_per_ch), 'r-')  # Returns a tuple of line objects, thus the comma
    plt.ylim(ymin=-10, ymax=10)
    fig.canvas.draw()

    while True:
        i.acquire(wait_4_all_samples=wait_4_all_samples)
        si = i.data[0].size
        print("Samples acquired %d " % si)
        if si > 0:
            add_z = i.samples_per_ch - si
            line1.set_ydata(np.append(i.data[0], np.zeros([add_z])))
            fig.canvas.draw()
        time.sleep(0.15)


def test_append_data():
    t = DAQTask(b'input continuous simulated')  # Set Acquisition Mode to: "Continuous Samples",
    # set sampling to 2560Hz, number of samples 2560

    print('Number of channels %d ' % t.number_of_ch)
    print('Sample click rate %d ' % t.sample_rate)

    print(30 * '-')
    print('Shorter than nr of samples')
    print(30 * '-')
    N = 500
    da = np.arange(N)
    data = np.array([da, -da])

    t.data = None

    goOn = True
    while goOn:
        goOn = not t._append_data(data)

    print(np.shape(t.data))
    print(np.shape(t.data_residual))

    t.data = None

    goOn = True
    while goOn:
        goOn = not t._append_data(data)

    print(np.shape(t.data))
    print(np.shape(t.data_residual))

    print(30 * '-')
    print('Longer than nr of samples')
    print(30 * '-')

    N = 3000
    da = np.arange(N)
    data = np.array([da, -da])

    t.data = None

    goOn = True
    while goOn:
        goOn = not t._append_data(data)

    print(np.shape(t.data))
    print(np.shape(t.data_residual))

    t.data = None

    goOn = True
    while goOn:
        goOn = not t._append_data(data)

    print(np.shape(t.data))
    print(np.shape(t.data_residual))


def testt():
    import matplotlib.pyplot as plt

    o = DAQTask(b'haet out')  # Task should be "Continuous"
    o.frequency_start_Hz = 1000.
    o.amplitude_start = 5.
    o.cycle_time_s = 1
    o.generate_chirp(frequency_end_Hz=20000, prolog_zeros=20000)
    # time.sleep(3)
    #o.clear_task(wait_until_done=False)
    i = DAQTask(b'haet force')
    i.acquire()
    plt.plot(i.data[3])
    plt.show()
    o.ClearTask()


if __name__ == "__main__":
    # import cProfile
    #test_append_data()
    #cProfile.run("chirp_example()")
    #acquire_N_samples_example(show=True)
    acquire_cont_example(show=True)
    #random_cont_output_and_cont_input()
    #random_cont_output_and_cont_input(wait_4_all_samples = False)
    #constant_sine_example()
    #chirp_example()
    #testt()
    #random_example()
    #get_daq_tasks()