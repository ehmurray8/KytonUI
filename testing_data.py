import testing_handle_data_dummied as data
import sm125_wrapper as interrogator_wrapper
import time
# from pprint import pprint


def data_test_setup():
    interrogator_location = '10.0.0.122'
    interrogator_port = 50000
    interrogator_socket = interrogator_wrapper.setup(interrogator_location, interrogator_port)

    wait_time_between_points = 2.0

    return interrogator_socket, wait_time_between_points


def data_test(interrogator_socket, wait_time_between_points):
    all_points_data = []

    for i in range(25):
        time.sleep(wait_time_between_points)
        sp_flag = "DUMMY_FLAG"

        temp, wlen, ampl, t_st, ser_num = data.get_data_point_built_in(interrogator_socket)
        all_points_data.append({'Temperature': temp,
                                'Wavelengths': wlen,
                                'Amplitudes': ampl,
                                'Setpoint': sp_flag,
                                'Serial number': ser_num,
                                'Time:': t_st})
        print({'Wavelengths': wlen,
               'Amplitudes': ampl,
               })

if __name__ == '__main__':
    interrogator_socket_, wait_time_between_points_ = data_test_setup()
    data_test(interrogator_socket_, wait_time_between_points_)
