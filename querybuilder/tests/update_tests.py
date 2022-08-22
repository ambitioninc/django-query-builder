import json

from django import VERSION
from django.test.utils import override_settings
from django_dynamic_fixture import G

from querybuilder.logger import Logger
from querybuilder.query import Query
from querybuilder.tests.models import Account, Order, MetricRecord
from querybuilder.tests.query_tests import QueryTestCase


@override_settings(DEBUG=True)
class TestUpdate(QueryTestCase):

    def setUp(self):
        self.logger = Logger()
        self.logger.start_logging()

        # Starting on Django 4, the id field adds ::integer automatically
        # self.integer_cast_string = ''
        # if (VERSION[0] == 4 and VERSION[1] >= 1) or VERSION[0] >= 5:
        #     self.integer_cast_string = '::integer'

    def test_update_single_row(self):
        query = Query().from_table(
            table=Account,
            fields=[
                'id',
                'user_id',
                'first_name',
                'last_name'
            ]
        )

        rows = [
            [1, 1, 'Test\'s', '"User"']
        ]

        sql, sql_params = query.get_update_sql(rows)

        self.assertEqual(
            sql,
            (
                'UPDATE querybuilder_tests_account '
                'SET user_id = new_values.user_id, '
                'first_name = new_values.first_name, '
                'last_name = new_values.last_name '
                f'FROM (VALUES (%s, %s::integer, %s::varchar(64), %s::varchar(64))) '
                'AS new_values (id, user_id, first_name, last_name) '
                'WHERE querybuilder_tests_account.id = new_values.id'
            )
        )

        self.assertEqual(sql_params[0], 1)
        self.assertEqual(sql_params[1], 1)
        self.assertEqual(sql_params[2], 'Test\'s')
        self.assertEqual(sql_params[3], '"User"')

        query.update(rows)
        sql = self.logger.get_log()[0]['sql']
        self.assertEqual(
            sql,
            (
                "UPDATE querybuilder_tests_account "
                "SET user_id = new_values.user_id, "
                "first_name = new_values.first_name, "
                "last_name = new_values.last_name "
                f"FROM (VALUES (1, 1::integer, "
                "'Test''s'::varchar(64), '\"User\"'::varchar(64))) "
                "AS new_values (id, user_id, first_name, last_name) "
                "WHERE querybuilder_tests_account.id = new_values.id"
            )
        )

    def test_update_json_field(self):
        MetricRecord.objects.create(id=10, data={'default1': 'd1'})
        MetricRecord.objects.create(id=11, data={'default2': 'd2'})

        query = Query().from_table(
            table=MetricRecord,
            fields=[
                'id',
                'data',
            ]
        )

        # Manually prep the values for db query
        rows = [
            [10, json.dumps({'first': '111'})],
            [11, json.dumps({'second': '222'})],
        ]

        query.update(rows)

        records = list(MetricRecord.objects.order_by('id'))
        self.assertEqual(records[0].data, {'first': '111'})
        self.assertEqual(records[1].data, {'second': '222'})

    def test_update_multiple_rows(self):
        query = Query().from_table(
            table=Account,
            fields=[
                'id',
                'user_id',
                'first_name',
                'last_name'
            ]
        )

        rows = [
            [1, 1, 'Test', 'User'],
            [2, 2, 'Test2', 'User2']
        ]

        sql, sql_params = query.get_update_sql(rows)

        self.assertEqual(
            sql,
            (
                'UPDATE querybuilder_tests_account '
                'SET user_id = new_values.user_id, '
                'first_name = new_values.first_name, '
                'last_name = new_values.last_name '
                f'FROM (VALUES (%s, %s::integer, %s::varchar(64), %s::varchar(64)), '
                '(%s, %s, %s, %s)) '
                'AS new_values (id, user_id, first_name, last_name) '
                'WHERE querybuilder_tests_account.id = new_values.id'
            )
        )
        self.assertEqual(sql_params[0], 1)
        self.assertEqual(sql_params[1], 1)
        self.assertEqual(sql_params[2], 'Test')
        self.assertEqual(sql_params[3], 'User')
        self.assertEqual(sql_params[4], 2)
        self.assertEqual(sql_params[5], 2)
        self.assertEqual(sql_params[6], 'Test2')
        self.assertEqual(sql_params[7], 'User2')

        query.update(rows)
        sql = self.logger.get_log()[0]['sql']
        self.assertEqual(
            sql,
            (
                "UPDATE querybuilder_tests_account "
                "SET user_id = new_values.user_id, "
                "first_name = new_values.first_name, "
                "last_name = new_values.last_name "
                f"FROM (VALUES (1, 1::integer, 'Test'::varchar(64), 'User'::varchar(64)), "
                "(2, 2, 'Test2', 'User2')) "
                "AS new_values (id, user_id, first_name, last_name) "
                "WHERE querybuilder_tests_account.id = new_values.id"
            )
        )

    def test_update_null_numbers(self):
        """
        Verifies that null values can be bulk updated
        """
        order1 = G(Order, revenue=10)
        order2 = G(Order, revenue=20)
        order3 = G(Order, revenue=30)
        query = Query().from_table(table=Order, fields=['id', 'revenue'])

        logger = Logger()
        logger.start_logging()
        rows = [[order1.id, None], [order2.id, None], [order3.id, 3000]]
        query.update(rows)

        orders = list(Order.objects.order_by('id'))
        self.assertIsNone(orders[0].revenue)
        self.assertIsNone(orders[1].revenue)
        self.assertEqual(3000, orders[2].revenue)

    def test_update_all_nulls(self):
        """
        Verifies that the sql is modified when all values for a field are null. For whatever reason,
        postgres doesn't handle this the same when all values are null
        """
        order1 = G(Order, revenue=10, margin=5)
        order2 = G(Order, revenue=20, margin=10)
        order3 = G(Order, revenue=30, margin=15)
        query = Query().from_table(table=Order, fields=['id', 'revenue', 'margin'])

        logger = Logger()
        logger.start_logging()
        rows = [[order1.id, None, 50], [order2.id, None, 100], [order3.id, None, 150]]
        query.update(rows)

        orders = list(Order.objects.order_by('id'))
        self.assertIsNone(orders[0].revenue)
        self.assertIsNone(orders[1].revenue)
        self.assertIsNone(orders[2].revenue)
