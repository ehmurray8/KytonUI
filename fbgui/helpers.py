"""General helper functions used throughout the package."""
import functools
import os
from typing import List


def flatten(list2d: List[List]) -> List:
    """
    Accepts a 2D list and flattens it into a 1D list.

    :param list2d: Matrix to flatten
    :returns: list is ordered how the list is visually seen in 1D
    """
    return functools.reduce(lambda x, y: x+y, list2d)


def clean_str_list(str_list: List[str]) -> List[str]:
    """
    Removes invisible characters from a list of strings.

    :param str_list: list of strings
    :returns: list of strings without whitespace characters
    """
    return list(map(lambda s: s.rstrip("\n\r\t"), str_list))


def list_cast(str_list: List[str], cast_type: type) -> List:
    """
    Converts a list of strings to the given type.

    :param str_list: list of strings
    :param cast_type: type to cast the strings to
    :returns: list of values of the cast type
    :raises ValueError: if list cannot be cast to the specified time
    """
    str_list = clean_str_list(str_list)
    return list(map(lambda x: cast_type(x), str_list))


def is_unique(test_list: List) -> bool:
    """Checks if test_list is all unique values.

    :param test_list: list of objects to test for uniqueness
    :returns: whether or not the elements of the test_list are unique.
    """
    seen = set()
    return not any(i in seen or seen.add(i) for i in test_list)


def get_file_name(file_str: str) -> str:
    """
    Returns the name of a file removing the file path and file extension.

    :param file_str: file path file named.file extension
    :return: file name
    """
    return os.path.splitext(os.path.split(file_str)[1])[0]


def average(elements: List[List[List[float]]]) -> List[List[float]]:
    """
    Converts a 3 dimensional array of floats into a 2 dimensional array by averaging the inner arrays.

    :param elements: Elements to convert
    :return: Elements with the inner lists averaged
    """
    for i, element_channel in enumerate(elements):
        for j, element in enumerate(element_channel):
            try:
                elements[i][j] = sum(element) / len(element)
            except ZeroDivisionError:
                elements[i][j] = 0
    return elements


def make_length(values: List, length: int) -> List:
    """
    Force the values list to be of length, length.

    :param values: list to resize
    :param length: required length of the list
    :return: list of length, length
    """
    values = values[:length]
    values += [0] * (length - len(values))
    return values


