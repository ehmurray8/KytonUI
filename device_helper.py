"""
Gets the amplitude and wavelength data using the Mircon Optics SM125,
and the Optical Switch.
"""
# pylint: disable=import-error, relative-import
import sys
import time
import socket
import _thread
import tkinter as tk
import sm125_wrapper
import optical_switch_wrapper as op_switch_wrapper


def avg_waves_amps(parent):
    """Gets the average wavelengths and powers, updates parent.data_pts."""
    amplitudes_avg = []
    wavelengths_avg = []
    actual_switches = []
    switch_num = 0
    for i, arr in enumerate(parent.switches):
        if len(arr) != 0 and arr[0] != 0:
            actual_switches = arr
            switch_num = i
            break

    num_snums = parent.options.num_pts.get()
    wavelengths_avg, amplitudes_avg, lens = \
        __get_average_data(num_snums, parent.header,
                           parent.program_type.in_prog_msg,
                           parent.sm125, parent.op_switch,
                           switch_num, actual_switches)

    chan_errs = __process_data(parent, lens, actual_switches,
                               wavelengths_avg, amplitudes_avg,
                               switch_num)

    if len(chan_errs) > 0:
        chan_error(chan_errs, parent.chan_error_been_warned)
        parent.chan_error_been_warned = True


def __get_data(header, in_prog_msg, all_waves, all_amps, sm125, op_switch,
               actual_switches):
    keep_going = True
    switch_index = 0
    while keep_going:
        try:
            if len(actual_switches) > switch_index:
                op_switch_wrapper.set_channel(op_switch, 1,
                                              actual_switches[switch_index])
                switch_index += 1
                time.sleep(1.25)
            else:
                keep_going = False
            wavelens, amps, lens = sm125_wrapper.get_data_actual(sm125)
            all_waves.append(wavelens[0])
            all_amps.append(amps[0])
        except socket.error:
            header.configure(text="SM125 Connection Error...Trying Again")
    header.configure(text=in_prog_msg)
    return wavelens, amps, lens


def __get_average_data(num_snums, header, in_prog_msg, sm125, op_switch,
                       switch_num, actual_switches):
    need_init = True
    for i in range(num_snums):
        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            all_waves = []
            all_amps = []
            wavelengths, amplitudes, lens = __get_data(header, in_prog_msg,
                                                       all_waves, all_amps,
                                                       sm125, op_switch,
                                                       actual_switches)
        else:
            wavelengths = [[]]
            amplitudes = [[]]
            lens = [0, 0, 0, 0]

        if need_init:
            wavelengths_avg = [0] * (len(wavelengths[0]) +
                                     len(actual_switches) - 1)
            amplitudes_avg = [0] * (len(amplitudes[0]) +
                                    len(actual_switches) - 1)
            need_init = False

        switch_chan_starting_index = 0
        for i in range(switch_num):
            switch_chan_starting_index += lens[i]

        offset = 0
        for i, wavelength in enumerate(wavelengths[0]):
            if i == switch_chan_starting_index:
                for waves in all_waves:
                    wavelengths_avg[i + offset] += \
                            waves[switch_chan_starting_index]
                    offset += 1
                if offset != 0:
                    offset -= 1
            else:
                wavelengths_avg[i + offset] += wavelength

        offset = 0
        for i, amp in enumerate(amplitudes[0]):
            if i == switch_chan_starting_index:
                for amps in all_amps:
                    amplitudes_avg[i + offset] += \
                            amps[switch_chan_starting_index]
                    offset += 1
                if offset != 0:
                    offset -= 1
            else:
                amplitudes_avg[i + offset] += amp

    wavelengths_avg = [x / num_snums for x in wavelengths_avg]
    amplitudes_avg = [x / num_snums for x in amplitudes_avg]
    return wavelengths_avg, amplitudes_avg, lens


def __process_data(parent, lens, actual_switches, wavelengths_avg,
                   amplitudes_avg, switch_num):
    chan_num = 1
    parent.data_pts = {}
    chan_errs = []
    offset = 0
    for chan in parent.channels:
        max_pts = lens[chan_num-1]
        if chan_num-1 == switch_num:
            max_pts += len(actual_switches)
        temp = chan_num
        start_index = 0
        while temp > 1:
            start_index += lens[temp-2]
            temp -= 1
        start_index += offset
        num_snums = 0
        for snum in chan:
            if num_snums < max_pts:
                parent.data_pts[snum] = (wavelengths_avg[start_index],
                                         amplitudes_avg[start_index])
                start_index += 1
            else:
                chan_errs.append(snum)
                parent.data_pts[snum] = (0, 0)
            num_snums += 1
        if chan_num-1 == switch_num and len(actual_switches) > 1:
            offset = len(actual_switches) - 1
        chan_num += 1
    return chan_errs


def chan_error(snums, warned):
    """
    Creates the error messsage to alert the user not enough fbgs
    are being scanned.
    """
    if not warned:
        errs_str = "SM125 didn't report any data for the serial numbers: "
        need_comma = False
        for snum in snums:
            if need_comma:
                errs_str += ", "
            errs_str += str(snum)
            need_comma = True

        _thread.start_new_thread(lambda: tk.messagebox.showwarning(
            "Scanning error", errs_str), ())
