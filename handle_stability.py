from datetime import datetime, timedelta


class StabilityVars:
    stable_meas_count = 0
    dwell_start_timestamp = None


def check_in_band(test_temp, target_temp, bandwidth):
    upper_bound = target_temp + bandwidth / 2
    lower_bound = target_temp - bandwidth / 2
    if (test_temp >= lower_bound) and (test_temp <= upper_bound):
        print("MEASUREMENT IN BOUND")
        return True
    else:
        return False


def average_running_stability(running_temps):
    delta_list = []
    if len(running_temps) > 1:
        for i, v in enumerate(running_temps[:-1]):
            delta_list.append(running_temps[i + 1] - running_temps[i])
        delta_ave = sum(delta_list) / len(delta_list)
        return 1000 * abs(delta_ave)
    else:
        return 999999


def check_stability(running_temps, sp_stability, num_temps_for_drift):
    print("AVERAGED STABILITY: {}".format(average_running_stability(running_temps)))
    if average_running_stability(running_temps) <= sp_stability and len(running_temps) >= num_temps_for_drift:
        StabilityVars.stable_meas_count += 1
        print("STAB MEAS COUNT {}".format(StabilityVars.stable_meas_count))
        if StabilityVars.stable_meas_count >= num_temps_for_drift:
            print("STABLE SETPOINT")
            return True
        else:
            return False
    else:
        StabilityVars.stable_meas_count = 0
        return False


def check_dwell(dwell_start, dwell_in_seconds):
    if (datetime.now() - dwell_start) >= timedelta(seconds=dwell_in_seconds):
        return True
    else:
        return False


def range_index(look_up_temp, temperature_ranges):
    if 0 <= look_up_temp < temperature_ranges[0][0]:
        return 0
    elif temperature_ranges[0][0] <= look_up_temp < temperature_ranges[1][0]:
        return 1
    elif temperature_ranges[1][0] <= look_up_temp < temperature_ranges[2][0]:
        return 2
    elif temperature_ranges[2][0] <= look_up_temp < temperature_ranges[3][0]:
        return 3
    else:
        return 3


def check_if_in_band_stable_ready(set_point_temp, measured_temp, running_temps, temperature_ranges,
                                  dwell_time_value, num_temps_for_drift):
    print("CHECKING STABILITY SETPOINT: {} MEASURED TEMP: {} RUNNING TEMPS: {}".format(set_point_temp,
                                                                                       measured_temp, running_temps))
    bandwidth = temperature_ranges[int(range_index(measured_temp, temperature_ranges))][1]
    sp_stability = temperature_ranges[range_index(set_point_temp, temperature_ranges)][2]
    in_band_flag = check_in_band(measured_temp, set_point_temp, float(bandwidth))

    if in_band_flag:
        if StabilityVars.dwell_start_timestamp is None:
            StabilityVars.dwell_start_timestamp = datetime.now()
        if check_stability(running_temps, sp_stability,
                           num_temps_for_drift) and check_dwell(StabilityVars.dwell_start_timestamp, dwell_time_value):
            StabilityVars.stable_meas_count = 0
            return True
        else:
            return False
    else:
        return False
