def mp_execute(res, slot):
    """Executes mini program in slot PROG<slot>."""
    res.write("PROG{0}:EXEC".format(slot))


def mp_abort(res, slot):
    """Aborts mini program in slot PROG<slot>."""
    res.write("PROG{0}:ABORT".format(slot))


def mp_line(res, slot, command):
    """Writes new line to mini program slot PROG<slot>."""
    res.write("PROG{0}:NEWL {1}".format(slot, command))


def mp_delete(res, slot):
    """Set attenuation level for specified in slot PROG<slot>."""
    res.write('PROG{0}:DEL'.format(slot))


def comm_start_line(res, slot):
    """Start-line command for mini-program in PROG<slot>."""
    return res.write('MBEG{0}'.format(slot))


def comm_end_line(res):
    """End-line command for mini-program in PROG<slot>."""
    return res.write('MEND')


def comm_set_a(res, module, level):
    """Set attenuation level for specified module."""
    return 'A{0} {1}'.format(module, level)


def comm_get_a(res, module):
    """Return attenuation level for specified module."""
    return 'A{0}?'.format(module)


def comm_set_i(res, in_channel, out_channel):
    """Establishe optical connection between matrix input channel and out channel."""
    return 'I{0] {1}'.format(in_channel, out_channel)


def comm_get_i(res, module):
    """Return matrix module channel number."""
    return 'I{0}?'.format(module)


def comm_set_m(res, module, channel):
    """Set matrix module output channel to apecified channel number."""
    return 'M{0} {1}'.format(module, channel)


def comm_get_m(res, module):
    """Return channel setting for specified module."""
    return 'M{0}?'.format(module)


def comm_set_s(res, module, state):
    """Set output channel of two-position switch module to output state."""
    return 'S{0} {1}'.format(module, state)


def comm_get_s(res, module):
    """Get current output state of two-position switch module."""
    return 'S{0}?'.format(module)


def comm_loop_begin(res, times):
    """Loop start point command for mini-program.  Times variable is the number of times the loop will run"""
    return 'BLOOP {0}'.format(times)


def comm_loop_end():
    """Loop end point command for mini-program"""
    return 'ELOOP'
