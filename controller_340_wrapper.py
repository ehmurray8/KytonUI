def get_temp_c(res):
    """Return temperature reading in degrees C."""
    ret = res.query('CRDG? B')
    # ret2, b, c = ret.partition('E')
    # ret3 = ret2[1:len(ret2)]
    # ret3 = float(ret3)
    return ret  # ret3


def get_heater_output(res):
    """Return heater output as percentage of the maximum heater output."""
    return res.query('HTR?')


def get_temp_k(res):
    """Return temperature reading in degrees Kelvin."""
    ret = res.query('KRDG? B')
    ret2, b, c = ret.partition('E')
    ret3 = ret2[1:len(ret2)]
    # ret3 = float(ret3)
    return ret3


def get_pid(res):
    """Get PID values of the controller; return as a tuple: <P value>,<I value>,<D value>."""
    # return res.query('PID? {0}'.format(str(res.current_loop)))
    return res.query('PID? {0}'.format(1))


def get_set_point(res):
    """Get temperature setpoint."""
    # return res.query('SETP? {0}'.format(str(res.current_loop)))
    return res.query('SETP? {0}'.format(1))


def get_zone(res, zone):
    """Get the number of the zone that temp controller is currently in."""
    # return res.query('ZONE? {0},{1}'.format(str(res.current_loop), zone))
    return res.query('ZONE? {0},{1}'.format(1, zone))


def set_remote_mode(res):
    """Set temperature controller to remote mode WITHOUT local control lock-out."""
    res.query('MODE 1')


def set_pid(res, PVal, IVal, DVal):
    """Set PID for temperature controller and format input as integers."""
    # res.query('PID {0},{1},{2},'.format(str(res.current_loop), PVal, IVal, DVal))
    res.query('PID {0},{1},{2}, {3}'.format(1, PVal, IVal, DVal))
    # fix PID format string


def set_set_point(res, ptVal, current_loop):
    """Set temperature controller set-point value and take in integer value for ptVal."""
    res.query('SETP {0},{1}'.format(current_loop, ptVal))


def set_zone(res, zone, topVal, PVal, IVal, DVal, manualOut, range):
    """Set controller zones.

    Keyword arguments:
    zone - number of zone in table to configure.  Valid values: 1 to 10
    topVal - top temperature for zone.
    PVal -- proportional component.  Valid values: 0.1 to 1000
    IVal -- integral component.  Valid values: 0.1 to 1000
    DVal -- derivative component.  Valid values: 0 to 200%
    manualOut -- specifies manual output percentage for this zone.  Valid values: 0 to 100%
    range - heater range for this zone.  Valid values: 0 to 3
    """
    # res.query('ZONE {0},{1},{2},{3},{4},{5},{6},{7}'.format(str(res.current_loop), zone, topVal, PVal, IVal, DVal, manualOut, range))
    res.query('ZONE {0},{1},{2},{3},{4},{5},{6},{7}'.format(1, zone, topVal, PVal, IVal, DVal, manualOut, range))
