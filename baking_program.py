"""Module for baking program specific logic."""
# pylint:disable=import-error, relative-import, missing-super-argument
import time
import program
import dev_helper
import file_helper
import options_frame


class BakingPage(program.Page):
    """Contains the baking_program specific logic, and gui elements."""

    def __init__(self, master, pid):
        baking_type = program.ProgramType(program.BAKING_ID)
        super().__init__(master, pid, baking_type)

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
        if self.running:
            if not self.check_stable():
                self.baking_loop()
                self.after(int(self.options.init_time.get()
                               * 1000 + .5), self.program_loop)
            else:
                self.baking_loop()
                self.after(int(self.options.prim_time.get() *
                               1000 * 60 * 60 + .5), self.program_loop)

    def baking_loop(self):
        """Runs the baking process."""
        temperature = self.master.temp_controller.get_temp_c()
        temperature = float(temperature[:-3])

        waves, amps = dev_helper.avg_waves_amps(self.master.laser, self.master.switch, self.switches,
                                                self.options.num_pts.get(), self.master.after)

        temp2 = self.master.temp_controller.get_temp_c()
        temperature += float(temp2[:-3])

        temperature /= 2.0
        curr_time = time.time()

        file_helper.write_csv_file(self.options.file_name.get(), self.snums,
                                   curr_time, temperature, waves, amps, options_frame.BAKING)
