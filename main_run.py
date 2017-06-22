import time
import visa
import handle_stability as stability
# import testing_dummy_vars as data
import handle_data as data
import contoller_340_wrapper as controller_wrapper
import sm125_wrapper as interrogator_wrapper
import delta_oven_wrapper as oven_wrapper
import tkinter as tk
import ui_module
import config

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

"""
Uses UI to do basic setup.
"""
def setup():
    # Collect settings from GUI
    term_char = '/n'
    (controller_location, oven_location, interrogator_location, interrogator_port, num_temps_for_drift,
    wait_time_between_points, list_of_sp, dwell_time_value, temperature_ranges) = app.gather_settings

    # Create resource manager
    resource_manager = visa.ResourceManager()

    # Create GPIB agents
    controller = resource_manager.open_resource(controller_location, read_termination=term_char)

    # Create oven resource and turn on heater
    oven = resource_manager.open_resource(oven_location, read_termination=term_char)
    oven_wrapper.heater_on(oven)

    # Setup socket to interrogator
    interrogator_socket = interrogator_wrapper.setup(interrogator_location, interrogator_port)

    # Temporary dummy variables
    temperature_ranges = [[20, 4.0, 65], [50, 4.0, 65], [100, 4.0, 65], [1000, 4.0, 65]]
    list_of_sp = [100.0, 125.0, 150.0]

    # root.mainloop()

    return controller, oven, interrogator_socket, num_temps_for_drift, wait_time_between_points,\
        list_of_sp, temperature_ranges, dwell_time_value


def main_control(app, controller, oven, interrogator_socket, num_temps_for_drift, wait_time_between_points,
                 list_of_sp, dwell_time_value, temperature_ranges):
    cancel_run_flag = False
    running_temps = []
    fig = plt.Figure()
    graph = fig.add_subplot(111)
    # data_header = ['Temperature', 'Wavelengths', 'Amplitudes', 'Setpoint', 'Serial number', 'Time seconds',
    # 'Time milliseconds']

    for sp in list_of_sp:
        # Set set point for controller
        controller_wrapper.set_set_point(controller, sp, 1)

        # Set temperature of oven
        oven_wrapper.set_temp(oven, sp)
        while not cancel_run_flag:
            graph.clear()
            # pprint(set_points_only_data)
            x = [config.set_points_only_data[en][1] for en in range(len(config.set_points_only_data))]
            y = [config.set_points_only_data[en][2] for en in range(len(config.set_points_only_data))]
            # graph.plot(x, y)
            app.update_plot(x, y)
            time.sleep(wait_time_between_points)
            temp = controller_wrapper.get_temp_c(controller)

            running_temps.append(temp)

            if len(running_temps) > num_temps_for_drift:
                running_temps.pop(0)

            sp_flag = stability.check_if_in_band_stable_ready(sp, temp, running_temps,
                                                              temperature_ranges, dwell_time_value, num_temps_for_drift)

            # print("### {}".format(data.get_data_point_built_in(controller, interrogator_socket)))
            temp, wlen, ampl, t_st, ser_num = data.get_data_point_built_in(controller, interrogator_socket)
            config.all_points_data.append((temp, wlen, ampl, sp_flag, ser_num, t_st))
            if sp_flag:
                config.set_points_only_data.append((temp, wlen, ampl, sp_flag, ser_num, t_st))
                break
            # return set_points_only_data, all_points_data

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)

    config.root = tk.Tk()
    config.root.wm_title("Options Panel")
    app = ui_module.Application(config.root)
    app.mainloop()

    # Gather settings from setup
    controller_, oven_, interrogator_socket_, num_temps_for_drift_, wait_time_between_points_, list_of_sp_, temperature_ranges_, dwell_time_value_ = setup()

    # Run main control loop
    main_control(controller_, oven_, interrogator_socket_, num_temps_for_drift_, wait_time_between_points_, list_of_sp_, temperature_ranges_, dwell_time_value_)

    # print(ret_values[0])
