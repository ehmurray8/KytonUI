"""Contains the calibration program specific logic."""

from typing import List
import math
import time
import visa
import datetime
from uuid import UUID
from fbgui import file_helper as fh
from fbgui.constants import CAL, TEMP
from fbgui.program import Program, ProgramType
from fbgui.messages import MessageType, Message
from fbgui.main_program import Application


class CalProgram(Program):
    """Contains the logic specific for running a calibration program."""
    def __init__(self, master: Application):
        """
        Creates a new CalProgram object that overrides the Program class with the CAl program type.

        :param master: Application object representing the main gui.
        """
        cal_type = ProgramType(CAL)
        super().__init__(master, cal_type)

    def program_loop(self, thread_id: UUID):
        """
        Runs the calibration main loop.

        :param thread_id: UUID of the thread this code is running in
        """
        temps_arr = self.options.get_target_temps()
        self.cal_loop(temps_arr, thread_id)
        if self.master.thread_map[thread_id]:
            self.create_excel()
            self.pause_program()

    def sleep(self, thread_id: UUID) -> bool:
        """
        Sleeps for the configured temp_interval on the home screen.

        :param thread_id: UUID of the thread this code is running in
        :return: False if the program was paused, True otherwise
        """
        start_time = time.time()
        while time.time() - start_time < self.options.temp_interval.get():
            time.sleep(.5)
            if not self.master.thread_map[thread_id]:
                return False
        return True

    def get_temp(self, thread_id: UUID) -> float:
        """
        Takes the configured number of temperature readings and averages them.

        :param thread_id: UUID of the thread the code is currently running in
        :return: the averaged temperature
        """
        avg_temp = 0.
        temp = None
        for _ in range(self.options.num_temp_readings.get()):
            while temp is None:
                try:
                    self.master.conn_dev(TEMP, thread_id=thread_id)
                    temp = float((self.master.temp_controller.get_temp_k()))
                    avg_temp += temp
                except (AttributeError, visa.VisaIOError):
                    self.temp_controller_error()
            temp = None
        self.disconnect_devices()
        return avg_temp/self.options.num_temp_readings.get()

    def cal_loop(self, temps: List[float], thread_id: UUID):
        """
        Runs the main calibration loop.

        :param temps: the list of temperatures to set the oven to
        :param thread_id: UUID of the code the thread is currently running in
        """
        last_cycle_num = fh.get_last_cycle_num(self.options.file_name.get(), CAL)
        if last_cycle_num == self.options.num_cal_cycles.get():
            self.master.main_queue.put(Message(MessageType.WARNING, "Calibration Program Complete",
                                               "The calibration program has already completed the specified {} cycles"
                                               .format(self.options.num_cal_cycles.get())))
        for cycle_num in range(self.options.num_cal_cycles.get() - last_cycle_num):
            cycle_num += last_cycle_num
            if not self.master.thread_map[thread_id]:
                return

            temp = self.get_temp(thread_id)

            kwargs = {"force_connect": True, "thread_id": thread_id}
            if temp < float(temps[0]) + 274.15 - 5:
                kwargs["heat"] = True
            else:
                kwargs["cooling"] = True

            self.master.main_queue.put(Message(MessageType.INFO, text="Initializing cycle {} to start temperature {}K."
                                               .format(cycle_num+1, temps[0]+274.15-5), title=None))
            start_init_time = time.time()
            if not self.master.thread_map[thread_id]:
                return

            self.set_oven_temp(temps[0] - 5, **kwargs)
            self.disconnect_devices()
            kwargs["force_connect"] = False
            while not self.reset_temp(temps[0], thread_id):
                if not self.sleep(thread_id):
                    return
                self.set_oven_temp(temps[0] - 5, **kwargs)

            self.master.main_queue.put(Message(MessageType.INFO, text="Initializing cycle {} took {}.".format(
                cycle_num+1, str(datetime.timedelta(seconds=int(time.time()-start_init_time)))), title=None))

            self.master.main_queue.put(Message(MessageType.INFO, text="Starting cycle {}.".format(cycle_num+1),
                                               title=None))
            start_cycle_time = time.time()
            for temp in temps:
                if temp >= temps[0]:
                    kwargs = {"temp": temp, "heat": True, "force_connect": True}
                else:
                    kwargs = {"temp": temp, "heat": False, "cooling": True, "force_connect": True}
                self.set_oven_temp(**kwargs)
                self.disconnect_devices()
                if not self.sleep(thread_id):
                    return
                kwargs["force_connect"] = False
                while not self.check_drift_rate(thread_id, cycle_num+1):
                    if not self.sleep(thread_id):
                        return
                    self.set_oven_temp(**kwargs)
            self.master.main_queue.put(Message(MessageType.INFO, text="Cycle {} complete it ran for {}.".format(
                cycle_num+1, str(datetime.timedelta(seconds=int(time.time()-start_cycle_time)))), title=None))

    def reset_temp(self, start_temp: float, thread_id: UUID) -> bool:
        """
        Checks to see if the temperature is 5K below the starting temperature.

        :param start_temp: The first temperature the oven is set to
        :param thread_id: UUID of the thread the code is currently running in
        """
        temp = self.get_temp(thread_id)
        if temp <= float(start_temp + 274.15) - 5:
            return True
        return False

    def check_drift_rate(self, thread_id: UUID, cycle_num: int) -> bool:
        """
        Checks if the drift rate is below the configured drift.

        :param thread_id: UUID of the thread the code is curretnly running in
        :param cycle_num: The number of the current calibration cycle
        :return: True if the drift rate is below the configured drift rate, otherwise False
        """
        while True:
            try:
                self.master.conn_dev(TEMP, thread_id)
                start_time = time.time()
                if not self.master.thread_map[thread_id]:
                    return False
                start_temp = self.get_temp(thread_id)
                waves, amps = self.get_wave_amp_data(thread_id)
                if not self.master.thread_map[thread_id]:
                    return False
                curr_temp = self.get_temp(thread_id)
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
                self.temp_controller_error()
