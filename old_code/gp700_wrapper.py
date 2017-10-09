def op_complete_query(res):
    # return res.query("*OPC?") + "\n" + res.query("SYSTem:ERRor?")
    # return ""
    return res.query("SYSTem:ERRor?")


def disp_off_cmd(res):
    res.query("DISP:OFF")


def set_a(res, module, level):
    """Set attenuation level for specified module."""
    res.query('A{0} {1}\n'.format(module, level))


def get_a(res, module):
    """Return attenuation level for specified module."""
    # return res.query('A?')
    return res.query('A1? PROG:NEWL')  # .format(module))


def set_i(res, in_channel, out_channel):
    """Establishe optical connection between matrix input channel and out channel."""
    res.query('I{0] {1}'.format(in_channel, out_channel))


def get_i(res, module):
    """Return matrix module channel number."""
    return res.query('I{0}?'.format(module))


def set_m(res, module, channel):
    """Set matrix module output channel to apecified channel number."""
    res.query('M{0} {1}'.format(module, channel))


def get_m(res, module):
    """Return channel setting for specified module."""
    return res.query('M{0}?'.format(module))


def set_s(res, module, state):
    """Set output channel of two-position switch module to output state."""
    res.query('S{0} {1}'.format(module, state))


def get_s(res, module):
    """Get current output state of two-position switch module."""
    return res.query('S{0}?'.format(module))
