from visa import ResourceManager
from pyvisa.resources.gpib import GPIBInstrument
import time


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
