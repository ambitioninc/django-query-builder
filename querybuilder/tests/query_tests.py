import datetime

from django.db import connections
from django.test import TestCase
from django_dynamic_fixture import G
import six

from querybuilder.fields import CountField
from querybuilder.query import Query
from querybuilder.tests.models import User, Account, Order


def get_comparison_str(item1, item2):
    return 'Items are not equal.\nGot:\n{0}\nExpected:\n{1}'.format(item1, item2)


class QueryConstructorTests(TestCase):
    databases = ['default', 'mock-second-database']

    def test_init_with_connection(self):
        """
        Test passing in a connection object works
        """
        conn = connections['default']
        self.assertIn(
            type(Query(conn).from_table('auth_user').count()), six.integer_types
        )

    def test_init_no_connection(self):
        """
        Test passing in no object works
        """
        self.assertIn(
            type(Query().from_table('auth_user').count()), six.integer_types
        )

    def test_get_cursor_for_connection(self):

        query = Query(connections['default'])
        self.assertEqual(query.get_cursor().db, connections['default'])

        query2 = Query(connections['mock-second-database'])
        self.assertEqual(query2.get_cursor().db, connections['mock-second-database'])

        # uses default if no connection is specified
        query3 = Query()
        self.assertEqual(query3.get_cursor().db, connections['default'])


class QueryTestCase(TestCase):

    def setUp(self):
        super(QueryTestCase, self).setUp()
        user1 = G(User, id=1, email='wes.okes@gmail.com')
        user2 = G(User, id=2, email='two+wes.okes@gmail.com')
        account1 = G(Account, id=1, user=user1, first_name='Wes', last_name='Okes')
        account2 = G(Account, id=2, user=user2, first_name='Wesley', last_name='Okes')

        G(
            Order, account=account1, revenue=200, margin=100, margin_percent=0.5, time=datetime.datetime(2012, 10, 19))
        G(
            Order, account=account1, revenue=100, margin=25, margin_percent=0.25, time=datetime.datetime(2012, 10, 19))
        G(
            Order, account=account2, revenue=500, margin=100, margin_percent=0.2, time=datetime.datetime(2012, 10, 19))
        G(
            Order, account=account2, revenue=1000, margin=600, margin_percent=0.6, time=datetime.datetime(2012, 10, 19))


# TODO: add tests for selecting fields like {'alias': 'agg() + agg()'}


class QueryTest(QueryTestCase):
    def test_find_table(self):
        query = Query().from_table(
            table=Account
        ).from_table(
            table={
                'account2': Account
            }
        ).join(Order)

        table = query.find_table(Account)
        self.assertIsNotNone(table, 'Table not found')

        result = table.get_identifier()
        expected = 'querybuilder_tests_account'
        self.assertEqual(result, expected, get_comparison_str(result, expected))

    def test_find_table_alias(self):
        query = Query().from_table(
            table=Account
        ).from_table(
            table={
                'account2': Account
            }
        ).join(Order)

        table = query.find_table('account2')
        self.assertIsNotNone(table, 'Table not found')

        result = table.get_identifier()
        expected = 'account2'
        self.assertEqual(result, expected, get_comparison_str(result, expected))

    def test_find_join_table(self):
        query = Query().from_table(
            table=Account
        ).from_table(
            table={
                'account2': Account
            }
        ).join(Order)

        table = query.find_table(Order)
        self.assertIsNotNone(table, 'Table not found')

        result = table.get_identifier()
        expected = 'querybuilder_tests_order'
        self.assertEqual(result, expected, get_comparison_str(result, expected))

    def test_wrap(self):
        query = Query().from_table(
            Account
        ).wrap().wrap().wrap().wrap()
        query_str = query.get_sql()
        expected_query = (
            'WITH T0T0T0T0 AS (SELECT querybuilder_tests_account.* FROM querybuilder_tests_account), '
            'T0T0T0 AS (SELECT T0T0T0T0.* FROM T0T0T0T0), '
            'T0T0 AS (SELECT T0T0T0.* FROM T0T0T0), '
            'T0 AS (SELECT T0T0.* FROM T0T0) '
            'SELECT T0.* '
            'FROM T0'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_select_sql(self):
        sql = 'SELECT id FROM querybuilder_tests_account ORDER BY id LIMIT 1'
        rows = Query().select(sql=sql)
        received = rows[0]['id']
        expected = User.objects.all().order_by('id')[0].id
        self.assertEqual(
            received,
            expected,
            'Expected {0} but received {1}'.format(
                expected,
                received
            )
        )

    def test_select_sql_args(self):
        sql = 'SELECT id FROM querybuilder_tests_account WHERE id = %(my_id)s'
        sql_args = {
            'my_id': 2
        }
        rows = Query().select(sql=sql, sql_args=sql_args)
        received = rows[0]['id']
        expected = User.objects.all().filter(id=2)[0].id
        self.assertEqual(
            received,
            expected,
            'Expected {0} but received {1}'.format(
                expected,
                received
            )
        )

    def test_explain(self):
        sql = 'SELECT id FROM querybuilder_tests_account WHERE id = %(my_id)s'
        sql_args = {
            'my_id': 2
        }
        rows = Query().explain(sql=sql, sql_args=sql_args)
        self.assertTrue(len(rows) > 0, 'Explain did not return anything')


class TableTest(QueryTestCase):
    def test_find_field(self):
        query = Query().from_table(
            table=Account,
            extract_fields=True,
        ).from_table(
            table={
                'account2': Account
            },
            fields=[{
                'name': 'first_name'
            }]
        ).join(Order)

        table = query.tables[0]
        field = table.find_field('id')
        self.assertIsNotNone(field, 'Field not found')

        result = field.get_identifier()
        expected = 'querybuilder_tests_account.id'
        self.assertEqual(result, expected, get_comparison_str(result, expected))

    def test_find_field_alias(self):
        query = Query().from_table(
            table=Account,
            extract_fields=True,
        ).from_table(
            table={
                'account2': Account
            },
            fields=[{
                'name': 'first_name'
            }]
        ).join(Order)

        table = query.tables[1]
        field = table.find_field(alias='name')
        self.assertIsNotNone(field, 'Field not found')

        result = field.get_identifier()
        expected = 'name'
        self.assertEqual(result, expected, get_comparison_str(result, expected))
        result = field.name
        expected = 'first_name'
        self.assertEqual(result, expected, get_comparison_str(result, expected))


class FieldTest(QueryTestCase):
    def test_cast(self):
        query = Query().from_table(
            table=Account,
            fields=[
                CountField(
                    'id',
                    alias='count',
                    cast='float'
                )
            ]
        )

        query_str = query.get_sql()
        expected_query = (
            'SELECT CAST(COUNT(querybuilder_tests_account.id) AS FLOAT) AS "count" FROM querybuilder_tests_account'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

        received = query.select()[0]['count']
        expected = float(len(User.objects.all()))
        self.assertEqual(
            received,
            expected,
            'Expected {0} but received {1}'.format(
                expected,
                received
            )
        )
