from querybuilder.helpers import value_for_keypath, set_value_for_keypath
from querybuilder.tests.base import QuerybuilderTestCase


class HelperTest(QuerybuilderTestCase):
    """
    Tests the helper functions
    """

    def test_value_for_keypath(self):
        """
        Tests all cases of value_for_keypath
        """
        self.assertEqual({}, value_for_keypath({}, ''))
        self.assertIsNone(value_for_keypath({}, 'fake'))
        self.assertIsNone(value_for_keypath({}, 'fake.path'))
        self.assertEqual({'fruit': 'apple'}, value_for_keypath({'fruit': 'apple'}, ''))
        self.assertEqual('apple', value_for_keypath({'fruit': 'apple'}, 'fruit'))
        self.assertIsNone(value_for_keypath({'fruit': 'apple'}, 'fake'))
        self.assertIsNone(value_for_keypath({'fruit': 'apple'}, 'fake.path'))
        self.assertEqual(
            {'fruits': {'apple': 'red', 'banana': 'yellow'}},
            value_for_keypath({'fruits': {'apple': 'red', 'banana': 'yellow'}}, '')
        )
        self.assertEqual(
            {'apple': 'red', 'banana': 'yellow'},
            value_for_keypath({'fruits': {'apple': 'red', 'banana': 'yellow'}}, 'fruits')
        )
        self.assertEqual('red', value_for_keypath({'fruits': {'apple': 'red', 'banana': 'yellow'}}, 'fruits.apple'))
        self.assertEqual(
            {'color': 'red', 'taste': 'good'},
            value_for_keypath({'fruits': {'apple': {'color': 'red', 'taste': 'good'}}}, 'fruits.apple')
        )
        self.assertEqual(
            'red',
            value_for_keypath({'fruits': {'apple': {'color': 'red', 'taste': 'good'}}}, 'fruits.apple.color')
        )
        self.assertEqual(
            'good',
            value_for_keypath({'fruits': {'apple': {'color': 'red', 'taste': 'good'}}}, 'fruits.apple.taste')
        )

    def test_set_value_for_keypath(self):
        """
        Tests all cases of set_value_for_keypath
        """
        self.assertIsNone(set_value_for_keypath({}, '', None))
        self.assertIsNone(set_value_for_keypath({}, '', 'test value'))
        self.assertIsNone(set_value_for_keypath({'fruit': 'apple'}, '', None))
        self.assertIsNone(set_value_for_keypath({'fruit': 'apple'}, '', 'test value'))
        self.assertEqual({'fruit': None}, set_value_for_keypath({'fruit': 'apple'}, 'fruit', None))
        self.assertEqual({'fruit': 'test value'}, set_value_for_keypath({'fruit': 'apple'}, 'fruit', 'test value'))
        self.assertIsNone(set_value_for_keypath({'fruit': 'apple'}, 'fake', None))
        self.assertIsNone(set_value_for_keypath({'fruit': 'apple'}, 'fake', 'test value'))
        self.assertIsNone(set_value_for_keypath({'fruit': 'apple'}, 'fake.fake', 'test value'))
        self.assertEqual(
            {'fruit': {'apple': 'green'}},
            set_value_for_keypath({'fruit': {'apple': 'red'}}, 'fruit.apple', 'green')
        )
        self.assertEqual(
            {'fruit': {'apple': None}},
            set_value_for_keypath({'fruit': {'apple': 'red'}}, 'fruit.apple', None)
        )
        self.assertIsNone(set_value_for_keypath({'fruit': {'apple': {'color': 'red'}}}, 'fruit.apple.fake', 'green'))
        self.assertEqual(
            {'fruit': {'apple': {'color': 'green'}}},
            set_value_for_keypath({'fruit': {'apple': {'color': 'red'}}}, 'fruit.apple.color', 'green')
        )
        self.assertEqual(
            {'fruit': {'apple': {'color': {'puppies': {'count': 10, 'breed': 'boxers'}}}}},
            set_value_for_keypath(
                {'fruit': {'apple': {'color': 'red'}}},
                'fruit.apple.color',
                {'puppies': {'count': 10, 'breed': 'boxers'}}
            )
        )
        self.assertEqual(
            {'fruit': {'apple': {'color': 'red', 'animals': {'puppies': {'count': 10, 'breed': 'boxers'}}}}},
            set_value_for_keypath(
                {'fruit': {'apple': {'color': 'red'}}},
                'fruit.apple.animals',
                {'puppies': {'count': 10, 'breed': 'boxers'}},
                create_if_needed=True
            )
        )
