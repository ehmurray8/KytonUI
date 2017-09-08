import sys
import _thread
import tkinter as tk
import sm125_wrapper

def avg_waves_amps(sm125, channels, header, options, warned):
        """Gets the average wavelengths and powers, returns dictionary SNUM:(wave,power)"""
        #pylint:disable=too-many-locals, too-many-branches, too-many-statements
        amplitudes_avg = []
        wavelengths_avg = []
        count = 0
        need_init = True
        while count < int(options.num_pts.get()):
            if len(sys.argv) > 1 and sys.argv[1] == "-k":
                can_connect = False

                while not can_connect:
                    try:
                        wavelengths, amplitudes, lens = sm125_wrapper.get_data_actual(sm125)
                        can_connect = True
                    except visa.VisaIOError:
                        header.configure(text="SM125 Connection Error...Trying Again")
                header.configure(text="Baking...")
            else:
                wavelengths = [[]]
                amplitudes = [[]]
                lens = [0, 0, 0, 0]

            if need_init:
                wavelengths_avg = [0] * len(wavelengths[0])
                amplitudes_avg = [0] * len(amplitudes[0])
                need_init = False
                i = 0

            i = 0
            for wavelength_list in wavelengths:
                for wavelength in wavelength_list:
                    wavelengths_avg[i] += wavelength
                    i += 1

            i = 0
            for ampl in amplitudes:
                for amp in ampl:
                    amplitudes_avg[i] += amp
                    i += 1

            count += 1

        i = 0
        while i < len(wavelengths_avg):
            wavelengths_avg[i] /= (count)
            amplitudes_avg[i] /= (count)
            i += 1

        chan_num = 1
        data_pts = {}
        chan_errs = []
        for chan in channels:
            max_pts = lens[chan_num-1]
            temp = chan_num
            start_index = 0
            while temp > 1:
                start_index += lens[temp-2]
                temp -= 1
            count = 0
            for snum in chan:
                if count < max_pts:
                    data_pts[snum] = (wavelengths_avg[start_index],
                                      amplitudes_avg[start_index])
                    start_index += 1
                else:
                    chan_errs.append(snum)
                    data_pts[snum] = (0, 0)
                count += 1
            chan_num += 1

        if len(chan_errs) > 0:
            chan_error(chan_errs, warned)
            warned = True
        print(str(data_pts))
        return data_pts, warned


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

