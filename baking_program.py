"""Module for baking program specific logic."""
# pylint:disable=import-error, relative-import, missing-super-argument
import sys
import time
import queue
import threading
from program import Page, ProgramType, BAKING_ID
import device_helper
import file_helper
import options_frame


class BakingPage(Page):
    """Contains the baking_program specific logic, and gui elements."""
    def __init__(self, parent, master, start_page):
        baking_type = ProgramType(BAKING_ID)
        super().__init__(parent, master, start_page, baking_type)

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
                self.after(int(self.options.init_time.get() * 1000 + .5), self.program_loop)
            else:
                self.baking_loop()
                self.after(int(self.options.prim_time.get() * 1000 * 60 + .5), self.program_loop)

    def listen_for_data(self):
        """Listens for the data_pts."""
        try:
            self.data_pts = self.thread_queue.get_nowait()
        except queue.Empty:
            self.after(100, self.listen_for_result)

    def baking_loop(self):
        """Runs the baking process."""
        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            temperature = self.temp_controller.get_temp_c()
            temperature = float(temperature[:-3])
        else:
            temperature = 0.0

        wavelengths_avg = []
        amplitudes_avg = []

        device_helper.avg_waves_amps(self)
        self.listen_for_data()

        for snum in self.snums:
            wavelengths_avg.append(self.data_pts[snum][0])
            amplitudes_avg.append(self.data_pts[snum][1])

        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            temp2 = self.temp_controller.get_temp_c()
            temperature += float(temp2[:-3])

        temperature /= 2.0
        curr_time = time.time()

        if len(sys.argv) > 1 and sys.argv[1] == "-k":
            threading.Thread(target=file_helper, args=(self.options.file_name.get(), self.snums,
                                                       curr_time, temperature, wavelengths_avg,
                                                       amplitudes_avg, options_frame.BAKING)).start()
            file_helper.write_csv_file(self.options.file_name.get(), self.snums,
                                       curr_time, temperature, wavelengths_avg,
                                       amplitudes_avg, options_frame.BAKING)
