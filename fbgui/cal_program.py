"""Containts the calibration program page."""

import time
from fbgui import file_helper as fh
from fbgui.constants import CAL, TEMP, SWITCH, LASER, OVEN
from fbgui.program import Program, ProgramType


class CalProgram(Program):
    """Object representation of the Calibration Program page."""
    def __init__(self, master):
        cal_type = ProgramType(CAL)
        super().__init__(master, cal_type)

    def program_loop(self):
        """Runs the calibration."""
        temps_arr = self.options.get_target_temps()
        self.cal_loop(temps_arr)

    def cal_loop(self, temps_arr):
        for _ in range(self.options.num_cal_cycles.get()):
            for temp in temps_arr:
                while True:
                    self.set_oven_temp(temp)
                    self.master.conn_dev(TEMP)
                    self.master.conn_dev(LASER)
                    if sum(len(switch) for switch in self.switches):
                        self.master.conn_dev(SWITCH)
                    start_temp = self.master.temp_controller.get_temp_k()
                    waves, amps = self.get_wave_amp_data()
                    start_temp += self.master.temp_controller.get_temp_k()
                    start_temp /= 2
                    start_time = time.time()

                    self.disconnect_devices()

                    # Need to write csv file init code
                    fh.write_db(self.options.file_name.get(), self.snums, start_time,
                                start_temp, waves, amps, CAL, self.table, False, 0.0)
                    if self.__check_drift_rate(start_time, start_temp):
                        break
                    else:
                        time.sleep(int(self.options.temp_interval.get()*1000 + .5))

            self.master.conn_dev(OVEN)
            self.master.oven.heater_off()
            self.master.oven.set_temp(temps_arr[0])

            if self.options.cooling.get():
                self.master.oven.cooling_on()

            self.disconnect_devices()
            self.reset_temp(temps_arr)

    def reset_temp(self, temps_arr):
        """Checks to see if the the temperature is within the desired amount."""
        self.master.conn_dev(TEMP)
        temp = float((self.master.temp_controller.get_temp_k()))
        while temp >= float(temps_arr[0]) + .1:
            time.sleep(int(self.options.temp_interval.get()*1000 + .5))
            temp = float(self.master.temp_controller.get_temp_k())
        self.disconnect_devices()

    def get_drift_rate(self, last_time, last_temp):
        self.master.conn_dev(TEMP)
        self.master.conn_dev(LASER)
        if sum(len(switch) for switch in self.switches):
            self.master.conn_dev(SWITCH)
        waves, amps = self.get_wave_amp_data()
        curr_temp = float(self.master.temp_controller.get_temp_k())
        curr_temp += float((self.master.temp_controller.get_temp_k()))
        self.disconnect_devices()
        curr_temp /= 2
        curr_time = time.time()

        time_ratio_min = curr_time / last_time / 60
        temp_ratio_mk = curr_temp / last_temp / 1000

        drift_rate = temp_ratio_mk / time_ratio_min
        return drift_rate, curr_temp, curr_time, waves, amps

    def __check_drift_rate(self, last_time, last_temp):
        drift_rate, curr_temp, curr_time, waves, amps = self.get_drift_rate(last_time, last_temp)
        while drift_rate > self.options.drift_rate.get():
            fh.write_db(self.options.file_name.get(), self.snums, curr_time,
                        curr_temp, waves, amps, CAL, self.table, False, drift_rate)
            time.sleep(int(self.options.temp_interval.get()*1000 + .5))
            drift_rate, curr_temp, curr_time, waves, amps = self.get_drift_rate(last_time, last_temp)

        # record actual point
        fh.write_db(self.options.file_name.get(), self.snums, curr_time,
                    curr_temp, waves, amps, CAL, self.table, True, drift_rate)
