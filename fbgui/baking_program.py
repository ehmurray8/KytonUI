"""Module for baking program specific logic."""
import math
import time
from fbgui import file_helper as fh, program
from fbgui.constants import BAKING, LASER, SWITCH, TEMP


class BakingProgram(program.Program):
    """Contains the baking_program specific logic, and gui elements."""

    def __init__(self, master):
        baking_type = program.ProgramType(BAKING)
        super().__init__(master, baking_type)

    def check_stable(self, thread_id):
        """Check if the program is ready to move to primary interval."""
        self.master.conn_dev(TEMP, thread_id)
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

    def program_loop(self, thread_id):
        """Runs the baking process."""
        stable = False
        try:
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
                    self.master.conn_dev(TEMP, thread_id)
                    self.master.conn_dev(LASER, thread_id)
                    temperature = self.master.temp_controller.get_temp_k()
                    if sum(len(switch) for switch in self.switches):
                        self.master.conn_dev(SWITCH, thread_id)
                else:
                    temperature = self.master.temp_controller.get_temp_k(True, self.options.set_temp.get())

                if not self.master.thread_map[thread_id]:
                    self.disconnect_devices()
                    return

                waves, amps = self.get_wave_amp_data(thread_id)

                if not self.master.thread_map[thread_id]:
                    self.disconnect_devices()
                    return

                if self.master.use_dev:
                    temp2 = self.master.temp_controller.get_temp_k()
                    temperature += temp2
                else:
                    temp2 = self.master.temp_controller.get_temp_k(self.options.set_temp.get())
                    temperature += temp2

                temperature /= 2.
                curr_time = time.time()

                if self.master.use_dev:
                    self.disconnect_devices()

                if not self.master.thread_map[thread_id]:
                    self.disconnect_devices()
                    return

                if not fh.write_db(self.options.file_name.get(), self.snums, curr_time, temperature,
                                   waves, amps, BAKING, self.table, self.master.main_queue):
                    self.pause_program()

                start_time = time.time()
                while self.master.thread_map[thread_id] and time.time() - start_time < self.options.prim_time.get() \
                        * 60 * 60:
                    time.sleep(.5)
            else:
                self.disconnect_devices()
        except AttributeError:  # Program has been paused
            self.disconnect_devices()
