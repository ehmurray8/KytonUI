from visa import ResourceManager
from pyvisa.resources.gpib import GPIBInstrument


class Oven(object):
    """
    Delta oven object, uses pyvisa.

    :ivar pyvisa.resources.gpib.GPIBInstrument device: PyVisa GPIB connection to the device
    """

    def __init__(self, loc: str, manager: ResourceManager, use_dev: bool):
        """
        Opens a GPIB connection with the device at the specified location.

        :param loc: the location of the device
        :param manager: the PyVisa Resource Manager
        :param use_dev: if True connect to the device
        """
        self.device = None
        if use_dev:
            self.device = manager.open_resource(loc, read_termination="\n", open_timeout=2500)  # type: GPIBInstrument

    def set_temp(self, temp: float):
        """
        Sets set point of delta oven.

        :param temp: Temperature to set the oven to
        """
        self.device.query('S {}'.format(temp))

    def heater_on(self):
        """Turns oven heater on."""
        self.device.query('H ON')

    def heater_off(self):
        """Turns oven heater off."""
        self.device.query('H OFF')

    def cooling_on(self):
        """Turns oven cooling on."""
        self.device.query('C ON')

    def cooling_off(self):
        """Turns oven cooling off."""
        self.device.query('C OFF')

    def close(self):
        """Closes the resource."""
        if self.device is not None:
            self.device.close()
