import functools
import os


def flatten(list2d):
    """Accepts a 2D list and flattens it into a 1D list. Returned list is ordered how the list is visually seen."""
    return functools.reduce(lambda x, y: x+y, list2d)


def to_ext(file, ext):
    """Accepts a file name and returns the file name with a csv extension."""
    return os.path.splitext(file)[0] + "." + ext


def clean_str_list(str_list):
    """Removes invisible characters from a list of strings, and returns a list of strings."""
    return list(map(lambda s: s.rstrip("\n\r\t"), str_list))


def list_cast(str_list, cast_type):
    """
    Converts a list of strings to the given type. This function does not catch the potential
    ValueError that is thrown from an unsuccessful cast.
    """
    str_list = clean_str_list(str_list)
    return list(map(lambda x: cast_type(x), str_list))


def is_unique(test_list):
    """Returns whether or not the elements of the test_list are unique."""
    seen = set()
    return not any(i in seen or seen.add(i) for i in test_list)
