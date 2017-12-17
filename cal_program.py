"""Containts the calibration program page."""

# pylint: disable=import-error, relative-import, missing-super-argument
import time
from program import Page, ProgramType
from constants import CAL
import dev_helper
import file_helper
import options_frame
import threading


class CalPage(Page):
    """Object representation of the Calibration Program page."""
    def __init__(self, master):
        cal_type = ProgramType(CAL)
        super().__init__(master, cal_type)
        self.temp_mutex = threading.Semaphore()
        self.cycle_mutex = threading.Semaphore()

    def program_loop(self):
        """Runs the calibration."""
        temps_arr = self.options.get_target_temps()

        for _ in range(self.options.num_cal_cycles.get()):
            print("Cycle acquire")
            self.cycle_mutex.acquire()
            for temp in temps_arr:
                print("Temp acquire")
                self.temp_mutex.acquire()
                self.master.oven.set_temp(temp)
                self.master.oven.cooling_off()
                self.master.oven.heater_on()
                print("take first reading")

                start_temp = float(self.master.temp_controller.get_temp_k())
                waves, amps = dev_helper.avg_waves_amps(self.master.laser, self.master.switch, self.switches,
                                                        self.options.num_pts.get(), self.master.after)

                start_temp += float(self.master.temp_controller.get_temp_k())
                start_temp /= 2
                start_time = time.time()

                print("write first reading")
                # Need to write csv file init code
                file_helper.write_csv_file(self.options.file_name.get(), self.snums, start_time,
                                           start_temp, waves, amps, options_frame.CAL, False, 0.0)

                thread = threading.Thread(target=self.__check_drift_rate, args=(start_time, start_temp))
                self.after(int(self.options.temp_interval.get() * 1000 + .5), thread.start)
                #thread = threading.Thread(target=self.__check_drift_rate, args=(start_time, start_temp))
                #self.after(int(self.options.temp_interval.get() * 1000 + .5), thread.start)

            self.master.oven.heater_off()
            self.master.oven.set_temp(temps_arr[0])

            if self.options.cooling.get():
                self.master.oven.cooling_on()

            self.check_temp(temps_arr)

    def check_temp(self, temps_arr):
        """Checks to see if the the temperature is within the desired amount."""
        temp = float(self.master.temp_controller.get_temp_c())
        if temp >= float(temps_arr[0]) - .1:
            thread = threading.Thread(target=self.__check_drift_rate, args=(temps_arr, ))
            self.after(int(self.options.temp_interval.get() * 1000 + .5), thread.start)
        else:
            print("cycle release")
            self.cycle_mutex.release()

    def __check_drift_rate(self, last_time, last_temp):
        print("take reading")
        curr_temp = float(self.master.temp_controller.get_temp_k())

        waves, amps = dev_helper.avg_waves_amps(self.master.laser, self.master.switch, self.switches,
                                                self.options.num_pts.get(), self.master.after)

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
            print("temp release")
            self.temp_mutex.release()
        else:
            print("write reading")
            file_helper.write_csv_file(self.options.file_name.get(), self.snums, curr_time,
                                       curr_temp, waves, amps, options_frame.CAL, False, drift_rate)
            thread = threading.Thread(target=self.__check_drift_rate, args=(curr_time, curr_temp))
            self.after(int(self.options.temp_interval.get() * 1000 + .5), thread.start)
