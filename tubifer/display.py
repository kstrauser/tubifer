"""Calculate and display ISP data plan prices"""

import re

import click

from . import provider

DEFAULTS = '_defaults'
DIGITS = re.compile(r'([0-9]+)')


class Indenter:  # pylint: disable=too-few-public-methods
    """Indented printer.

    By default, prints unindented. If initialized with another
    Indented instance, prints one level more indented than its parent.

    >>> i = Indenter()
    >>> i('foo')
    foo
    >>> j = Indenter(i)
    >>> j('bar')
      bar
    """

    def __init__(self, parent=None):
        if parent is None:
            self.level = 0
        else:
            self.level = parent.level + 1

    def __call__(self, *args, **kwargs):
        if self.level:
            print(' ' + '  ' * (self.level - 1), *args, **kwargs)
        else:
            print(*args, **kwargs)


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


def defaulted(dataset, names):
    """Return a list of (key, value) with applied defaults, in order of names."""

    try:
        defaults = dataset['_defaults']
    except KeyError:
        return [(name, dataset[name]) for name in names]

    return [(name, provider.overlay(defaults, dataset[name]))
            for name in names if name != DEFAULTS]


def visit(provider_name, type_name, plan_name, option_name, state, city, usage_gb):
    pass


def select(value, choices, description, callback=None):
    if value is None:
        return natural_sorted(choices)

    if value not in choices:
        if callback:
            callback('{} name {!r} must be one of {}'.format(
                description, value, natural_sorted(choices)))
        return []

    return [value]


def show_providers(parent, providers, provider_name=None, **kwargs):
    """Show one or more providers"""

    indent = Indenter(parent)

    names = select(provider_name, providers, 'Provider', indent)

    for key, value in defaulted(providers, names):
        print()
        indent('Provider: {}'.format(key))
        show_provider(indent, value, **kwargs)


def show_provider(parent, provider_data, state=None, city=None, type_name=None, **kwargs):
    """Show a provider and one or more of its plan types"""

    indent = Indenter(parent)

    types = provider.get_geo_types(provider_data, state, city)
    if types is None:
        indent('Unavailable in this location')
        return

    names = select(type_name, types, 'Type', indent)

    for key, value in defaulted(types, names):
        print()
        indent('Type: {}'.format(key))
        show_type(indent, value, **kwargs)


def show_type(parent, type_, plan_name=None, **kwargs):
    """Show a plan type and one or more of its plans"""

    indent = Indenter(parent)

    names = select(plan_name, type_['plans'], 'Plan', indent)

    if names and type_['sources']:
        indent('Sources:')
        for name in natural_sorted(type_['sources']):
            Indenter(indent)('{}: {}'.format(name, type_['sources'][name]))

    for key, value in defaulted(type_['plans'], names):
        print()
        indent('Plan: {}'.format(key))
        show_plan(indent, value, **kwargs)


def show_plan(parent, plan, option_name=None, **kwargs):
    """Show a plan and one or more of its options"""

    indent = Indenter(parent)

    indent('Description: {}'.format(plan['description']))

    names = select(option_name, plan['options'], 'Option', indent)

    for key, value in defaulted(plan['options'], names):
        print()
        indent('Option: {}'.format(key))
        show_option(indent, value, **kwargs)


def show_option(parent, option, usage_gb=None):
    """Show an option and its price / time calculations"""

    indent = Indenter(parent)

    price = option['price']
    cap_gb = option.get('capGB')

    indent('Base price: ${}/month'.format(price))
    if usage_gb is not None:
        if cap_gb is not None and usage_gb > cap_gb:
            price += option['overagePerGB'] * (usage_gb - cap_gb)
        indent('Extended price: ${}/month'.format(price))

    if cap_gb is not None:
        indent("Cap GB: {}".format(cap_gb))

    max_mbps = option.get('maxMbps')
    if max_mbps is not None:
        indent("Max Mbps: {}".format(max_mbps))
        if cap_gb is not None:
            usage_hours = cap_gb * 1024 * 1024 * 1024 / (max_mbps * 1000 * 1000 / 8) / 3600
            indent('Usage hours: {:.1f}'.format(usage_hours))


@click.command()
@click.argument('provider_name', required=False)
@click.argument('type_name', required=False)
@click.argument('plan_name', required=False)
@click.argument('option_name', required=False)
@click.option('--state', help='State to show plans for')
@click.option('--city', help='City to show prices for')
@click.option('--usage-gb', help='Expected data usage in GB', type=int)
def show_data_prices(**kwargs):
    """Show ISP data plan prices on one or provider options.

    By default, show-data-prices displays all defined options for all
    providers. Results may be increasingly narrowed by giving
    provider, type, plan, and option names.

    If --usage-gb is given, plan options will display the calculated
    price for using that amount of data in a month.

    "Usage hours" are the number of hours each month you can use a
    plan option at full speed without exceeding its data cap.

    """

    dataset = {}
    for name in provider.providers():
        provider_data = provider.load(name)
        dataset[provider_data['name']] = provider_data

    show_providers(None, dataset, **kwargs)
