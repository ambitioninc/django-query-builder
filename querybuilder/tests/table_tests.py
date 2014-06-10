from django.test import TestCase
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
