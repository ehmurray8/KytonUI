"""Module for baking program specific logic."""
import time
import math
import asyncio
import program
import file_helper as fh
from constants import BAKING, LASER, SWITCH, TEMP, OVEN


class BakingProgram(program.Program):
    """Contains the baking_program specific logic, and gui elements."""

    def __init__(self, master):
        baking_type = program.ProgramType(BAKING)
        super().__init__(master, baking_type)

    def check_stable(self):
        """Check if the program is ready to move to primary interval."""
        self.master.conn_buttons[TEMP]()
        temp1 = float(self.master.loop.run_until_complete(self.master.temp_controller.get_temp_k())[3:])
        start = time.time()
        self.master.loop.run_until_complete(asyncio.sleep(60))
        temp2 = float(self.master.loop.run_until_complete(self.master.temp_controller.get_temp_k())[3:])
        end = time.time()
        if self.master.use_dev:
            self.disconnect_devices()
        drift_rate = math.fabs(temp2 - temp1) / ((end - start) / 60)
        print("Calculated Drift rate: {}, Expected Drift Rate: {}".format(drift_rate, self.options.drift_rate.get() * .001))
        if -self.options.drift_rate.get() * .001 <= drift_rate <= self.options.drift_rate.get() * .001:
            return True
        return False

    def program_loop(self):
        """Runs the baking process."""
        stable = False
        while self.options.set_temp.get() and self.master.use_dev and not stable :
            stable = self.check_stable()
            print(stable)
            self.master.conn_buttons[OVEN]()
            self.master.loop.run_until_complete(self.set_oven_temp())
            self.disconnect_devices()

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
            if self.options.set_temp.get() and self.master.use_dev and not stable:
                self.master.conn_buttons[OVEN]()
                self.master.loop.run_until_complete(self.set_oven_temp())
                self.disconnect_devices()
