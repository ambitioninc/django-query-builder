from django.test import TestCase
from querybuilder.fields import Field
from querybuilder.query import Query
from querybuilder.tables import TableFactory, SimpleTable, ModelTable, QueryTable
from querybuilder.tests.models import Account


class TableFactoryTest(TestCase):
    """
    Tests the functionality of the table factory
    """
    def test_str(self):
        """
        Verifies that a table is generated for a str object and that kwargs are passed
        """
        table = TableFactory('test', fields=['one'])
        self.assertIsInstance(table, SimpleTable)
        self.assertEqual(1, len(table.fields))

    def test_unicode(self):
        """
        Verifies that a table is generated for a unicode object and that kwargs are passed
        """
        table = TableFactory(u'test', fields=['one'])
        self.assertIsInstance(table, SimpleTable)
        self.assertEqual(1, len(table.fields))

    def test_model(self):
        """
        Verifies that a table is generated from a model and that kwargs are passed
        """
        table = TableFactory(Account, fields=['one'])
        self.assertIsInstance(table, ModelTable)
        self.assertEqual(1, len(table.fields))

    def test_query(self):
        """
        Verifies that a table is generated from a query object and that kwargs are passed
        """
        table = TableFactory(Query().from_table('test'), fields=['one'])
        self.assertIsInstance(table, QueryTable)
        self.assertEqual(1, len(table.fields))

    def test_table(self):
        """
        Verifies that kwargs are properly set from another table object and that kwargs are passed
        """
        test_table = TableFactory('test', alias='test_alias')
        table = TableFactory(test_table, fields=['one'])
        self.assertIsInstance(table, SimpleTable)
        self.assertEqual(1, len(table.fields))
        self.assertEqual('test_alias', table.alias)

    def test_none(self):
        """
        Verifies that None is returned for unsupported data
        """
        table = TableFactory(5, fields=['one'])
        self.assertIsNone(table)

    def test_dict(self):
        """
        Verifies that dict alias data is properly extracted
        """
        table = TableFactory({'test_alias': Account}, fields=['one'])
        self.assertIsInstance(table, ModelTable)
        self.assertEqual(1, len(table.fields))
        self.assertEqual('test_alias', table.alias)


class TableTest(TestCase):
    """
    Tests functionality of the Table class
    """
    def test_add_fields_str(self):
        """
        Tests calling add_fields with a str object
        """
        table = TableFactory('test')
        fields = table.add_fields('one')
        self.assertEqual(1, len(fields))
        self.assertIsNotNone(fields[0])
        self.assertEqual('test.one', fields[0].get_identifier())

    def test_add_fields_unicode(self):
        """
        Tests calling add_fields with a unicode object
        """
        table = TableFactory('test')
        fields = table.add_fields(u'one')
        self.assertEqual(1, len(fields))
        self.assertIsNotNone(fields[0])
        self.assertEqual('test.one', fields[0].get_identifier())

    def test_add_fields_tuple(self):
        """
        Tests calling add_fields with a tuple of names
        """
        table = TableFactory('test')
        fields = table.add_fields(('one', 'two'))
        self.assertEqual(2, len(fields))
        self.assertIsNotNone(fields[0])
        self.assertIsNotNone(fields[1])
        self.assertEqual('test.one', fields[0].get_identifier())
        self.assertEqual('test.two', fields[1].get_identifier())

    def test_add_fields_list(self):
        """
        Tests calling add_fields with a list of names
        """
        table = TableFactory('test')
        fields = table.add_fields(['one', 'two'])
        self.assertEqual(2, len(fields))
        self.assertIsNotNone(fields[0])
        self.assertIsNotNone(fields[1])
        self.assertEqual('test.one', fields[0].get_identifier())
        self.assertEqual('test.two', fields[1].get_identifier())

    def test_add_existing_field(self):
        """
        Tests the add field function to make sure an existing field is ignored
        """
        table = TableFactory('test')
        field = table.add_field('one')
        self.assertIsInstance(field, Field)
        field = table.add_field('one')
        self.assertIsNone(field)

    def test_remove_field(self):
        """
        Verifies that a field is properly removed
        """
        table = TableFactory('test')
        table.add_fields(['one', 'two'])
        self.assertEqual(2, len(table.fields))
        field = table.remove_field('one')
        self.assertIsNotNone(field)
        self.assertEqual('test.one', field.get_identifier())
        self.assertEqual(1, len(table.fields))
        field = table.remove_field('one')
        self.assertIsNone(field)

    def test_get_field_identifiers(self):
        """
        Makes sure correct identifiers are returned for all fields
        """
        table = TableFactory('test')
        table.add_fields(['one', 'two'])
        self.assertEqual(['test.one', 'test.two'], table.get_field_identifiers())

    def test_find_field(self):
        """
        Verifies that the correct field is returned
        """
        table = TableFactory('test')
        table.add_fields(['one', 'two'])
        field = table.find_field('one')
        self.assertEqual('test.one', field.get_identifier())
        self.assertEqual(table.fields[0], field)

    def test_find_field_alias(self):
        """
        Verifies that the correct field is returned when passing an alias
        """
        table = TableFactory('test')
        table.add_fields(['one', {'my_alias': 'two'}])
        field = table.find_field(alias='my_alias')
        self.assertEqual('my_alias', field.get_identifier())
        self.assertEqual(table.fields[1], field)

    def test_find_field_none(self):
        """
        Verifies that None is returned when no field is found
        """
        table = TableFactory('test')
        table.add_fields(['one', 'two'])
        field = table.find_field('fake_field')
        self.assertIsNone(field)


class QueryTableTest(TestCase):
    """
    Tests the QueryTable object
    """
    def test_get_from_name(self):
        """
        Verifies that the correct name is generated
        """
        inner_query = Query().from_table(Account)
        query = Query().from_table(inner_query)
        self.assertEqual(
            '(SELECT querybuilder_tests_account.* FROM querybuilder_tests_account)',
            query.tables[0].get_from_name()
        )
