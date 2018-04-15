class Message(object):

    def __init__(self, warning, is_warn, args):
        self.warning_type = warning
        self.is_warning = is_warn
        self.args = args


class WarningHandler(object):

    def __init__(self):
        self.warnings = {"Excel": False, "File": False, "Program Running": False, "Config": False, "Location": False,
                         "Connection": False}
        pass

    def handle_msg(self, msg):
        """
        Handles showing a messagebox to the user without repeating itself.

        :param msg: Message object
        :return: A tuple of the title, and message for the message box.
        """
        if not self.warnings[msg.warning_type] and msg.is_warning:
            if msg.warning_type == "Excel":
                return ("Excel File Generation Error",
                        "No data has been recorded yet, or the database has been corrupted.")
            elif msg.warning_type == "File":
                return "File Error",

        elif not msg.is_warning:
            self.warnings[msg.warning_type] = False
