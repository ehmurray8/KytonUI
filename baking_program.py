"""Module for baking program specific logic."""
# pylint:disable=import-error, relative-import, missing-super-argument
import time
import asyncio
import program
import file_helper as fh
from constants import BAKING, LASER, SWITCH, TEMP


class BakingProgram(program.Program):
    """Contains the baking_program specific logic, and gui elements."""

    def __init__(self, master):
        baking_type = program.ProgramType(BAKING)
        super().__init__(master, baking_type)

    def check_stable(self):
        """Check if the program is ready to move to primary interval."""
        num_stable = self.options.init_duration.get()
        if self.stable_count < num_stable:
            self.stable_count += 1
            return False
        return True

    def program_loop(self):
        """Runs the baking process."""
        while self.master.running:
            if self.master.use_dev:
                self.master.conn_buttons[TEMP]()
                self.master.conn_buttons[LASER]()
                temperature = self.master.loop.run_until_complete(self.master.temp_controller.get_temp_k())
                temperature = float(temperature[:-3])
                #TODO: Handle error catching and warning
                if sum(len(switch) for switch in self.switches):
                    self.master.conn_buttons[SWITCH]()
            else:
                temperature = self.master.loop.run_until_complete(
                    self.master.temp_controller.get_temp_k(True, self.options.set_temp.get()))

            waves, amps = self.master.loop.run_until_complete(self.get_wave_amp_data())

            if self.master.use_dev:
                temp2 = self.master.loop.run_until_complete(self.master.temp_controller.get_temp_k())
            else:
                temp2 = self.master.loop.run_until_complete(
                    self.master.temp_controller.get_temp_k(True, self.options.set_temp.get()))
            temperature += float(temp2[:-3])
            temperature /= 2.0
            curr_time = time.time()

            if self.master.use_dev:
                self.disconnect_devices()

            if not self.master.running:
                break

            fh.write_db(self.options.file_name.get(), self.snums, curr_time, temperature,
                        waves, amps, BAKING, self.table)
            if not self.check_stable():
                self.master.loop.run_until_complete(asyncio.sleep(self.options.init_time.get()))
            else:
                self.master.loop.run_until_complete(asyncio.sleep(self.options.prim_time.get() * 60 * 60))
