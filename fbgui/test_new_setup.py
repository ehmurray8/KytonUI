import time
import visa
from threading import Thread
from visa import ResourceManager
from pyvisa.resources.gpib import GPIBInstrument
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from collections import deque
from sys import argv
import datetime
import os


# READ SETTINGS
REMOVE_POINTS = False
NUM_SCANS = int(argv[1])
START_WAVE = int(argv[2])
END_WAVE = int(argv[3])
POWER = int(argv[4])


class VidiaLaser(object):
    """
    Vidia-Swept laser wrapper object.

    :ivar pyvisa.resources.gpib.GPIBInstrument device: PyVisa GPIB connection to the device
    """

    def __init__(self, loc: str, manager: ResourceManager, use_dev: bool):
        """
        Create a visa connection using loc and manager to the Vidia-Swept laser.

        :param loc: the GPIB location of the laser
        :param manager:  the PyVisa resource manager
        :param use_dev: if True connect to laser
        """
        self.device = None
        if use_dev:
            self.device = manager.open_resource(loc)  # type: GPIBInstrument

    def start_scan(self, num_scans: int=-1, start_wave: int=1510, end_wave: int=1575, power: int=6):
        """
        Starts the scanning process for the laser.

        :param num_scans: the number of scans to run, defaults to -1 (continuous scan)
        :param start_wave: the starting wave for the scan
        :param end_wave: the ending wave for the scan
        :param power: the power to set the laser to
        """
        self.device.query(":POW {}".format(power))
        time.sleep(.5)
        self.device.query(":OUTP ON")
        time.sleep(.5)
        self.device.query(":WAVE:STAR {}".format(start_wave))
        time.sleep(.5)
        self.device.query(":WAVE:STOP {}".format(end_wave))
        time.sleep(.5)
        self.device.query(":OUTP:TRAC OFF")
        time.sleep(.5)
        self.device.query(":OUTP:SCAN:STAR {}".format(num_scans))

    def get_wavelength(self) -> float:
        """
        Returns wavelength information from the laser.

        :return: min wavelength, set wavelength, max wavelength
        """
        return float(self.device.query(":SENS:WAVE?"))

    def get_mean_wavelength(self) -> float:
        """
        Return the mean wavelength of the scan.

        :return: mean wavelength of the scan range
        """
        return (float(self.device.query(":WAVE MAX?")) + float(self.device.query(":WAVE MIN?"))) / 2

    def stop_scan(self):
        """Stop the laser scan, and turn off the power."""
        self.device.query(":OUTP:SCAN:ABORT")
        self.device.query(":OUTP OFF")


class NewportPower(object):
    """
    Newport Power Meter 1830-C wrapper object.

    :ivar pyvisa.resources.gpib.GPIBInstrument device: PyVisa GPIB connection to the device
    """

    def __init__(self, loc: str, manager: ResourceManager, use_dev: bool):
        """
        Create a visa connection using loc and manager to the Newport Power Meter.

        :param loc: the GPIB location of the power meter
        :param manager: the PyVisa resource manager
        :param use_dev: if True connect to the power meter
        """
        self.device = None
        if use_dev:
            self.device = manager.open_resource(loc)  # type: GPIBInstrument

    def set_units_dbm(self):
        """Set the units of the device to dBm"""
        if self.device.query("U?\n") != "3":
            self.device.query("U3")

    def get_power(self) -> float:
        """
        Returns the power reading of the device in dBm.

        :return: power in dBm.
        """
        power_watts = float(self.device.query("D?\n"))
        return power_watts


wave = None
above_mean = False
waves = deque()
powers = deque()
all_waves = []
all_powers = []
pop = False
kill_thread = False


def animate(_):
    axes.clear()
    axes.set_ylabel("Power (dBm)")
    axes.set_xlabel("Wavelength (nm)")
    axes.scatter(waves, powers)


def collect():
    global above_mean
    count = 0
    while not kill_thread and (count < NUM_SCANS or NUM_SCANS == -1):
        try:
            wave = laser.get_wavelength()
            pow = power.get_power()
            if wave < START_WAVE or wave > END_WAVE or pow > POWER + .5:
                raise ValueError
            waves.append(wave)
            powers.append(pow)
            if wave > laser.get_mean_wavelength():
                above_mean = True
            if above_mean and wave < laser.get_mean_wavelength():
                count += 1
                above_mean = False
        except (ValueError, visa.VisaIOError) as r:
            pass
        time.sleep(.1)


if __name__ == "__main__":
    try:
        man = visa.ResourceManager()
        laser = VidiaLaser("GPIB1::8::INSTR", man, True)
        power = NewportPower("GPIB1::4::INSTR", man, True)
        laser.start_scan(num_scans=NUM_SCANS, start_wave=START_WAVE, end_wave=END_WAVE, power=POWER)
        mean_wave = (START_WAVE + END_WAVE) / 2.

        Thread(target=collect).start()

        try:
            if NUM_SCANS != 1:
                fig, axes = plt.subplots()
                fig.suptitle("Power vs. Wavelength")
                axes.set_ylabel("Power (dBm)")
                axes.set_xlabel("Wavelength (nm)")
                anim = FuncAnimation(fig, animate, interval=5)
                axes.scatter(powers, waves)
                plt.show()

            if NUM_SCANS == 1:
                plt.scatter(powers, waves)
                plt.ylabel("Power (dBm)")
                plt.xlabel("Wavelength (nm)")
                plt.title("Power vs. Wavelength")
                plt.show()
        except AttributeError:
            pass

        t = time.time()
        timestamp = datetime.datetime.fromtimestamp(t).strftime("%Y%m%dT%H%M%S")
        if not os.path.isdir(r"C:\Users\phils\Documents\FBGScans"):
            os.mkdir(r"C:\Users\phils\Documents\FBGScans")
        with open(os.path.join(r"C:\Users\phils\Documents\FBGScans",
                               "{}_scan_{}-{}.txt".format(str(timestamp), START_WAVE, END_WAVE)), "w") as f:
            for wave, power in zip(waves, powers):
                f.write("{}, {}\n".format(wave, power))

        kill_thread = True
        time.sleep(2)

        laser.stop_scan()
    except visa.VisaIOError:
        pass
