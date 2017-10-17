"""
Gets the amplitude and wavelength data using the Mircon Optics SM125,
and the Optical Switch.
"""
# pylint: disable=import-error, relative-import
import sys
import time
import socket
import threading
import tkinter as tk


def avg_waves_amps(parent):
    """Gets the average wavelengths and powers, updates data_pts."""
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

    chan_errs, data_pts = __process_data(parent, lens, actual_switches,
                                         wavelengths_avg, amplitudes_avg,
                                         switch_num)

    if len(chan_errs) > 0:
        chan_error(chan_errs, parent.chan_error_been_warned, parent.master)
        parent.chan_error_been_warned = True

    parent.thread_queue.put(data_pts)


def __get_data(header, in_prog_msg, all_waves, all_amps, sm125, op_switch,
               actual_switches):
    keep_going = True
    switch_index = 0
    while keep_going:
        try:
            if len(actual_switches) > switch_index:
                op_switch.set_channel(actual_switches[switch_index])
                switch_index += 1
                time.sleep(1.25)
            else:
                keep_going = False
            wavelens, amps, lens = sm125.get_data()
            all_waves.append(wavelens)
            all_amps.append(amps)
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
            wavelengths_avg = [0] * (len(wavelengths) +
                                     len(actual_switches) - 1)
            amplitudes_avg = [0] * (len(amplitudes) +
                                    len(actual_switches) - 1)
            need_init = False

        switch_chan_starting_index = 0
        for i in range(switch_num):
            switch_chan_starting_index += lens[i]

        offset = 0
        for i, wavelength in enumerate(wavelengths):
            if i == switch_chan_starting_index:
                for waves in all_waves:
                    wavelengths_avg[i + offset] += \
                        waves[switch_chan_starting_index]
                    offset += 1
                if offset != 0:
                    offset -= 1
            else:
                if i + offset < len(wavelengths_avg):
                    wavelengths_avg[i + offset] += wavelength

        offset = 0
        for i, amp in enumerate(amplitudes):
            if i == switch_chan_starting_index:
                for amps in all_amps:
                    amplitudes_avg[i + offset] += \
                        amps[switch_chan_starting_index]
                    offset += 1
                if offset != 0:
                    offset -= 1
            else:
                if i + offset < len(amplitudes_avg):
                    amplitudes_avg[i + offset] += amp

    wavelengths_avg = [x / num_snums for x in wavelengths_avg]
    amplitudes_avg = [x / num_snums for x in amplitudes_avg]
    return wavelengths_avg, amplitudes_avg, lens


def __process_data(parent, lens, actual_switches, wavelengths_avg,
                   amplitudes_avg, switch_num):
    chan_num = 1
    data_pts = {}
    chan_errs = []
    offset = 0
    for chan in parent.channels:
        max_pts = lens[chan_num - 1]
        if chan_num - 1 == switch_num:
            max_pts += len(actual_switches)
        temp = chan_num
        start_index = 0
        while temp > 1:
            start_index += lens[temp - 2]
            temp -= 1
        start_index += offset
        num_snums = 0
        for snum in chan:
            if num_snums < max_pts:
                data_pts[snum] = (wavelengths_avg[start_index],
                                  amplitudes_avg[start_index])
                start_index += 1
            else:
                chan_errs.append(snum)
                data_pts[snum] = (0, 0)
            num_snums += 1
        if chan_num - 1 == switch_num and len(actual_switches) > 1:
            offset = len(actual_switches) - 1
        chan_num += 1
    return chan_errs, data_pts


def add_to_queue(master, errs_str):
    """Adds the warning to the main_queue to properly handle threading."""
    master.main_queue.put(
        (tk.messagebox.showwarning, ("Scanning error", errs_str), {}))


def chan_error(snums, warned, master):
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

        threading.Thread(target=add_to_queue, args=(master, errs_str)).start()
