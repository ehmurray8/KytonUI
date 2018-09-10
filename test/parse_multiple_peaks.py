"""
Channel 1 | Channel 2 | Channel 3 | Channel 4
0           1                       0
0           4                       0
            4
            7

Averaging two data collections together
"""

from typing import List
from fbgui.laser_data import LaserData

EXPECTED = [[11, 16], [21, 31, 36, 41], [], [51, 56]]

READINGS = [
    # (Switch #1)
    [
        # First Collection
        [
            [10, 15],
            [20],
            [0],
            [50, 55]
        ],
        # Second Collection
        [
            [12, 17],
            [22],
            [0],
            [52, 57]
        ],
    ],
    # (Switch #4)
    [
        # First Collection
        [
            [12, 17],
            [30, 35],
            [0],
            [52, 57]
        ],
        # Second Collection
        [
            [10, 15],
            [32, 37],
            [0],
            [50, 55]
        ]
    ],
    # (Switch #7)
    [
        # First Collection
        [
            [10, 15],
            [40],
            [0],
            [50, 55]
        ],
        # Second Collection
        [
            [12, 17],
            [42],
            [0],
            [52, 57]
        ]
    ]
]


def collect_data(switch_positions: List[List[int]], number_to_average: int, switch_channel_index: int):
    laser_data = LaserData(switch_positions, switch_channel_index)
    for switch_number, switch_position in enumerate(sorted(set(switch_positions[switch_channel_index]))):
        _switch_to(switch_position)
        for run_number in range(number_to_average):
            for channel in range(4):
                if len(switch_positions[channel]):
                    laser_data.add_wavelengths(channel, READINGS[switch_number][run_number][channel], switch_position)
    wavelengths = laser_data.get_wavelengths()
    assert wavelengths == EXPECTED


def _switch_to(position: int):
    pass


if __name__ == "__main__":
    SWITCH_POSITIONS = [[0, 0], [1, 4, 4, 7], [], [0, 0]]
    NUMBER_TO_AVERAGE = 2
    SWITCH_CHANNEL_INDEX = 1
    collect_data(SWITCH_POSITIONS, NUMBER_TO_AVERAGE, SWITCH_CHANNEL_INDEX)
