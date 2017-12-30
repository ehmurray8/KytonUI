"""Containts the calibration program page."""

# pylint: disable=import-error, relative-import, missing-super-argument
import time
from program import Program, ProgramType
from constants import CAL
import file_helper
import options_frame
import asyncio


class CalProgram(Program):
    """Object representation of the Calibration Program page."""
    def __init__(self, master):
        cal_type = ProgramType(CAL)
        super().__init__(master, cal_type)

    async def program_loop(self):
        """Runs the calibration."""
        temps_arr = self.options.get_target_temps()

        for _ in range(self.options.num_cal_cycles.get()):
            for temp in temps_arr:
                while True:
                    self.master.oven.set_temp(temp)
                    self.master.oven.cooling_off()
                    self.master.oven.heater_on()

                    start_temp = float(self.master.temp_controller.get_temp_k())
                    waves, amps = await self.get_wave_amp_data()

                    start_temp += float(self.master.temp_controller.get_temp_k())
                    start_temp /= 2
                    start_time = time.time()

                    # Need to write csv file init code
                    file_helper.write_csv_file(self.options.file_name.get(), self.snums, start_time,
                                               start_temp, waves, amps, options_frame.CAL, False, 0.0)
                    if self.__check_drift_rate(start_time, start_temp):
                        break
                    else:
                        await asyncio.sleep(int(self.options.temp_interval.get()*1000 + .5))

            self.master.oven.heater_off()
            self.master.oven.set_temp(temps_arr[0])

            if self.options.cooling.get():
                self.master.oven.cooling_on()

            await self.reset_temp(temps_arr)

    async def reset_temp(self, temps_arr):
        """Checks to see if the the temperature is within the desired amount."""
        temp = float(self.master.temp_controller.get_temp_c())
        while temp >= float(temps_arr[0]) - .1:
            await asyncio.sleep(int(self.options.temp_interval.get()*1000 + .5))
            temp = float(self.master.temp_controller.get_temp_c())

    async def get_drift_rate(self, last_time, last_temp):
        waves, amps = await self.get_wave_amp_data()
        curr_temp = float(self.master.temp_controller.get_temp_k())
        curr_temp += float(self.master.temp_controller.get_temp_k())
        curr_temp /= 2
        curr_time = time.time()

        time_ratio_min = curr_time / last_time / 60
        temp_ratio_mk = curr_temp / last_temp / 1000

        drift_rate = temp_ratio_mk / time_ratio_min
        return drift_rate, curr_temp, curr_time, waves, amps

    async def __check_drift_rate(self, last_time, last_temp):
        drift_rate, curr_temp, curr_time, waves, amps = self.get_drift_rate(last_time, last_temp)
        while drift_rate > self.options.drift_rate.get():
            file_helper.write_csv_file(self.options.file_name.get(), self.snums, curr_time,
                                       curr_temp, waves, amps, options_frame.CAL, False, drift_rate)
            drift_rate, curr_temp, curr_time, waves, amps = self.get_drift_rate(last_time, last_temp)

        # record actual point
        file_helper.write_csv_file(self.options.file_name.get(), self.snums, curr_time,
                                   curr_temp, waves, amps, options_frame.CAL, True, drift_rate)
