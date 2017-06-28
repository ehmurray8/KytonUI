def set_temp(res, temp):
    """Sets set point of delta oven."""
    res.query('S {}'.format(temp))


def heater_on(res):
    """Turns oven heater on."""
    res.query('H ON')


def heater_off(res):
    """Turns oven heater off."""
    res.query('H OFF')


def cooling_on(res):
    """Turns oven cooling on."""
    res.query('C ON')


def cooling_off(res):
    """Turns oven cooling off."""
    res.query('C OFF')
