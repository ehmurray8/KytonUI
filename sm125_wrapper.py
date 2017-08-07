"""Module used to interface with Micron Options SM125 device."""
#pylint:disable=unused-variable

import struct
from socket import * #pylint:disable=unused-wildcard-import, wildcard-import

import numpy


def setup(interrogator_location, interrogator_port):
    """Sets up a socket using a location and a port."""
    soc = socket(AF_INET, SOCK_STREAM)
    soc.connect((interrogator_location, interrogator_port))
    return soc


def get_data(soc):
    """Return interrogator output data. Soc is TCP socket location of device."""
    soc.send(b'#GET_DATA')
    pre_response = soc.recv(10)
    return soc.recv(int(pre_response))


def get_data_actual(soc):
    #pylint:disable=missing-docstring, too-many-locals
    wavelength_scale_factor = 10000.0
    amplitude_scale_factor = 100.0
    soc = socket(AF_INET, SOCK_STREAM)
    #print("connecting socket")
    soc.connect(('10.0.0.122', 50000))
    #print("sending data request")
    soc.send(b'#GET_PEAKS_AND_LEVELS')
    #print("receiving data")
    pre_response = soc.recv(10)
    response = soc.recv(int(pre_response))
    formatted_response = numpy.fromstring(response[:20], dtype='3uint32, 4uint16')
    time_stamp_sec, time_stamp_msec, serial_number = formatted_response[0][0]
    ns1, ns2, ns3, ns4 = formatted_response[0][1]

    #print(time_stamp_sec, time_stamp_msec, serial_number)

    total_peaks = ns1 + ns2 + ns3 + ns4

    #print(str(total_peaks) + 'int32')

    wavelengths = numpy.fromstring(response[32:32 + 4 * total_peaks], \
            dtype=(str(total_peaks) + 'int32'))
    amplitudes = numpy.fromstring(response[32 + 4 * total_peaks:32 + 6 * total_peaks], \
            dtype=(str(total_peaks) + 'int16'))
    wavelengths_list = [en / wavelength_scale_factor for en in wavelengths]
    amplitudes_list = [en / amplitude_scale_factor for en in amplitudes]

    #wavelens_by_chan = [[], [], [], []]
    #wavelens_by_chan[0] = wavelengths_list[:ns1]
    #wavelens_by_chan[1] = wavelengths_list[ns1:ns1+ns2]
    #wavelens_by_chan[2] = wavelengths_list[ns1+ns2:ns1+ns2+ns3]
    #wavelens_by_chan[3] = wavelengths_list[ns1+ns2+ns3:]
    chan_lens = [ns1, ns2, ns3, ns4]

    return wavelengths_list, amplitudes_list, chan_lens 


def get_data_built_in(soc):
    #pylint:disable=too-many-locals
    """
    Return wavelength and amplitude using SM125's built in peak detector.
    Soc is TCP location of interrogator.
    """
    wavelength_scale_factor = 10000.0
    amplitude_scale_factor = 100.0
    soc.send(b'#GET_PEAKS_AND_LEVELS')
    pre_response = soc.recv(10)
    response = soc.recv(int(pre_response))
    formatted_response = numpy.fromstring(response[:20], dtype='3uint32, 4uint16')
    time_stamp_sec, time_stamp_micro_sec, serial_number = formatted_response[0][0]
    time_stamp = time_stamp_sec + time_stamp_micro_sec / 1000000.0
    ns1, ns2, ns3, ns4 = formatted_response[0][1]

    total_peaks = ns1 + ns2 + ns3 + ns4

    wavelengths = numpy.fromstring(response[32:32 +     4 * total_peaks], \
            dtype=(str(total_peaks) + 'int32'))
    amplitudes = numpy.fromstring(response[32 + 4 * total_peaks:32 + 6 * total_peaks],
                                  dtype=(str(total_peaks) + 'int16'))
    wavelengths_list = [en / wavelength_scale_factor for en in wavelengths]
    amplitudes_list = [en / amplitude_scale_factor for en in amplitudes]
    return wavelengths_list, amplitudes_list, time_stamp  # , serial_number

def get_data_channels(soc, channels):
    #pylint:disable=too-many-locals
    """
    Return wavelength and amplitude using SM125's built in peak detector.
    Soc is TCP location of interrogator.
    """
    wavelength_scale_factor = 10000.0
    amplitude_scale_factor = 100.0
    soc.send(b'#GET_PEAKS_AND_LEVELS')
    pre_response = soc.recv(10)
    response = soc.recv(int(pre_response))
    formatted_response = numpy.fromstring(response[:20], dtype='3uint32, 4uint16')
    time_stamp_sec, time_stamp_micro_sec, serial_number = formatted_response[0][0]
    time_stamp = time_stamp_sec + time_stamp_micro_sec / 1000000.0
    ns1, ns2, ns3, ns4 = formatted_response[0][1]

    total_peaks = ns1 + ns2 + ns3 + ns4

    wavelengths = numpy.fromstring(response[32:32 + 4 * total_peaks], \
            dtype=(str(total_peaks) + 'int32'))

    amplitudes = numpy.fromstring(response[32 + 4 * total_peaks:32 + 6 * total_peaks],
                                  dtype=(str(total_peaks) + 'int16'))
    wavelengths_list = [en / wavelength_scale_factor for en in wavelengths]
    amplitudes_list = [en / amplitude_scale_factor for en in amplitudes]

    chan1_waves = wavelengths_list[0:ns1]
    chan2_waves = wavelengths_list[ns1:ns2+ns1]
    chan3_waves = wavelengths_list[ns1+ns2:ns3+ns2+ns1]
    chan4_waves = wavelengths_list[ns1+ns2+ns3:]

    chan1_amps = amplitudes_list[0:ns1]
    chan2_amps = amplitudes_list[ns1:ns2+ns1]
    chan3_amps = amplitudes_list[ns1+ns2:ns3+ns2+ns1]
    chan4_amps = amplitudes_list[ns1+ns2+ns3:]

    channels = list(set(channels)).sort()
    waves_coll = [[]]
    amps_coll = [[]]
    for channel in channels:
        if channel == 1:
            waves_coll.append(chan1_waves)
            amps_coll.append(chan1_amps)
        elif channel == 2:
            waves_coll.append(chan1_waves)
            amps_coll.append(chan1_amps)
        elif channel == 3:
            waves_coll.append(chan1_waves)
            amps_coll.append(chan1_amps)
        elif channel == 4:
            waves_coll.append(chan1_waves)
            amps_coll.append(chan1_amps)

    return waves_coll, amps_coll  # , serial_number


# IMPLEMENT to use numpy instead of struct library
def process_raw(raw_data):
    """Process raw_data binary data. Return it as a structure."""
    sub_header = raw_data[160:320]
    size, min_wl, wl_inc, num_points, dut_num = struct.unpack('<IIIII', sub_header)
    sub_data = raw_data[320:16 * num_points]
    return struct.unpack('<i', sub_data)
