from socket import *

import numpy

soc = socket(AF_INET, SOCK_STREAM)
print("connecting socket")
soc.connect(('10.0.0.122', 50000))
print("sending data request")
soc.send(b'#GET_PEAKS_AND_LEVELS')
print("receiving data")
pre_response = soc.recv(10)
response = soc.recv(int(pre_response))
formatted_response = numpy.fromstring(response[:20], dtype='3uint32, 4uint16')
time_stamp_sec, time_stamp_msec, serial_number = formatted_response[0][0]
ns1, ns2, ns3, ns4 = formatted_response[0][1]

print(time_stamp_sec, time_stamp_msec, serial_number)

total_peaks = ns1 + ns2 + ns3 + ns4

print(str(total_peaks) + 'int32')

wavelengths = numpy.fromstring(response[32:32 + 4 * total_peaks], dtype=(str(total_peaks) + 'int32'))
amplitudes = numpy.fromstring(response[32 + 4 * total_peaks:32 + 6 * total_peaks], dtype=(str(total_peaks) + 'int16'))

print(wavelengths, amplitudes)
