"""Contains the calibration program specific logic."""

import datetime
import math
import time
from typing import List, Tuple
from uuid import UUID

import tkinter as tk
import visa

from fbgui.constants import CAL, TEMP
from fbgui.exceptions import ProgramStopped
from fbgui.main_program import Application
from fbgui.messages import MessageType, Message
from fbgui.program import Program, ProgramType


class CalProgram(Program):
    """Contains the logic specific for running a calibration program."""
    def __init__(self, master: Application):
        """
        Creates a new CalProgram object that overrides the Program class with the CAl program type.

        :param master: Application object representing the main gui.
        """
        cal_type = ProgramType(CAL)
        super().__init__(master, cal_type)
        self.current_set_temp = None
        self.thread_id = None  # type: UUID

    def program_loop(self, thread_id: UUID):
        """
        Runs the calibration main loop.

        :param thread_id: UUID of the thread this code is running in
        """
        temps_arr = self.options.get_target_temps()
        self.thread_id = thread_id
        self.cal_loop(temps_arr)
        if self.master.thread_map[self.thread_id]:
            self.create_excel()
            self.pause_program()

    def sleep(self):
        """
        Sleeps for the configured temp_interval on the home screen.
        """
        start_time = time.time()
        while time.time() - start_time < self.options.temp_interval.get():
            time.sleep(.5)
            self.check_program_stopped()

    def get_temp(self) -> float:
        """
        Takes the configured number of temperature readings and averages them.

        :return: the averaged temperature
        """
        avg_temp = 0.
        temp = None
        for _ in range(self.options.num_temp_readings.get()):
            while temp is None:
                try:
                    self.master.conn_dev(TEMP, thread_id=self.thread_id)
                    temp = float((self.master.temp_controller.get_temp_k()))
                    avg_temp += temp
                except (AttributeError, visa.VisaIOError):
                    self.temp_controller_error()
            temp = None
        self.disconnect_devices()
        return avg_temp/(float(self.options.num_temp_readings.get()))

    def cal_loop(self, temps: List[float]):
        """
        Runs the main calibration loop.

        :param temps: the list of temperatures to set the oven to
        """
        cycles = set(self.database_controller.get_cycle_nums())
        last_cycle_num = self.database_controller.get_last_cycle_num()
        if len(cycles) >= self.options.num_cal_cycles.get():
            self.master.main_queue.put(Message(MessageType.WARNING, "Calibration Program Complete",
                                               "The calibration program has already completed the specified {} cycles"
                                               .format(self.options.num_cal_cycles.get())))
        next_cycle_num = last_cycle_num + 1
        for cycle_num in range(next_cycle_num, next_cycle_num + self.options.num_cal_cycles.get() - len(cycles)):
            self.check_program_stopped()

            temp = self.get_temp()

            kwargs = {"force_connect": True, "thread_id": self.thread_id}
            if temp < float(temps[0]) + 273.15 - 4.5:
                kwargs["heat"] = True
            else:
                kwargs["cooling"] = True

            self.master.main_queue.put(Message(MessageType.INFO, text="Initializing cycle {} to start temperature {} C."
                                               .format(cycle_num, temps[0] - 5), title=None))
            start_init_time = time.time()
            self.check_program_stopped()

            self.current_set_temp = temps[0] - 5
            self.set_oven_temp(temps[0] - 5, **kwargs)
            self.disconnect_devices()
            kwargs["force_connect"] = False

            while not self.reset_temp(temps[0]):
                self.sleep()

            self.master.main_queue.put(Message(MessageType.INFO, text="Initializing cycle {} took {}.".format(
                cycle_num, str(datetime.timedelta(seconds=int(time.time()-start_init_time)))), title=None))

            self.master.main_queue.put(Message(MessageType.INFO, text="Starting cycle {}.".format(cycle_num),
                                               title=None))
            self.record_beginning_extra_points(cycle_num, temps[0])

            start_cycle_time = time.time()
            for temp in temps:
                self.current_set_temp = temp
                if temp >= temps[0]:
                    kwargs = {"temp": temp, "heat": True, "force_connect": True}
                else:
                    kwargs = {"temp": temp, "heat": False, "cooling": True, "force_connect": True}
                self.set_oven_temp(**kwargs)
                self.disconnect_devices()
                self.sleep()
                kwargs["force_connect"] = False
                while not self.check_drift_rate(cycle_num):
                    self.sleep()
                    self.set_oven_temp(**kwargs)
            self.record_end_extra_points(cycle_num, temps[-1])
            self.master.main_queue.put(Message(MessageType.INFO, text="Cycle {} complete it ran for {}.".format(
                cycle_num, str(datetime.timedelta(seconds=int(time.time()-start_cycle_time)))), title=None))
        self.set_oven_temp(50, force_connect=False, heat=False)

    def record_beginning_extra_points(self, cycle_num: int, first_temperature: float):
        for temperature_float_var, wavelength_text, power_text in self.options.extra_points:
            temperature = temperature_float_var.get()
            if temperature != 0 and temperature < first_temperature:
                self.record_extra_point(cycle_num, temperature, wavelength_text, power_text)

    def record_end_extra_points(self, cycle_num: int, last_temperature: float):
        for temperature_float_var, wavelength_text, power_text in self.options.extra_points:
            temperature = temperature_float_var.get()
            if temperature != 0 and temperature > last_temperature:
                self.record_extra_point(cycle_num, temperature, wavelength_text, power_text)

    def record_extra_point(self, cycle_num: int, temperature: float, wavelength_text: tk.Text, power_text: tk.Text):
        try:
            wavelengths = [float(x) for x in wavelength_text.get(1.0, tk.END).split(",") if float(x) != 0.0]
        except ValueError:
            wavelengths = []
        try:
            powers = [float(x) for x in power_text.get(1.0, tk.END).split(",") if float(x) != 0.0]
        except ValueError:
            powers = []
        number_of_fbgs = sum(len(x) for x in self.options.sn_ents)
        if len(wavelengths) == number_of_fbgs == len(powers):
            curr_time = time.time()
            temperature += 273.15
            self.database_controller.record_calibration_point(curr_time, temperature, wavelengths, powers, drift_rate=0,
                                                              is_real_calibration_point=True, cycle_num=cycle_num)

    def reset_temp(self, start_temp: float) -> bool:
        """
        Checks to see if the temperature is 4.5K below the starting temperature.

        :param start_temp: The first temperature the oven is set to
        :param cycle_num: Number of the current cycle
        """
        temp = self.get_temp()
        drift_rate = self.get_drift_rate()
        kwargs = {"force_connect": False, "thread_id": self.thread_id}
        if temp < float(start_temp + 273.15 - 4.5):
            kwargs["heat"] = True
        else:
            kwargs["cooling"] = True
        self.set_oven_temp(start_temp - 5, **kwargs)
        if drift_rate is not None:
            drift_rate = drift_rate[0]
        if temp <= float(start_temp + 273.15) - 4.5 or drift_rate < self.options.drift_rate.get():
            return True
        return False

    def get_drift_rate(self, get_wave_amp: bool=False) -> Tuple[float, float, float, List[float], List[float]]:
        """
        Get the drift rate of the system.

        :param: the UUID of the thread the code is currently running on
        :return: the current drift rate in mK/min
        """
        self.master.conn_dev(TEMP, thread_id=self.thread_id)
        start_time = time.time()
        self.check_program_stopped()
        start_temp = self.get_temp()

        waves = []
        amps = []
        if get_wave_amp:
            waves, amps = self.get_wave_amp_data(self.thread_id)
        else:
            time.sleep(5)

        self.check_program_stopped()
        self.sleep()

        self.master.conn_dev(TEMP, thread_id=self.thread_id)
        curr_temp = self.get_temp()
        curr_time = time.time()
        self.disconnect_devices()

        drift_rate = math.fabs(start_temp - curr_temp) / math.fabs(start_time - curr_time)
        drift_rate *= 60000.
        return drift_rate, curr_temp, curr_time, waves, amps

    def check_drift_rate(self, cycle_num: int) -> bool:
        """
        Checks if the drift rate is below the configured drift, and the temperature is within 1 degree of the set
        temperature.

        :param cycle_num: The number of the current calibration cycle
        :return: True if the drift rate is below the configured drift rate, otherwise False
        """
        while True:
            try:
                drift_rate, curr_temp, curr_time, waves, amps = self.get_drift_rate(get_wave_amp=True)

                if drift_rate <= self.options.drift_rate.get():
                    self.database_controller.record_calibration_point(curr_time, curr_temp, waves, amps, drift_rate,
                                                                      is_real_calibration_point=True,
                                                                      cycle_num=cycle_num)
                    return True

                self.check_program_stopped()
                self.database_controller.record_calibration_point(curr_time, curr_temp, waves, amps,
                                                                  drift_rate, is_real_calibration_point=False,
                                                                  cycle_num=cycle_num)
                return False
            except (AttributeError, visa.VisaIOError):
                self.temp_controller_error()

    def check_program_stopped(self):
        if not self.master.thread_map[self.thread_id]:
            raise ProgramStopped
