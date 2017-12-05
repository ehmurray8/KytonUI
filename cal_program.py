"""Containts the calibration program page."""

# pylint: disable=import-error, relative-import, missing-super-argument
import time
from program import Page, ProgramType, CAL_ID
import dev_helper
import file_helper
import options_frame


class CalPage(Page):
    """Object representation of the Calibration Program page."""
    def __init__(self, master):
        cal_type = ProgramType(CAL_ID)
        super().__init__(master, cal_type)
        self.finished_point = False
        self.temp_is_good = False

    def program_loop(self):
        """Runs the calibration."""
        temps_arr = self.options.get_target_temps()

        cycle_num = 0
        while cycle_num < self.options.num_cal_cycles.get():
            for temp in temps_arr:
                self.master.oven.set_temp(temp)
                self.master.oven.cooling_off()
                self.master.oven.heater_on()

                start_temp = float(self.master.temp_controller.get_temp_k())
                waves, amps = dev_helper.avg_waves_amps(self.master.laser, self.master.switch,
                                                        self.switches, self.options.num_pts.get(),
                                                        self.master.after)

                for snum in self.snums:
                    waves.append(self.data_pts[snum][0])
                    amps.append(self.data_pts[snum][1])

                start_temp += float(self.master.temp_controller.get_temp_k())
                start_temp /= 2
                start_time = time.time()

                # Need to write csv file init code
                file_helper.write_csv_file(self.options.file_name.get(), self.snums, start_time,
                                           start_temp, waves, amps, options_frame.CAL, False, 0.0)

                self.finished_point = False
                # pylint: disable=cell-var-from-loop
                # CHECK TO MAKE SURE THIS IS OK
                self.after(60000, lambda: self.__check_drift_rate(start_time, start_temp))
                while not self.finished_point:
                    pass

            self.master.oven.heater_off()
            self.master.oven.set_temp(temps_arr[0])

            if self.options.cooling.get():
                self.master.oven.cooling_on()

            self.check_temp(temps_arr)
            self.temp_is_good = False
            while not self.temp_is_good:
                pass

            cycle_num += 1

    def check_temp(self, temps_arr):
        """Checks to see if the the temperature is within the desired amount."""
        temp = float(self.master.temp_controller.get_temp_c())
        while temp > float(temps_arr[0]):
            temp = float(self.master.temp_controller.get_temp_c())
            time.sleep(.1)
        self.temp_is_good = True

    def __check_drift_rate(self, last_time, last_temp):
        curr_temp = float(self.master.temp_controller.get_temp_k())

        waves, amps = dev_helper.avg_waves_amps(self.master.laser, self.master.switch,
                                                self.switches, self.options.num_pts.get(),
                                                self.master.after)

        curr_temp += float(self.master.temp_controller.get_temp_k())
        curr_temp /= 2
        curr_time = time.time()

        time_ratio_min = curr_time / last_time / 60
        temp_ratio_mk = curr_temp / last_temp / 1000

        drift_rate = temp_ratio_mk / time_ratio_min

        if drift_rate <= self.options.drift_rate.get():
            # record actual point
            file_helper.write_csv_file(self.options.file_name.get(), self.snums, curr_time,
                                       curr_temp, waves, amps, options_frame.CAL, True, drift_rate)
            self.finished_point = True
        else:
            file_helper.write_csv_file(self.options.file_name.get(), self.snums, curr_time,
                                       curr_temp, waves, amps, options_frame.CAL, False, drift_rate)
            self.after(60000, lambda: self.__check_drift_rate(
                curr_time, curr_temp))
