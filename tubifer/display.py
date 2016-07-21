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


class Display:
    provider_callback = Indenter()
    type_callback = Indenter(provider_callback)
    plan_callback = Indenter(type_callback)
    option_callback = Indenter(plan_callback)

    def visit_provider(self, name, value):  # pylint: disable=unused-argument
        """Show a provider's details"""

        print()
        self.provider_callback('Provider: {}'.format(name))

    def visit_type(self, name, type_):
        """Show a type's details"""

        child_indent = Indenter(self.type_callback)
        grandchild_indent = Indenter(child_indent)

        print()
        self.type_callback('Type: {}'.format(name))

        if type_['sources']:
            child_indent('Sources:')
            for name in natural_sorted(type_['sources']):
                grandchild_indent('{}: {}'.format(name, type_['sources'][name]))

    def visit_plan(self, name, plan):
        """Show a plan's details"""

        child_indent = Indenter(self.plan_callback)

        print()
        self.plan_callback('Plan: {}'.format(name))
        child_indent('Description: {}'.format(plan['description']))

    def visit_option(self, name, option, usage_gb):
        """Show an option's details and its price / time calculations"""

        child_indent = Indenter(self.option_callback)

        print()
        self.option_callback('Option: {}'.format(name))

        price = option['price']
        cap_gb = option.get('capGB')

        child_indent('Base price: ${}/month'.format(price))
        if usage_gb is not None:
            if cap_gb is not None and usage_gb > cap_gb:
                price += option['overagePerGB'] * (usage_gb - cap_gb)
            child_indent('Extended price: ${}/month'.format(price))

        if cap_gb is not None:
            child_indent("Cap GB: {}".format(cap_gb))

        max_mbps = option.get('maxMbps')
        if max_mbps is not None:
            child_indent("Max Mbps: {}".format(max_mbps))
            if cap_gb is not None:
                usage_hours = cap_gb * 1024 * 1024 * 1024 / (max_mbps * 1000 * 1000 / 8) / 3600
                child_indent('Usage hours: {:.1f}'.format(usage_hours))


def select(value, choices, description, callback=None):
    """Return a list of the relevent values in choices"""

    if value is None:
        return natural_sorted(choices)

    if value not in choices:
        if callback:
            callback('Error: {} name {!r} must be one of {}'.format(
                description, value, natural_sorted(choices)))
        return []

    return [value]


def visit_providers(handler, providers, provider_name=None, **kwargs):
    """Interate across all defined providers"""

    names = select(provider_name, providers, 'Provider', handler.provider_callback)

    for key, value in defaulted(providers, names):
        visit_provider(handler, key, value, **kwargs)


def visit_provider(  # pylint: disable=too-many-arguments
        handler, name, provider_data, state=None, city=None, type_name=None, **kwargs):
    """Iterate across a provider's types"""

    handler.visit_provider(name, provider_data)

    types = provider.get_geo_types(provider_data, state, city)
    if types is None:
        Indenter()('Unavailable in this location')
        return

    names = select(type_name, types, 'Type', handler.type_callback)

    for key, value in defaulted(types, names):
        visit_type(handler, key, value, **kwargs)


def visit_type(handler, name, type_, plan_name=None, **kwargs):
    """Iterate across a type's plans"""

    handler.visit_type(name, type_)

    names = select(plan_name, type_['plans'], 'Plan', handler.plan_callback)
    if not names:
        return

    for key, value in defaulted(type_['plans'], names):
        visit_plan(handler, key, value, **kwargs)


def visit_plan(handler, name, plan, option_name=None, **kwargs):
    """Iterate across a plans options"""

    handler.visit_plan(name, plan)

    names = select(option_name, plan['options'], 'Option', handler.option_callback)

    for key, value in defaulted(plan['options'], names):
        visit_option(handler, key, value, **kwargs)


def visit_option(handler, name, option, usage_gb=None):
    """Visit an option leaf node"""

    handler.visit_option(name, option, usage_gb)


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

    visit_providers(Display(), dataset, **kwargs)
