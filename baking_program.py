"""Module for baking program specific logic."""
# pylint:disable=import-error, relative-import, missing-super-argument
import sys
import time
import program
import device_helper
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
        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            temperature = self.temp_controller.get_temp_c()
            temperature = float(temperature[:-3])
        else:
            temperature = 0.0

        wavelengths_avg = []
        amplitudes_avg = []

        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            device_helper.avg_waves_amps(self)
        else:
            time.sleep(15)

        for snum in self.snums:
            wavelengths_avg.append(self.data_pts[snum][0])
            amplitudes_avg.append(self.data_pts[snum][1])

        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            temp2 = self.temp_controller.get_temp_c()
            temperature += float(temp2[:-3])

        temperature /= 2.0
        curr_time = time.time()

        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            file_helper.write_csv_file(self.options.file_name.get(), self.snums,
                                       curr_time, temperature, wavelengths_avg,
                                       amplitudes_avg, options_frame.BAKING)
