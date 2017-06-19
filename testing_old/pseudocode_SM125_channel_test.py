"""
def class SM125_channel(IWavelengthScan):

    #implements IWavelengthScan
    Friend Enum channelState
        Active = 1
        inactive = 0
    End Enum

    def __init__(SM125_communicator, channel_number)
        self.my_comm = SM125_communicator
        self.chnl_num = channel_number
    def __init__(SM125_communicator, channel_number, name)
        self.my_comm = SM125_communicator
        self.chnl_num = channel_number
        self.channel_name = name

    @property
    def current_state()
        Dim CS As String
        CS = MyComm.UserCommand("#GET_DUT" & ChnlNum & "_STATE")
        If CS.Chars(CS.Length - 3) = "1" Then Return channelState.Active
        If CS.Chars(CS.Length - 3) = "0" Then Return channelState.inactive

    @current_state.setter
    def current_state()
        Set(ByVal Value As channelState)
            MyComm.UserCommand("#SET_DUT" & ChnlNum & "_STATE " _& Value)

    def num_points()
        return _Wl.Length

    def is_peak_point(wavelength)
            for pk in peaks:
                if pk.wavelength = wavelength:
                    return True
            return False

    @property
    def WL() #extends IWavelengthScan.Wavelengths
            return _Wl

    @WL.setter(value)
    def WL() #extends IWavelengthScan.Wavelengths
            if value.length != _Wl.length:
                _Wl() = []
            array.Copy(Value, _Wl, Value.Length)

    @property
    def PWR() #IWavelengthScan.Powers
        return _Pwr

    @PWR.setter(value)
    def PWR() #IWavelengthScan.Powers
            if value.length != _Pwr.length:
                _Pwr = []
            array.Copy(Value, _Pwr, Value.Length)

"""