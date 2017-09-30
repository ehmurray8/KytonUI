import sys
import time
import _thread
import tkinter as tk
import sm125_wrapper
import optical_switch_wrapper as op_switch_wrapper

#def avg_waves_amps(sm125, optical_switch, channels, switches, header, options, warned):
def avg_waves_amps(parent):
        """Gets the average wavelengths and powers, returns dictionary SNUM:(wave,power)"""
        #pylint:disable=too-many-locals, too-many-branches, too-many-statements
        amplitudes_avg = []
        wavelengths_avg = []

        actual_switches = []
        switch_chan = 0
        done = False
        for i, arr in enumerate(parent.switches):
            if len(arr) != 0 and arr[0] != 0:
                actual_switches = arr
                switch_num = i
                break
        
        count = 0
        need_init = True

        while count < int(parent.options.num_pts.get()):
            if len(sys.argv) > 1 and sys.argv[1] == "-k":
                all_wavelengths = []
                all_amplitudes = []
                keep_going = True

                switch_index = 0
                while keep_going:
                    try:
                        if len(actual_switches) > switch_index:
                            op_switch_wrapper.set_channel(parent.op_switch, 1, actual_switches[switch_index])
                            switch_index += 1
                            time.sleep(1.25)
                        else:
                            keep_going = False
                            break
                            
                        wavelengths, amplitudes, lens = sm125_wrapper.get_data_actual(parent.sm125)
                        all_wavelengths.append(wavelengths[0])
                        all_amplitudes.append(amplitudes[0])
                    except visa.VisaIOError:
                        parent.header.configure(text="SM125 Connection Error...Trying Again")
                parent.header.configure(text="Baking...")
            else:
                wavelengths = [[]]
                amplitudes = [[]]
                lens = [0, 0, 0, 0]

            if need_init:
                wavelengths_avg = [0] * (len(wavelengths[0]) + len(actual_switches) - 1)
                amplitudes_avg = [0] * (len(amplitudes[0]) + len(actual_switches) - 1)
                need_init = False

            switch_chan_starting_index = 0
            for i in range(switch_num):
                switch_chan_starting_index += lens[i]

            offset = 0
            for i, wavelength in enumerate(wavelengths[0]):
                if i == switch_chan_starting_index:
                    for waves in all_wavelengths:
                        wavelengths_avg[i + offset] += waves[switch_chan_starting_index]
                        offset += 1
                    if offset != 0:
                        offset -= 1
                else:
                    wavelengths_avg[i + offset] += wavelength

            offset = 0
            for i, amp in enumerate(amplitudes[0]):
                if i == switch_chan_starting_index:
                    for amps in all_amplitudes:
                        amplitudes_avg[i + offset] += amps[switch_chan_starting_index]
                        offset += 1
                    if offset != 0:
                        offset -= 1
                else:
                    amplitudes_avg[i + offset] += amp

            count += 1
            
        for i in range(len(wavelengths_avg)):
            wavelengths_avg[i] /= (count)
            amplitudes_avg[i] /= (count)

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
            count = 0
            for snum in chan:
                if count < max_pts:
                    parent.data_pts[snum] = (wavelengths_avg[start_index],
                                             amplitudes_avg[start_index])
                    start_index += 1
                else:
                    chan_errs.append(snum)
                    parent.data_pts[snum] = (0, 0)
                count += 1
            if chan_num-1 == switch_num and len(actual_switches) > 1:
                offset = len(actual_switches) - 1
            chan_num += 1

        if len(chan_errs) > 0:
            chan_error(chan_errs, parent.chan_error_been_warned)
            parent.chan_error_been_warned = True
        #return data_pts, warned


def chan_error(snums, warned):
        """Creates the error messsage to alert the user not enough fbgs are being scanned."""
        if not warned:
            errs_str = "Micron Optics didn't report any data for the serial numbers: "
            need_comma = False
            for snum in snums:
                if need_comma:
                    errs_str += ", "
                errs_str += str(snum)
                need_comma = True

            #TODO make this threaded
            _thread.start_new_thread(lambda: tk.messagebox.showwarning("Scanning error", errs_str), ())
            #tk.messagebox.showwarning("Scanning error", errs_str)

