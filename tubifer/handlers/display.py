"""The Display handler renders nodes to stdout"""

from ..common import natural_sorted


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


class Display:
    """Handler that renders nodes to stdout"""

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
