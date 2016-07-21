"""Calculate and display ISP data plan prices"""

import click

from . import provider
from .common import DEFAULTS, natural_sorted
from .handlers import Display


def defaulted(dataset, names):
    """Return a list of (key, value) with applied defaults, in order of names."""

    try:
        defaults = dataset['_defaults']
    except KeyError:
        return [(name, dataset[name]) for name in names]

    return [(name, provider.overlay(defaults, dataset[name]))
            for name in names if name != DEFAULTS]


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
        handler.type_callback('Unavailable in this location')
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
