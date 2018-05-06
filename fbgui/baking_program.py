"""Module for baking program specific logic."""
import math
import time
import visa
from uuid import UUID
import socket
from fbgui import file_helper as fh, program
from fbgui.constants import BAKING, TEMP


class BakingProgram(program.Program):
    """Contains the Baking Program specific logic, extends the Program abstract class."""

    def __init__(self, master):
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
        stable = False
        while self.master.thread_map[thread_id] and self.options.set_temp.get() and \
                self.master.use_dev and not stable:
            stable = self.check_stable(thread_id)
            if not stable:
                self.set_oven_temp()
                self.disconnect_devices()
        else:
            self.disconnect_devices()

        while self.master.thread_map[thread_id] and self.master.running:
            if self.master.use_dev:
                temperature = None
                while temperature is None:
                    try:
                        self.master.conn_dev(TEMP, thread_id=thread_id)
                        temperature = self.master.temp_controller.get_temp_k()
                    except (visa.VisaIOError, AttributeError, socket.error):
                        self.temp_controller_error()
            else:
                temperature = self.master.temp_controller.get_temp_k(True, self.options.set_temp.get())

            if not self.master.thread_map[thread_id]:
                return

            waves, amps = self.get_wave_amp_data(thread_id)

            if not self.master.thread_map[thread_id]:
                return

            if self.master.use_dev:
                temp2 = None
                while temp2 is None:
                    try:
                        self.master.conn_dev(TEMP, thread_id=thread_id)
                        temp2 = self.master.temp_controller.get_temp_k()
                        temperature += temp2
                    except (AttributeError, visa.VisaIOError):
                        self.temp_controller_error()
            else:
                temp2 = self.master.temp_controller.get_temp_k(True, self.options.set_temp.get())
                temperature += temp2

            temperature /= 2.
            curr_time = time.time()

            if self.master.use_dev:
                self.disconnect_devices()
            if not self.master.thread_map[thread_id]:
                return

            if not fh.write_db(self.options.file_name.get(), self.snums, curr_time, temperature,
                               waves, amps, BAKING, self.table, self.master.main_queue):
                self.pause_program()
                return

            start_time = time.time()
            count = 0
            while self.master.thread_map[thread_id] and time.time() - start_time < self.options.prim_time.get() \
                    * 60 * 60:
                time.sleep(.5)
                count += 1
                if count > 360:
                    count = 0
                    self.set_oven_temp()
        else:
            self.disconnect_devices()
