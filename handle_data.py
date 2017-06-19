import controller_331_wrapper as controller_wrapper
import sm125_wrapper as interrogator_wrapper


# Old method, may re-implement in future
def get_data_point(controller, lan_socket):
    # Find peak method goes here.  Eventually calculate power method called from here.
    initial_temp = controller_wrapper.get_temp_k(controller)
    wavelength, amplitude, serial_number = interrogator_wrapper.get_data_built_in(lan_socket)
    # interrogator_data = interrogator_wrapper.process_raw(raw_data)
    # peak_list = peak_detection_wrapper(interrogator_data)
    final_temp = controller_wrapper.get_temp_k(controller)
    ret_temp = (initial_temp + final_temp)/2
    return ret_temp, wavelength, amplitude, serial_number


def get_data_point_built_in(controller, lan_socket):
    initial_temp = controller_wrapper.get_temp_k(controller)
    wavelengths, amplitudes, time_stamp, serial_number = interrogator_wrapper.get_data_built_in(lan_socket)
    final_temp = controller_wrapper.get_temp_k(controller)
    ret_temp = (initial_temp + final_temp) / 2
    return ret_temp, wavelengths, amplitudes, time_stamp, serial_number
