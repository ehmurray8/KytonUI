class DataCollection:

    def __init__(self):
        self.times = [] #times in seconds, removed repeat data 
        self.temps = [] #temps in K, removed repeat data
        self.wavelens = [[]] #wavelengths broken into lists by Serial Numbers
        self.powers = [[]] #powers broken into lists by Serial Numbers
        self.wavelen_diffs = [[]] #wavelength delta from start broken into lists by Serial Numbers
        self.mean_wavelen_diffs = [] #average wavelength delta from start
