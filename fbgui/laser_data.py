from typing import List
from fbgui.helpers import average


class LaserData:

    def __init__(self, switch_positions: List[List[int]], switch_channel_index):
        self.switch_positions = switch_positions
        self.switch_channel = switch_channel_index
        self._wavelengths = [[[] for _ in range(len(position_list))] for position_list in switch_positions]
        self._powers = [[[] for _ in range(len(position_list))] for position_list in switch_positions]

    def add_wavelengths(self, channel: int, wavelengths: List[float], position: int):
        if channel != self.switch_channel:
            position = 0
        self._add(channel, wavelengths, position, self._wavelengths)

    def add_powers(self, channel: int, powers: List[float], position: int):
        if channel != self.switch_channel:
            position = 0
        self._add(channel, powers, position, self._powers)

    def get_wavelengths(self) -> List[List[float]]:
        return average(self._wavelengths)

    def get_powers(self) -> List[List[float]]:
        return average(self._powers)

    def _add(self, channel: int, elements_to_add: List[float], position: int, elements: List[List[List[float]]]):
        start = self.switch_positions[channel].index(position)
        for i, element in enumerate(elements_to_add):
            elements[channel][start + i].append(element)
