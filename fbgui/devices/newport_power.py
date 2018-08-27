from visa import ResourceManager
from pyvisa.resources.gpib import GPIBInstrument


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
