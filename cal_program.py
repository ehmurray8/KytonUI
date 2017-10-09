from program import Page, ProgramType, CAL_ID

def class CalPage(Page):
    def __init__(self, parent, master):
        cal_type = ProgramType(CAL_ID)
        super().__init__(parent, master, cal_type)


    def run_cal_loop(self):
        """Runs the calibration."""
        temps_arr = self.options.get_target_temps()

        cycle_num = 0
        while cycle_num < self.options.num_cal_cycles.get():
            for temp in temps_arr:
                oven_wrapper.set_temp(self.oven, temp)
                oven_wrapper.cooling_off(self.oven)
                oven_wrapper.heater_on(self.oven)

                start_temp = controller_wrapper.get_temp_k(self.controller)
                
                start_temp = float(start_temp[:-4])

                wavelengths_avg = []
                amplitudes_avg = []
                data_pts, self.chan_error_been_warned = \
                          device_helper.avg_waves_amps(self.sm125, self.op_switch, self.channels, self.switches, \
                          self.header, self.options, self.chan_error_been_warned)

                for snum in self.snums:
                    wavelengths_avg.append(data_pts[snum][0])
                    amplitudes_avg.append(data_pts[snum][1])

                start_temp += float(controller_wrapper.get_temp_k(self.controller)[:-4])
                start_temp /= 2
                start_time = time.time()

                #Need to write csv file init code
                file_helper.write_csv_file(self.options.file_name.get(), self.snums, start_time, \
                                           start_temp, wavelengths_avg, amplitudes_avg, \
                                           options_panel.CAL, False, 0.0)

                self.finished_point = False
                self.after(60000, lambda: self.__check_drift_rate(start_time, start_temp))
                while(not self.finished_point):
                    pass

            oven_wrapper.heater_off(self.oven)
            oven_wrapper.set_temp(self.oven, temps_arr[0])

            if self.options.cooling.get():
                oven_wrapper.cooling_on(self.oven)

            _thread.start_new_thread(lambda: self.check_temp(temps_arr), ())
            self.temp_is_good = False
            while(not self.temp_is_good):
                pass

            cycle_num += 1

    def check_temp(self, temps_arr):
        temp = float(controller_wrapper.get_temp_c(self.controller)[:-4])
        while temp > float(temps_arr[0]):
            temp = float(controller_wrapper.get_temp_c(self.controller)[:-4])
            time.sleep(.1)
        self.temp_is_good = True


    def __check_drift_rate(self, last_time, last_temp):
        curr_temp = float(controller_wrapper.get_temp_k(self.controller)[:-4])

        data_pts, self.chan_error_been_warned = \
                  device_helper.avg_waves_amps(self.sm125, self.channels, self.switches, \
                  self.header, self.options, self.chan_error_been_warned)

        wavelengths_avg = []
        amplitudes_avg = []
        for snum in self.snums:
            wlen = data_pts[snum][0]
            amp = data_pts[snum][1]
            wavelengths_avg.append(wlen)
            amplitudes_avg.append(amp)

        curr_temp += float(controller_wrapper.get_temp_k(self.controller)[:-4])
        curr_temp /= 2
        curr_time = time.time()

        time_diff = float(curr_time - last_time)
        temp_diff = float(curr_temp - last_temp)

        time_ratio_min = curr_time / last_time / 60
        temp_ratio_mk = curr_temp / last_temp / 1000

        drift_rate = temp_ratio_mk / time_ratio_min

        if drift_rate <= self.options.drift_rate.get():
            #record actual point
            file_helper.write_csv_file(self.options.file_name.get(), self.snums, curr_time, \
                                           curr_temp, wavelengths_avg, amplitudes_avg, \
                                           options_panel.CAL, True, drift_rate)
            self.finished_point = True
        else:
            file_helper.write_csv_file(self.options.file_name.get(), self.snums, curr_time, \
                                           curr_temp, wavelengths_avg, amplitudes_avg, \
                                           options_panel.CAL, False, drift_rate)
            self.after(60000, lambda: self.__check_drift_rate(curr_time, curr_temp))
