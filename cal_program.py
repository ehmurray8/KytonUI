"""Containts the calibration program page."""

import time
from typing import List
import math
import visa
import file_helper as fh
from constants import CAL, TEMP
from program import Program, ProgramType
from messages import MessageType, Message


class CalProgram(Program):
    """Object representation of the Calibration Program page."""
    def __init__(self, master):
        cal_type = ProgramType(CAL)
        super().__init__(master, cal_type)

    def program_loop(self, thread_id):
        """Runs the calibration."""
        temps_arr = self.options.get_target_temps()
        self.cal_loop(temps_arr, thread_id)
        if self.master.thread_map[thread_id]:
            self.create_excel()
            self.pause_program()

    def sleep(self, thread_id):
        start_time = time.time()
        while time.time() - start_time < self.options.temp_interval.get():
            time.sleep(.5)
            if not self.master.thread_map[thread_id]:
                return False
        return True

    def cal_loop(self, temps: List[float], thread_id):
        last_cycle_num = fh.get_last_cycle_num(self.options.file_name.get(), CAL)
        if last_cycle_num == self.options.num_cal_cycles.get():
            self.master.main_queue.put(Message(MessageType.WARNING, "Calibration Program Complete",
                                               "The calibration program has already completed the specified {} cycles"
                                               .format(self.options.num_cal_cycles.get())))
        for cycle_num in range(self.options.num_cal_cycles.get() - last_cycle_num):
            cycle_num += last_cycle_num
            if not self.master.thread_map[thread_id]:
                return

            temp = None
            while temp is None:
                try:
                    self.master.conn_dev(TEMP, thread_id)
                    temp = float((self.master.temp_controller.get_temp_k()))
                except (AttributeError, visa.VisaIOError):
                    pass
            kwargs = {"force_connect": True, "thread_id": thread_id}
            if temp < float(temps[0]) + 274.15 - 5:
                kwargs["heat"] = True
            else:
                kwargs["cooling"] = True

            if not self.master.thread_map[thread_id]:
                return
            self.set_oven_temp(temps[0] - 5, **kwargs)
            self.disconnect_devices()
            while not self.reset_temp(temps, thread_id):
                if not self.sleep(thread_id):
                    return

            for temp in temps:
                self.set_oven_temp(temp, heat=True, force_connect=True)
                self.disconnect_devices()
                if not self.sleep(thread_id):
                    return
                while not self.check_drift_rate(thread_id, cycle_num + 1):
                    if not self.sleep(thread_id):
                        return

            self.set_oven_temp(temps[0] - 5, cooling=True, force_connect=True)
            if self.options.cooling.get():
                self.master.oven.cooling_on()
            self.disconnect_devices()

            if not self.master.thread_map[thread_id]:
                return
            while not self.reset_temp(temps, thread_id):
                if not self.sleep(thread_id):
                    return

    def reset_temp(self, temps: List[float], thread_id) -> bool:
        """Checks to see if the the temperature is within the desired amount."""
        while True:
            try:
                self.master.conn_dev(TEMP, thread_id)
                temp = float((self.master.temp_controller.get_temp_k()))
                self.disconnect_devices()
                if temp <= float(temps[0] + 274.15) - 5:
                    return True
                return False
            except (AttributeError, visa.VisaIOError):
                pass

    def check_drift_rate(self, thread_id, cycle_num) -> bool:
        while True:
            try:
                self.master.conn_dev(TEMP, thread_id)
                start_time = time.time()
                if not self.master.thread_map[thread_id]:
                    return False
                start_temp = float(self.master.temp_controller.get_temp_k())
                waves, amps = self.get_wave_amp_data(thread_id)
                if not self.master.thread_map[thread_id]:
                    return False
                curr_temp = float(self.master.temp_controller.get_temp_k())
                curr_time = time.time()
                self.disconnect_devices()

                drift_rate = math.fabs(start_temp - curr_temp) / math.fabs(start_time - curr_time)
                drift_rate *= 60000.

                if not self.master.thread_map[thread_id]:
                    return False
                if drift_rate <= self.options.drift_rate.get():
                    fh.write_db(self.options.file_name.get(), self.snums, curr_time, curr_temp, waves, amps, CAL,
                                self.table, self.master.main_queue, drift_rate, True, cycle_num)
                    return True

                if not self.master.thread_map[thread_id]:
                    return False
                fh.write_db(self.options.file_name.get(), self.snums, curr_time, curr_temp, waves, amps, CAL,
                            self.table, self.master.main_queue, drift_rate, False, cycle_num)
                return False
            except (AttributeError, visa.VisaIOError):
                pass
