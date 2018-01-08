"""Module for baking program specific logic."""
# pylint:disable=import-error, relative-import, missing-super-argument
import asyncio
import threading
import time
import program
import file_helper
from constants import BAKING
from concurrent.futures import ThreadPoolExecutor

POOL = ThreadPoolExecutor(4)


class BakingProgram(program.Program):
    """Contains the baking_program specific logic, and gui elements."""

    def __init__(self, master):
        baking_type = program.ProgramType(BAKING)
        super().__init__(master, baking_type)

    def check_stable(self):
        """Check if the program is ready to move to primary interval."""
        init_time = self.options.init_time.get()
        init_dur = self.options.init_duration.get() * 60
        num_stable = int(init_dur / init_time + .5)

        if self.stable_count < num_stable:
            self.stable_count += 1
            return False
        return True

    def program_loop(self):
        """Infinite program loop."""
        if self.master.running:
            self.loop_handler()

    def loop_handler(self):
        threading.Thread(target=self.baking_loop).start()
        self.update_table()
        if not self.check_stable():
            self.master.after(int(self.options.init_time.get() * 1000 + .5), self.program_loop)
        else:
            self.master.after(int(self.options.prim_time.get() * 1000 * 60 * 60 + .5), self.program_loop)

    def baking_loop(self):
        """Runs the baking process."""
        temperature = self.master.loop.run_until_complete(self.master.temp_controller.get_temp_c())
        temperature = float(temperature[:-3])

        print("bake loop")
        waves, amps = self.master.loop.run_until_complete(self.get_wave_amp_data())

        temp2 = self.master.loop.run_until_complete(self.master.temp_controller.get_temp_c())
        temperature += float(temp2[:-3])

        temperature /= 2.0
        curr_time = time.time()

        file_helper.write_csv_file(self.options.file_name.get(), self.snums, curr_time, temperature,
                                   waves, amps, BAKING)
