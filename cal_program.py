"""Containts the calibration program page."""

import time
import math
import file_helper as fh
from constants import CAL, TEMP, SWITCH, LASER, OVEN
from program import Program, ProgramType


class CalProgram(Program):
    """Object representation of the Calibration Program page."""
    def __init__(self, master):
        cal_type = ProgramType(CAL)
        super().__init__(master, cal_type)

    def program_loop(self):
        """Runs the calibration."""
        temps_arr = self.options.get_target_temps()
        self.cal_loop(temps_arr)
        self.create_excel()

    def cal_loop(self, temps_arr):
        print("Num cycles: {}".format(self.options.num_cal_cycles.get()))
        print("Temps arr: {}".format(temps_arr))
        for _ in range(self.options.num_cal_cycles.get()):
            self.master.conn_dev(TEMP)
            temp = float((self.master.temp_controller.get_temp_k()))
            heat = False
            if temp < temps_arr[0]:
                heat = True
            self.set_oven_temp(temps_arr[0], heat)
            self.disconnect_devices()

            while not self.reset_temp(temps_arr):
                time.sleep(self.options.temp_interval.get())

            for temp in temps_arr:
                print("Setting temp: {}".format(temp))
                self.set_oven_temp(temp)
                self.disconnect_devices()
                time.sleep(self.options.temp_interval.get())

                while not self.check_drift_rate():
                    time.sleep(self.options.temp_interval.get())

            self.set_oven_temp(temps_arr[0], False)
            if self.options.cooling.get():
                self.master.oven.cooling_on()
            self.disconnect_devices()

            while not self.reset_temp(temps_arr):
                time.sleep(self.options.temp_interval.get())

    def reset_temp(self, temps_arr):
        """Checks to see if the the temperature is within the desired amount."""
        print("Resetting temp...")
        self.master.conn_dev(TEMP)
        temp = float((self.master.temp_controller.get_temp_k()))
        print("Temperature: {}".format(temp))
        self.disconnect_devices()
        if temp < float(temps_arr[0]) + .1:
            return True
        return False

    def check_drift_rate(self):
        print("Checking drift rate...")
        self.master.conn_dev(TEMP)
        self.master.conn_dev(LASER)
        if sum(len(switch) for switch in self.switches):
            self.master.conn_dev(SWITCH)

        start_time = time.time()
        start_temp = float(self.master.temp_controller.get_temp_k())
        waves, amps = self.get_wave_amp_data()
        curr_temp = float(self.master.temp_controller.get_temp_k())
        curr_time = time.time()
        self.disconnect_devices()

        print("Start time: {}, Start temp: {}".format(start_time, start_temp))
        print("Waves: {}, Amps: {}".format(waves, amps))
        print("Curr time: {}, Curr temp".format(curr_time, curr_temp))

        drift_rate = math.fabs(start_temp - curr_temp) / math.fabs(start_time - curr_time)
        drift_rate *= 60000.

        print("Drift rate: {}".format(drift_rate))

        if drift_rate <= self.options.drift_rate.get():
            print("Writing real point...")
            fh.write_db(self.options.file_name.get(), self.snums, curr_time,
                        curr_temp, waves, amps, CAL, self.table, drift_rate, True)
            return True

        print("Writing point...")
        fh.write_db(self.options.file_name.get(), self.snums, curr_time,
                    curr_temp, waves, amps, CAL, self.table, drift_rate, False)
        return False
