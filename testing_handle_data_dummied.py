import sm125_wrapper as interrogator_wrapper


def get_data_point_built_in(lan_socket):
    wavelengths, amplitudes, time_stamp, serial_number = interrogator_wrapper.get_data_built_in(lan_socket)
    ret_temp = "DUMMY_RET_TEMP"
    return ret_temp, wavelengths, amplitudes, time_stamp, serial_number
