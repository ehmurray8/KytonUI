"""Contains containers for the data stored in the csv file."""
# pylint: disable=too-few-public-methods, too-many-instance-attributes


class Metadata(object):
    """Contains the metadata stored at the beginning of the csv file."""

    def __init__(self):
        self.start_time = 0
        self.start_temp = 0
        self.start_wavelen_avg = 0
        self.start_wavelens = []
        self.serial_nums = []


class DataCollection(object):
    """Contains the main csv file data."""

    def __init__(self):
        self.times = []  # times in seconds, removed repeat data

        self.temps = []  # temps in K, removed repeat data
        self.temp_diffs = []  # delta temperature from start

        self.powers = [[]]  # powers broken into lists by Serial Numbers
        # power delta from start broken into lists by Serial Numbers
        self.power_diffs = [[]]
        self.mean_power_diffs = []  # average power delta from start

        self.wavelens = [[]]  # wavelengths broken into lists by Serial Numbers
        # wavelength delta from start broken into lists by Serial Numbers
        self.wavelen_diffs = [[]]
        self.mean_wavelen_diffs = []  # average wavelength delta from start
        self.drift_rates = []  # drift rates in mk/min
        self.real_points = []  # list of which points are the "real" cal points
