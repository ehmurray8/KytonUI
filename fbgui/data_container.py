"""Contains containers for the data stored in the csv file."""


class DataCollection(object):
    """Contains the main csv file data."""

    def __init__(self):
        self.times = []  # delta time in hours
        self.times_real = []
        self.timestamps = []  # timestamps
        self.timestamps_real = []

        self.temps = []  # temps in K, removed repeat data
        self.temp_diffs = []  # delta temperature from start
        self.temp_diffs_real = []

        self.powers = []  # powers broken into lists by Serial Numbers
        self.powers_real = []
        # 2D,  power delta from start broken into lists by Serial Numbers
        self.power_diffs = []
        self.mean_power_diffs = []  # average power delta from start
        self.power_diffs_real = []
        self.mean_power_diffs_real = []

        self.wavelens = []  # 2D, wavelengths broken into lists by Serial Numbers
        self.wavelens_real = []
        # 2D, wavelength delta from start broken into lists by Serial Numbers
        self.wavelen_diffs = []
        self.wavelen_diffs_real = []
        self.mean_wavelen_diffs = []  # average wavelength delta from start
        self.mean_wavelen_diffs_real = []
        self.drift_rates = []  # 2D, drift rates in mk/min
        self.real_points = []  # list of which points are the "real" cal points
        self.avg_drift_rates = []  # average drift rates in mK/min
