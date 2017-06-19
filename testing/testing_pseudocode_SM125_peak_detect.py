from ctypes import *

search_peaks = getattr(windll.peakdetect, '?searchForPeaks@@YAXQANHNNNNNNHPAH00@Z')
search_valleys = getattr(windll.peakdetect, '?searchForValleys@@YAXQANHNNNNNNHPAH00@Z')
print(search_peaks)
print(search_valleys)


"""
def SM125_peak_detect:

    def __init__(parent_channel)
        self.MyParent = parent_channel

    def search()
        if not Settings.Enabled:
            break
        number_of_peaks = -1
        returnPower(Settings.MaximumPeaks)
        returnWavelength(Settings.MaximumPeaks)
        try:
            if Settings.SearchType = SearchType.Peaks:
                _search_for_peaks(MyParent.PWR, MyParent.PWR.Length, MyParent.WL(0),
                                MyParent.WL(1) - MyParent.WL(0), Settings.Width, Settings.Threshold,
                                Settings.WidthLevel, Settings.RelativeThreshold, Settings.MaximumPeaks,
                                numberOfPeaks, returnWavelength, returnPower)
            else:
                _search_for_valleys(MyParent.PWR, MyParent.PWR.Length, MyParent.WL(0), _
                                  MyParent.WL(1) - MyParent.WL(0), Settings.Width, Settings.Threshold, _
                                  Settings.WidthLevel, Settings.RelativeThreshold, Settings.MaximumPeaks, _
                                  numberOfPeaks, returnWavelength, returnPower)

            if numberOfPeaks = -1:
                raise InvalidExpressionException("Error communicating with peackdetect.dll")

            MyParent.Peaks = []
            for i in Range(0, numberOfPeaks - 1):
                MyParent.Peaks(i).Wavelength = returnWavelength(i)
                MyParent.Peaks(i).Power = returnPower(i)

        except ValueError:
            return False
        else:
            return True
"""



"""
def _searchForPeaks(ByVal traceBuf() As Double, ByVal nPoints As Integer, _
                   ByVal minWvl As Double, ByVal wvlInc As Double, ByVal _width As Double, _
                   ByVal _threshold As Double, ByVal _widthLevel As Double, _
                   ByVal _relThreshold As Double, ByVal maxPeaks As Integer, _
                   ByRef nPeaks As Integer, ByVal peakPos() As Double, _
                   ByVal peakLevel() As Double)

def _searchForValleys(ByVal traceBuf() As Double, ByVal nPoints As Integer, _
                     ByVal minWvl As Double, ByVal wvlInc As Double, ByVal _width As Double, _
                     ByVal _threshold As Double, ByVal _widthLevel As Double, _
                     ByVal _relThreshold As Double, ByVal maxPeaks As Integer, _
                     ByRef nPeaks As Integer, ByVal peakPos() As Double, _
                     ByVal peakLevel() As Double)
"""