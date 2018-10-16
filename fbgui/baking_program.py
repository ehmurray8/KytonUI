"""Module for baking program specific logic."""
import math
import socket
import time
from uuid import UUID

import visa

from fbgui import program
from fbgui.constants import BAKING, TEMP
from fbgui.database_controller import DatabaseController
from fbgui.exceptions import ProgramStopped
from fbgui.main_program import Application


class BakingProgram(program.Program):
    """Contains the Baking Program specific logic, extends the Program abstract class."""

    def __init__(self, master: Application):
        """
        Creates a program with the Baking Program Type.

        :param master: Application object of the main gui
        """
        baking_type = program.ProgramType(BAKING)
        super().__init__(master, baking_type)

    def check_stable(self, thread_id: UUID) -> bool:
        """
        Check if the program is ready to move to primary interval.

        :param thread_id: UUID of the thread this code is running in
        :returns: True if the drift rate is stable otherwise returns false
        """
        while True:
            try:
                self.master.conn_dev(TEMP, thread_id=thread_id)
                temp1 = float(self.master.temp_controller.get_temp_k())
                start = time.time()
                time.sleep(60)
                temp2 = float(self.master.temp_controller.get_temp_k())
                end = time.time()
                self.disconnect_devices()
                drift_rate = math.fabs(temp2 - temp1) / ((end - start) / 60)
                if -self.options.drift_rate.get() * .001 <= drift_rate <= self.options.drift_rate.get() * .001:
                    return True
                return False
            except (AttributeError, visa.VisaIOError):
                self.temp_controller_error()

    def program_loop(self, thread_id: UUID):
        """
        Runs the baking process.

        :param thread_id: UUID of the thread this code is running in
        """
        database_controller = DatabaseController(self.options.file_name.get(), self.snums, self.master.main_queue,
                                                 BAKING, self.table)
        stable = False
        while self.master.thread_map[thread_id] and self.options.set_temp.get() and not stable:
            stable = self.check_stable(thread_id)
            if not stable:
                self.set_oven_temp()
                self.disconnect_devices()
        else:
            self.disconnect_devices()

        while self.master.thread_map[thread_id] and self.master.running:
            temperature = self.get_temperature(thread_id)

            curr_time = time.time()
            waves, powers = self.get_wave_amp_data(thread_id)
            curr_time += time.time()
            curr_time /= 2.

            temperature += self.get_temperature(thread_id)
            temperature /= 2.

            self.disconnect_devices()

            database_controller.record_baking_point(curr_time, temperature, waves, powers)

            start_time = time.time()
            count = 0
            while self.master.thread_map[thread_id] and time.time() - start_time < self.options.prim_time.get() \
                    * 60 * 60:
                count = self.set_oven(count)
        else:
            self.disconnect_devices()

    def get_temperature(self, thread_id: UUID) -> float:
        temperature = None
        while temperature is None:
            if not self.master.thread_map[thread_id]:
                raise ProgramStopped
            try:
                self.master.conn_dev(TEMP, thread_id=thread_id)
                temperature = self.master.temp_controller.get_temp_k()
            except (visa.VisaIOError, AttributeError, socket.error):
                self.temp_controller_error()
        return temperature

    def set_oven(self, count: int) -> int:
        time.sleep(.5)
        count += 1
        if count > 360:
            count = 0
            self.set_oven_temp()
        return count
