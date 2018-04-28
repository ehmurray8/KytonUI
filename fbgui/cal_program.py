"""Containts the calibration program page."""

from typing import List
import math
import time
from fbgui import file_helper as fh
from fbgui.constants import CAL, TEMP, SWITCH, LASER
from fbgui.program import Program, ProgramType


class CalProgram(Program):
    """Object representation of the Calibration Program page."""
    def __init__(self, master):
        cal_type = ProgramType(CAL)
        super().__init__(master, cal_type)

    def program_loop(self, thread_id):
        """Runs the calibration."""
        temps_arr = self.options.get_target_temps()
        self.cal_loop(temps_arr, thread_id)
        self.create_excel()
        self.pause_program()

    def cal_loop(self, temps: List[float], thread_id):
        for cycle_num in range(self.options.num_cal_cycles.get()):
            if not self.master.thread_map[thread_id]:
                self.disconnect_devices()
                print("Closing thread: {}".format(thread_id))
                return

            self.master.conn_dev(TEMP)
            temp = float((self.master.temp_controller.get_temp_k()))
            heat = False
            if temp < float(temps[0]) + 274.15 - 5:
                heat = True

            if not self.master.thread_map[thread_id]:
                self.disconnect_devices()
                print("Closing thread: {}".format(thread_id))
                return

            self.set_oven_temp(temps[0] - 5, heat)
            self.disconnect_devices()
            while not self.reset_temp(temps):
                time.sleep(self.options.temp_interval.get())
                if not self.master.thread_map[thread_id]:
                    print("Closing thread: {}".format(thread_id))
                    return

            for temp in temps:
                self.set_oven_temp(temp)
                self.disconnect_devices()
                if not self.master.thread_map[thread_id]:
                    print("Closing thread: {}".format(thread_id))
                    return
                time.sleep(self.options.temp_interval.get())

                while not self.check_drift_rate(thread_id, cycle_num + 1):
                    time.sleep(self.options.temp_interval.get())
                    if not self.master.thread_map[thread_id]:
                        print("Closing thread: {}".format(thread_id))
                        return

            self.set_oven_temp(temps[0] - 5, False)
            if self.options.cooling.get():
                self.master.oven.cooling_on()
            self.disconnect_devices()

            if not self.master.thread_map[thread_id]:
                print("Closing thread: {}".format(thread_id))
                return
            while not self.reset_temp(temps):
                time.sleep(self.options.temp_interval.get())
                if not self.master.thread_map[thread_id]:
                    print("Closing thread: {}".format(thread_id))
                    return

    def reset_temp(self, temps: List[float]) -> bool:
        """Checks to see if the the temperature is within the desired amount."""
        self.master.conn_dev(TEMP)
        temp = float((self.master.temp_controller.get_temp_k()))
        self.disconnect_devices()
        if temp <= float(temps[0] + 274.15) - 5:
            return True
        return False

    def check_drift_rate(self, thread_id, cycle_num) -> bool:
        self.master.conn_dev(TEMP)
        self.master.conn_dev(LASER)
        if sum(len(switch) for switch in self.switches):
            self.master.conn_dev(SWITCH)

        start_time = time.time()
        if not self.master.thread_map[thread_id]:
            print("Closing thread: {}".format(thread_id))
            return False
        start_temp = float(self.master.temp_controller.get_temp_k())
        waves, amps = self.get_wave_amp_data(thread_id)
        if not self.master.thread_map[thread_id]:
            print("Closing thread: {}".format(thread_id))
            return False
        curr_temp = float(self.master.temp_controller.get_temp_k())
        curr_time = time.time()
        self.disconnect_devices()

        drift_rate = math.fabs(start_temp - curr_temp) / math.fabs(start_time - curr_time)
        drift_rate *= 60000.

        if not self.master.thread_map[thread_id]:
            print("Closing thread: {}".format(thread_id))
            return False
        if drift_rate <= self.options.drift_rate.get():
            fh.write_db(self.options.file_name.get(), self.snums, curr_time,
                        curr_temp, waves, amps, CAL, self.table, drift_rate, True, cycle_num)
            return True

        if not self.master.thread_map[thread_id]:
            print("Closing thread: {}".format(thread_id))
            return False
        fh.write_db(self.options.file_name.get(), self.snums, curr_time,
                    curr_temp, waves, amps, CAL, self.table, drift_rate, False, cycle_num)
        return False
