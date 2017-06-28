from socket import *

import numpy

soc = socket(AF_INET, SOCK_STREAM)
print("connecting socket")
soc.connect(('10.0.0.122', 50000))
print("sending data request")
soc.send(b'#GET_DATA')
print("receiving data")
pre_response = soc.recv(10)
# print(int(pre_response))
# response = soc.recv(int(pre_response))
response = soc.recv(int(pre_response))

"""main_header_size, protocol_version, number_of_duts, reserved, counter, size_of_sub_header_one, \
 min_wavelength, wavelength_increment, number_of_data_points, \
 dut_number = numpy.fromstring(response[:40], dtype=numpy.uint32, count=10)"""
print(len(response))
data_output = numpy.fromstring(response[:40], dtype='<5u4, <5u4')  # , count=1 APPEND?
data_output2 = numpy.fromstring(response[40:], dtype='<u2')

print(len(response[40:]))

print(data_output)
print(len(data_output2))
print(data_output2)

"""print('main_header_size {}\n protocol_version {}\n number_of_duts {}\n '
      'reserved {}\n counter {}\n size_of_sub_header_one {}\n min_wavelength {}\n '
      'wavelength_increment {}\n number_of_data_points {}\n dut_number {}'.format(main_header_size,  protocol_version,
                                                                               number_of_duts, reserved, counter,
                                                                               size_of_sub_header_one, min_wavelength,
                                                                               wavelength_increment,
                                                                               number_of_data_points, dut_number))
"""
# print(list(v))
# w = numpy.fromstring(response[40:2*number_of_data_points], dtype=numpy.int16)
# print(list(w))
# print(2*len(list(w)))
# response_to_int = int.from_bytes(response, byteorder='little')


# inter_data = response[40:int(2*number_of_data_points)]

"""print('Sub header size is {}\n Minimum wlength is {}\n Wavelength incr is {}\n # data points is {}\n'
      ' DUT number is {}\n data is {}'.format(sub_header_size, min_wavelength, wavelength_increment,
                                              number_data_points, DUT_number, inter_data2))
"""
# print(number_data_points)
# print(len(inter_data))

# print(list(inter_data))

# print(inter_data.read('int:16'))

# v = struct.unpack("<16i", inter_data)
# print(v)
"""
id_list = []
id_ba = bytearray(inter_data)
for x in range(0, len(id_ba)):
    id_list.append(id_ba[x])
    #print(id_ba[x])

plt.plot(id_list)
plt.show()
"""
