"""Contains object representations of all the necessary devices."""

# pylint:disable=missing-super-argument
import socket
from concurrent.futures import ThreadPoolExecutor
from socket import AF_INET, SOCK_STREAM
import numpy as np
import functools

WAVELEN_SCALE_FACTOR = 10000.0
AMP_SCALE_FACTOR = 100.0

IOPool = ThreadPoolExecutor(4)


class SM125(socket.socket):
    """TCP socket connection for SM125 device."""
    def __init__(self, address, port, loop):
        super().__init__(AF_INET, SOCK_STREAM)
        self.loop = loop
        self.loop.run_until_complete(self.connect_dev(address, port))

    async def connect_dev(self, address, port):
        await self.loop.run_in_executor(IOPool, super().connect, (address, port))

    async def get_data(self):
        """Returns the SM125 wavelengths, amplitudes, and lengths of each channel."""
        await self.loop.run_in_executor(IOPool, self.send, b'#GET_PEAKS_AND_LEVELS')
        pre_response = await self.loop.run_in_executor(IOPool, self.recv, 10)
        response = await self.loop.run_in_executor(IOPool, self.recv, int(pre_response))
        chan_lens = np.fromstring(response[:20], dtype='3uint32, 4uint16')[0][1]
        total_peaks = sum(chan_lens)

        wave_start_idx = 32
        wave_end_idx = wave_start_idx + 4 * total_peaks
        wavelengths = np.fromstring(response[wave_start_idx:wave_end_idx], dtype=(str(total_peaks) + 'int32'))
        amp_start_idx = wave_end_idx
        amp_end_idx = amp_start_idx + 2 * total_peaks
        amplitudes = np.fromstring(response[amp_start_idx:amp_end_idx], dtype=(str(total_peaks) + 'int16'))

        wavelengths_list = [en / WAVELEN_SCALE_FACTOR for en in wavelengths]
        amplitudes_list = [en / AMP_SCALE_FACTOR for en in amplitudes]
        return wavelengths_list[0], amplitudes_list[0], chan_lens


class Oven(object):
    """Delta oven object, uses pyvisa."""
    def __init__(self, port, manager, loop):
        self.device = None
        self.loop = loop
        loc = "GPIB0::{}::INSTR".format(port)
        self.loop.run_until_complete(self.connect_dev(loc, manager))

    async def connect_dev(self, loc, manager):
        self.device = \
            await self.loop.run_in_executor(IOPool, functools.partial(manager.open_resource, loc, read_termination="\n"))

    async def set_temp(self, temp):
        """Sets set point of delta oven."""
        await self.loop.run_in_executor(IOPool, self.device.query, 'S {}'.format(temp))

    async def heater_on(self):
        """Turns oven heater on."""
        await self.loop.run_in_executor(IOPool, self.device.query, 'H ON')

    async def heater_off(self):
        """Turns oven heater off."""
        await self.loop.run_in_executor(IOPool, self.device.query, 'H OFF')

    async def cooling_on(self):
        """Turns oven cooling on."""
        await self.loop.run_in_executor(IOPool, self.device.query, 'C ON')

    async def cooling_off(self):
        """Turns oven cooling off."""
        await self.loop.run_in_executor(IOPool, self.device.query, 'C OFF')

    def close(self):
        """Closes the resource."""
        self.device.close()


class OpSwitch(socket.socket):
    """Object representation of the Optical Switch needed for the program."""

    def __init__(self, addr, port, loop):
        super().__init__(AF_INET, SOCK_STREAM)
        self.loop = loop
        self.loop.run_until_complete(self.connect_dev(addr, port))

    async def connect_dev(self, addr, port):
        await self.loop.run_in_executor(IOPool, self.connect, (addr, port))

    async def set_channel(self, chan):
        """Sets the channel on the optical switch."""
        msg = "<OSW{}_OUT_{}>".format(format(int(1), '02d'), format(int(chan), '02d'))
        await self.loop.run_in_executor(IOPool, self.send, msg.encode())


class TempController(object):
    """Object representation of the Temperature Controller needed for the program."""
    def __init__(self, port, manager, loop):
        self.device = None
        self.loop = loop
        loc = "GPIB0::{}::INSTR".format(port)
        self.loop.run_until_complete(self.connect_dev(loc, manager))

    async def connect_dev(self, loc, manager):
        self.device = await \
            self.loop.run_in_executor(IOPool, functools.partial(manager.open_resource, loc, read_termination='\n'))

    async def get_temp_c(self):
        """Return temperature reading in degrees C."""
        query = await self.loop.run_in_executor(IOPool, self.device.query, 'CRDG? B')
        return query[:-4]

    async def get_temp_k(self):
        """Return temperature reading in degrees Kelvin."""
        query = await self.loop.run_in_executor(IOPool, self.device.query, 'KRDG? B')
        return query[:-4]

    def close(self):
        """Close the device connection."""
        self.device.close()
