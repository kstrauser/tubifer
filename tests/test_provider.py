# pylint: disable=missing-docstring

import logging
import unittest

from tubifer import provider


class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.dataset = provider.load('_test.json')

    def test_simple_traversal(self):
        types = provider.get_geo_types(self.dataset)

        self.assertEqual(types['wired']['plans']['Family Plan']['options']['best']['maxMbps'], 100)

    def test_traverse_undefined_state(self):
        with self.assertLogs(level=logging.DEBUG) as logger:
            types = provider.get_geo_types(self.dataset, 'AA')

        self.assertEqual(types['wired']['plans']['Family Plan']['options']['best']['maxMbps'], 100)
        self.assertEqual(logger.output, [
            "DEBUG:tubifer.provider:State AA is not in Joe's Cable. Using top-level data."
        ])

    def test_traverse_unavailable_state(self):
        with self.assertLogs(level=logging.DEBUG) as logger:
            types = provider.get_geo_types(self.dataset, 'ZZ')

        self.assertIsNone(types)
        self.assertEqual(logger.output, [
            "DEBUG:tubifer.provider:Joe's Cable is not available in ZZ"
        ])

    def test_traverse_undefined_city(self):
        with self.assertLogs(level=logging.DEBUG) as logger:
            types = provider.get_geo_types(self.dataset, 'CA', 'BBBBB')

        self.assertEqual(types['wired']['plans']['Family Plan']['options']['best']['maxMbps'], 100)
        self.assertEqual(logger.output, [
            "DEBUG:tubifer.provider:City BBBBB, CA is not in Joe's Cable. Using state data."
        ])

    def test_traverse_unavailable_city(self):
        with self.assertLogs(level=logging.DEBUG) as logger:
            types = provider.get_geo_types(self.dataset, 'CA', 'Deadzone')

        self.assertIsNone(types)
        self.assertEqual(logger.output, [
            "DEBUG:tubifer.provider:Joe's Cable is not available in Deadzone, CA"
        ])

    def test_traverse_overriden_city(self):
        types = provider.get_geo_types(self.dataset, 'CA', 'Futura')

        self.assertNotIn('good', types['wired']['plans']['Family Plan']['options'])
        self.assertEqual(types['wired']['plans']['Family Plan']['options']['better']['price'], 40)
        self.assertNotIn('capGb', types['wired']['plans']['Family Plan']['options']['best'])

    def test_overlay_simple(self):
        self.assertEqual(
            provider.overlay({'foo': 1}, {'bar': 2}),
            {'foo': 1, 'bar': 2}
        )

    def test_overlay_with_removal(self):
        under = {'foo': 1, 'bar': 2}
        self.assertEqual(
            provider.overlay(under, {'bar': None}),
            {'foo': 1}
        )
        self.assertEqual(under, {'foo': 1, 'bar': 2})

    def test_overlay_wrong_types(self):
        with self.assertRaises(ValueError) as exc:
            provider.overlay({'foo': 1}, {'foo': 'bar'})

        self.assertEqual(exc.exception.args[0], "Can't replace 1 with 'bar'")

    def test_overlay_recursive(self):
        self.assertEqual(
            provider.overlay({
                'foo': {
                    'bar': {
                        'baz': 123,
                        'qux': 456,
                    },
                    'spam': {
                        'a': 789,
                        'b': 543,
                    },
                },
            },
            {
                'foo': {
                    'bar': {
                        'qux': None,
                    },
                    'spam': {
                        'a': 210,
                    },
                },
            }),
            {
                'foo': {
                    'bar': {
                        'baz': 123,
                    },
                    'spam': {
                        'a': 210,
                        'b': 543,
                    },
                },
            }
        )
