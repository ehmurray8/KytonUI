import visa

import sm125_wrapper as interrogator_wrapper




def setup_instruments():
    # Create resource manager
    

    # Create GPIB agents
    controller = resource_manager.open_resource(controller_location, read_termination=term_char)

    # Create oven
    oven = resource_manager.open_resource(oven_location, read_termination=term_char)

    gp700 = resource_manager.open_resource(gp700_location, read_termination=term_char)

    # Setup socket to interrogator
    interrogator_socket = interrogator_wrapper.setup(interrogator_location, interrogator_port)
    return controller, oven, gp700, interrogator_socket
