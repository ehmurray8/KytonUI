import time
import visa
import controller_340_wrapper as controller_wrapper
import sm125_wrapper as interrogator_wrapper
import delta_oven_wrapper as oven_wrapper
import gp700_wrapper

term_char = '/n'

controller_location = "GPIB::12::INSTR"
oven_location = "GPIB0::27::INSTR"
gp700_location = "GPIB::3::INSTR"
interrogator_location = "10.0.0.122"
interrogator_port = 50000

def setup_instruments():
     # Create resource manager
     resource_manager = visa.ResourceManager()

     # Create GPIB agents
     controller = resource_manager.open_resource(controller_location, read_termination=term_char)

     # Create oven
     oven = resource_manager.open_resource(oven_location, read_termination=term_char)

     gp700 = resource_manager.open_resource(gp700_location, read_termination=term_char)

     # Setup socket to interrogator
     interrogator_socket = interrogator_wrapper.setup(interrogator_location, interrogator_port)
     return controller, oven, gp700, interrogator_socket
