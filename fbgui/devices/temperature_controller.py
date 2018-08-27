import random
from pyvisa.resources.gpib import GPIBInstrument


class TemperatureController(object):
    """
    Object representation of the Temperature Controller needed for the program.

    :ivar pyvisa.resources.gpib.GPIBInstrument device: PyVisa GPIB connection to the device.
    """
    def __init__(self, loc, manager, use_dev):
        """
        Establishes a GPIB connection with the temperature controller.

        :param loc: the location of the instrument
        :param manager: the PyVisa resource manager
        :param use_dev: if True connect to the device
        """
        self.device = None
        if use_dev:
            self.device = manager.open_resource(loc, read_termination='\r\n', open_timeout=2500)  # type: GPIBInstrument

    def get_temp_k(self, dummy_val=False, center_num=0):
        """
        Return temperature reading in degrees Kelvin.

        :param dummy_val: If true make up a temperature
        :param center_num: The number the temperature is set to used for simulating the temp reading
        """
        if dummy_val:
            return float(random.gauss(center_num - 5, center_num + 5))
        else:
            query = self.device.query('KRDG? B')
            return float(query)

    def close(self):
        """Close the device connection."""
        if self.device is not None:
            self.device.close()
