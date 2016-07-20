import json
import pkg_resources
import re

import click

DIGITS = re.compile(r'([0-9]+)')


def lower_str_or_int(value):
    return int(value) if value.isdigit() else value.lower()


def natural_sort_key(value):
    # http://stackoverflow.com/questions/11150239/python-natural-sorting
    return [lower_str_or_int(c) for c in DIGITS.split(value)]


def natural_sorted(*args, **kwargs):
    return sorted(*args, key=natural_sort_key, **kwargs)


class Indenter:
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


def show_providers(parent, providers, provider_name=None, **kwargs):
    """Show one or more providers"""

    indent = Indenter(parent)

    names = natural_sorted(providers)
    if provider_name is not None:
        if provider_name not in providers:
            indent('Provider name {!r} must be one of {}'.format(provider_name, names))
            return
        names = [provider_name]

    for name in names:
        print()
        indent('Provider: {}'.format(name))
        show_provider(indent, providers[name], **kwargs)


def show_provider(parent, provider, type_name=None, **kwargs):
    """Show a provider and one or more of its plan types"""

    indent = Indenter(parent)

    names = natural_sorted(provider)
    if type_name is not None:
        if type_name not in names:
            indent('Type name {!r} must be one of {}'.format(type_name, names))
            return
        names = [type_name]

    for name in names:
        print()
        indent('Type: {}'.format(name))
        show_type(parent, provider[name], **kwargs)


def show_type(parent, type, plan_name=None, **kwargs):
    """Show a plan type and one or more of its plans"""

    indent = Indenter(parent)

    names = natural_sorted(type['plans'])
    if plan_name is not None:
        if plan_name not in names:
            indent('Plan name {!r} must be one of {}'.format(plan_name, names))
            return
        names = [plan_name]

    print()
    indent('Max Mbps: {}'.format(type['maxMbps']))
    if type['sources']:
        indent('Sources:')
        for name in natural_sorted(type['sources']):
            Indenter(indent)('{}: {}'.format(name, type['sources'][name]))

    for name in names:
        print()
        indent('Plan: {}'.format(name))
        show_plan(indent, type['plans'][name], max_mbps=type['maxMbps'], **kwargs)


def show_plan(parent, plan, option_name=None, **kwargs):
    """Show a plan and one or more of its options"""

    indent = Indenter(parent)

    names = natural_sorted(plan['options'])
    if option_name is not None:
        if option_name not in names:
            indent('Option name {!r} must be one of {}'.format(option_name, names))
            return
        names = [option_name]

    for name in names:
        print()
        indent('Option: {}'.format(name))
        show_option(indent, plan['options'][name], **kwargs)


def show_option(parent, option, max_mbps=None, gb=None):
    """Show an option and its price / time calculations"""

    indent = Indenter(parent)

    price = option['price']
    indent('Base price: ${}/month'.format(price))
    if gb is not None:
        if gb > option['capgb']:
            price += option['overagePerGb'] * (gb - option['capgb'])
        indent('Extended price: ${}/month'.format(price))

    if max_mbps is not None and option['capgb'] is not None:
        usage_hours = option['capgb'] * 1024 * 1024 * 1024 / (max_mbps * 1000 * 1000 / 8) / 3600
        indent('Usage hours: {:.1f}'.format(usage_hours))


@click.command()
@click.argument('provider', required=False)
@click.argument('type', required=False)
@click.argument('plan', required=False)
@click.argument('option_name', required=False)
@click.option('--gb', help='Expected data usage in GB', type=int)
def show_data_prices(provider, type, plan, option_name, gb):

    provider_data = pkg_resources.resource_string(__name__, 'data/providers.json')
    dataset = json.loads(provider_data.decode('utf-8'))

    show_providers(None, dataset, provider_name=provider, type_name=type, plan_name=plan,
                   option_name=option_name, gb=gb)
