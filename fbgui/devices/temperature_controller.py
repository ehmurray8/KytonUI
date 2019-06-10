
rom pyvisa.resources.gpib import GPIBInstrument


class TemperatureController(object):
    """
    Object representation of the Temperature Controller needed for the program.

    :ivar pyvisa.resources.gpib.GPIBInstrument device: PyVisa GPIB connection to the device.
    """
    def __init__(self, location, manager):
        """
        Establishes a GPIB connection with the temperature controller.

        :param location: the location of the instrument
        :param manager: the PyVisa resource manager
        """
        self.device = manager.open_resource(location, read_termination='\r\n',
                                            open_timeout=2500)  # type: GPIBInstrument

    def get_temp_k(self):
        """ Return temperature reading in degrees Kelvin. """
        query = self.device.query('KRDG? B')
        return float(query)

    def close(self):
        """Close the device connection."""
        self.device.close()
