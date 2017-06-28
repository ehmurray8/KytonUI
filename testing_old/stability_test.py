import time

import handle_stability as stability


def stab_test(dummy_temps, num_temps_for_drift, wait_time_between_points, list_of_sp,
              temperature_ranges, dwell_time_value):
    cancel_run_flag = False
    running_temps = []
    all_points_data = []
    set_points_only_data = []

    for sp in list_of_sp:
        while not cancel_run_flag:
            time.sleep(wait_time_between_points)
            temp = dummy_temps.pop(0)
            running_temps.append(temp)

            if len(running_temps) > num_temps_for_drift:
                running_temps.pop(0)

            sp_flag = stability.check_if_in_band_stable_ready(sp, temp, running_temps,
                                                              temperature_ranges, dwell_time_value, num_temps_for_drift)

            temp, wlen, ampl, t_sec, t_msec, ser_num = ('A', 'B', 'C', 'D', 'E', 'F')
            all_points_data.append({'Temperature': temp,
                                    'Wavelengths': wlen,
                                    'Amplitudes': ampl,
                                    'Setpoint': sp_flag,
                                    'Serial number': ser_num,
                                    'Time seconds': t_sec,
                                    'Time milliseconds': t_msec})
            if sp_flag:
                set_points_only_data.append({'Temperature': temp,
                                             'Wavelengths': wlen,
                                             'Amplitudes': ampl,
                                             'Setpoint': sp_flag,
                                             'Serial number': ser_num,
                                             'Time seconds': t_sec,
                                             'Time milliseconds': t_msec})
                break


if __name__ == '__main__':
    dummy_temps_ = [50.0] * 3 + [100.0] * 6 + [20.0] * 3 + [150.0] * 6
    num_temps_for_drift_ = 3
    wait_time_between_points_ = 2.0
    list_of_sp_ = [100, 150]
    temperature_ranges_ = [[20, 10.0, 5], [50, 20.0, 5], [100, 20.0, 5], [1000, 20.0, 5]]
    dwell_time_value_ = 0

    stab_test(dummy_temps_, num_temps_for_drift_, wait_time_between_points_, list_of_sp_, temperature_ranges_,
              dwell_time_value_)
