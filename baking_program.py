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
        #num_stable = self.options.init_duration.get()
        #if self.stable_count < num_stable:
        #    self.stable_count += 1
        #    return False
        #return True
        self.master.conn_buttons[TEMP]()
        temperature = self.master.loop.run_until_complete(self.master.temp_controller.get_temp_c())
        if self.master.use_dev:
            self.disconnect_devices()
        if float(temperature[:-3]) >= self.options.set_temp.get() - (self.options.set_temp.get() * .01):
            return True
        return False

    def program_loop(self):
        """Runs the baking process."""
        while self.master.running:
            stable = self.check_stable()
            print(stable)
            if stable:
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
                    temperature += float(temp2[:-3])
                else:
                    temp2 = self.master.loop.run_until_complete(
                        self.master.temp_controller.get_temp_k(True, self.options.set_temp.get()))
                    temperature += temp2
                temperature /= 2.0
                curr_time = time.time()

                if self.master.use_dev:
                    self.disconnect_devices()

                fh.write_db(self.options.file_name.get(), self.snums, curr_time, temperature,
                            waves, amps, BAKING, self.table)
                self.master.loop.run_until_complete(asyncio.sleep(self.options.prim_time.get() * 60 * 60))

            else:
                self.master.loop.run_until_complete(asyncio.sleep(60))
            #if not self.check_stable():
            #    self.master.loop.run_until_complete(asyncio.sleep(self.options.init_time.get()))
            #else:
