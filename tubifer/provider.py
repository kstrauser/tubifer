"""Data provider operations"""

import copy
import json
import logging

import pkg_resources

LOG = logging.getLogger(__name__)


def providers():
    """Return a list of available provider names."""
    return [name for name in pkg_resources.resource_listdir(__name__, 'data')
            if not name.startswith('_')]


def load(name):
    """Load the named provider's JSON file from the package and return it."""

    provider_data = pkg_resources.resource_string(__name__, 'data/{}'.format(name))
    return json.loads(provider_data.decode('utf-8'))


def overlay(under, over):
    """Recursively copy over onto under.

    If a key in over has the value None, then that key will be deleted
    from the result.

    If a key is in both over and under, both values must have the same
    type.
    """

    result = copy.deepcopy(under)
    for key, value in over.items():
        if value is None:
            try:
                del result[key]
            except KeyError:
                pass
            continue

        if key not in result:
            result[key] = value
            continue

        if type(result[key]) != type(value):  # pylint: disable=unidiomatic-typecheck
            raise ValueError("Can't replace {!r} with {!r}".format(result[key], value))

        if isinstance(value, dict):
            result[key] = overlay(result[key], value)
        else:
            result[key] = value

    return result


def get_geo_types(dataset, state=None, city=None):
    """Get the state and city's plan type information from a dataset."""

    inherit = dataset['types']

    if state is None:
        return dataset['types']

    try:
        state_data = dataset['state'][state]
    except KeyError:
        LOG.debug('State %s is not in %s. Using top-level data.',
                  state, dataset['name'])
        return inherit

    if state_data is None:
        LOG.debug('%s is not available in %s', dataset['name'], state)
        return None

    inherit = overlay(inherit, state_data)

    if city is None:
        return inherit

    try:
        city_data = state_data['city'][city]
    except KeyError:
        LOG.debug('City %s, %s is not in %s. Using state data.',
                  city, state, dataset['name'])
        return inherit

    if city_data is None:
        LOG.debug('%s is not available in %s, %s', dataset['name'], city, state)
        return None

    inherit = overlay(inherit, city_data)
    return inherit
