"""Code used project-wide"""

import re

DEFAULTS = '_defaults'
DIGITS = re.compile(r'([0-9]+)')


def lower_str_or_int(value):
    """Return the value as an int if possible, otherwise as a string"""
    return int(value) if value.isdigit() else value.lower()


def natural_sort_key(value):
    """Convet a value into a tuple suitable for natural ordering"""
    # http://stackoverflow.com/questions/11150239/python-natural-sorting
    return [lower_str_or_int(c) for c in DIGITS.split(value)]


def natural_sorted(iterable, *args, **kwargs):
    """Like sorted, but naturally ordered"""
    return sorted([_ for _ in iterable if _ != DEFAULTS], *args, key=natural_sort_key, **kwargs)
