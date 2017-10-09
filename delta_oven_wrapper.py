class Oven(object):
    def __init__(self, port, manager):
        loc = "GPIB0::{}::INSTR".format(port)
        self.device = manager.open_resource(loc, "\n")

    def set_temp(self, temp):
        """Sets set point of delta oven."""
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
