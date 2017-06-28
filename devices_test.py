import time

import visa

import controller_340_wrapper as controller_wrapper
import gp700_wrapper
import sm125_wrapper as interrogator_wrapper

term_char = '/n'

controller_location = "GPIB::12::INSTR"
oven_location = "GPIB0::27::INSTR"
gp700_location = "GPIB0::09::INSTR"
interrogator_location = "10.0.0.122"
interrogator_port = 50000
num_temps_for_drift = 5
wait_time_between_points = 2.0
list_of_sp = "[50.0, 100.0, 150.0]"
dwell_time_value = 8
temperature_ranges = "[[20, 20.0, 50], [50, 15.0, 50], [100, 20.0, 50], [1000, 20.0, 50]]"

# Create resource manager
resource_manager = visa.ResourceManager()
print(resource_manager.list_resources())

# Create GPIB agents
controller = resource_manager.open_resource(controller_location, read_termination=term_char)

# Create oven
oven = resource_manager.open_resource(oven_location, read_termination=term_char)

gp700 = resource_manager.open_resource(gp700_location, read_termination=term_char)

# Setup socket to interrogator
interrogator_socket = interrogator_wrapper.setup(interrogator_location, interrogator_port)

# Oven testing
# print("Turning oven cooling on...")
# oven_wrapper.cooling_on(oven)
# time.sleep(2)

# print("Setting oven temperature to 251.2...")
# oven_wrapper.set_temp(oven, 251.2)
# time.sleep(2)

# print("Turning oven cooling off...")
# oven_wrapper.cooling_off(oven)
# time.sleep(2)

# print("Turning oven heater on...")
# oven_wrapper.heater_on(oven)
# time.sleep(2)

# print("Turning oven heater off...")
# oven_wrapper.heater_off(oven)
# time.sleep(2)

# Temp Controller Testing
print("Heater output: " + controller_wrapper.get_heater_output(controller))

print("PID: " + controller_wrapper.get_pid(controller))

print("Set point: " + controller_wrapper.get_set_point(controller))

print("Temperature Celsius: " + controller_wrapper.get_temp_c(controller))

print("Temperature Kelvin: " + controller_wrapper.get_temp_k(controller))

print("Zone: " + controller_wrapper.get_zone(controller, 1))

print("Setting PID to 100, 100, 100")
controller_wrapper.set_pid(controller, 100, 100, 100)
time.sleep(2)

# print("Setting remote mode...")
# controller_wrapper.set_remote_mode(controller);
# time.sleep(2)

print("Setting oven set point to 333.333...")
controller_wrapper.set_set_point(controller, 333.333, 1)

# print("Setting zone up...")
# controller_wrapper.set_zone(controller, 1, 400, 27, 28, 29, 67, 1)

# SM125 Testing
# print("Data: " + interrogator_wrapper.get_data(interrogator_socket))

# print("Built in Data: " + interrogator_wrapper.get_data_built_in(interrogator_socket))

# GP700 Testing
print("Disp Off")
print("Error: " + gp700_wrapper.op_complete_query(gp700))
print("Attenuation level: " + gp700_wrapper.get_a(gp700, 8))

# print("Matrix channel select: " + gp700_wrapper.get_i(gp700, 1))

# print("M type module channel select: " + gp700_wrapper.get_m(gp700, 1))

# print("Setting attenuation level to 20...")
# gp700_wrapper.set_a(gp700, 1, 20)
# time.sleep(2)

# print("Setting M-type module channel to 2...")
# gp700_wrapper.set_m(gp700, 1, 2)
# time.sleep(2)

# print("Setting Matrix channel select to 5...")
# gp700_wrapper.set_i(gp700, 2, 10)
