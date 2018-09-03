"""
Channel 1 | Channel 2 | Channel 3 | Channel 4
0           1                       0
0           4                       0
            4
            7

Averaging two data collections together
"""

from typing import List
from collections import Counter

results = [
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
            [11, 16],
            [21],
            [0],
            [51, 56]
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
            [13, 18],
            [31, 36],
            [0],
            [53, 58]
        ]
    ],
    # (Switch #7)
    [
        # First Collection
        [
            [14, 19],
            [40],
            [0],
            [54, 59]
        ],
        # Second Collection
        [
            [13, 18],
            [41],
            [0],
            [53, 58]
        ]
    ]
]


def collect_data(fbgs: List[float], switch_positions: List[List[float]], number_to_average: int,
                 switch_channel_index: int):
    for run_number in range(number_to_average):
        for switch_position in set(switch_positions):
            pass


def _switch_to(position: int):
    pass


if __name__ == "__main__":
    FBGS = [2, 4, 0, 2]
    SWITCH_POSITIONS = [[0], [1, 4, 7], [0], [0]]
    NUMBER_TO_AVERAGE = 2
    SWITCH_CHANNEL_INDEX = 1
