"""
Channel 1 | Channel 2 | Channel 3 | Channel 4
0           1                       0
0           4                       0
            4
            7

Averaging two data collections together
"""

from fbgui.laser_data import LaserData
import unittest


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


class TestMultiplePeaks(unittest.TestCase):

    def setUp(self):
        super().setUp()
        self.switch_positions = [[0, 0], [1, 4, 4, 7], [], [0, 0]]
        self.number_to_average = 2
        self.switch_channel_index = 1

    def test_laser_data(self):
        laser_data = LaserData(self.switch_positions, self.switch_channel_index)
        for switch_number, switch_position in enumerate(sorted(set(self.switch_positions[self.switch_channel_index]))):
            for run_number in range(self.number_to_average):
                for channel in range(4):
                    if len(self.switch_positions[channel]):
                        laser_data.add_wavelengths(channel, READINGS[switch_number][run_number][channel],
                                                   switch_position)
        wavelengths = laser_data.get_wavelengths()
        self.assertEqual(wavelengths, EXPECTED)


if __name__ == "__main__":
    unittest.main()
