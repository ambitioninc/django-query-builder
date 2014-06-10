from django_dynamic_fixture import G
from querybuilder.logger import Logger
from querybuilder.query import Query
from querybuilder.tests.models import Account, Order
from querybuilder.tests.query_tests import QueryTestCase


class TestUpdate(QueryTestCase):

    def setUp(self):
        self.logger = Logger()
        self.logger.start_logging()

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

        self.assertEqual(sql, 'UPDATE tests_account SET user_id = new_values.user_id, first_name = new_values.first_name, last_name = new_values.last_name FROM (VALUES (%s, %s, %s, %s)) AS new_values (id, user_id, first_name, last_name) WHERE tests_account.id = new_values.id')
        self.assertEqual(sql_params[0], 1)
        self.assertEqual(sql_params[1], 1)
        self.assertEqual(sql_params[2], 'Test\'s')
        self.assertEqual(sql_params[3], '"User"')

        query.update(rows)
        sql = self.logger.get_log()[0]['sql']
        self.assertEqual(sql, "UPDATE tests_account SET user_id = new_values.user_id, first_name = new_values.first_name, last_name = new_values.last_name FROM (VALUES (1, 1, 'Test''s', '\"User\"')) AS new_values (id, user_id, first_name, last_name) WHERE tests_account.id = new_values.id")

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

        self.assertEqual(sql, 'UPDATE tests_account SET user_id = new_values.user_id, first_name = new_values.first_name, last_name = new_values.last_name FROM (VALUES (%s, %s, %s, %s), (%s, %s, %s, %s)) AS new_values (id, user_id, first_name, last_name) WHERE tests_account.id = new_values.id')
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
        self.assertEqual(sql, "UPDATE tests_account SET user_id = new_values.user_id, first_name = new_values.first_name, last_name = new_values.last_name FROM (VALUES (1, 1, 'Test', 'User'), (2, 2, 'Test2', 'User2')) AS new_values (id, user_id, first_name, last_name) WHERE tests_account.id = new_values.id")

    def test_update_null_number(self):
        """
        Verifies that null values can be bulk updated
        """
        order1 = G(Order, revenue=10)
        order2 = G(Order, revenue=20)
        query = Query().from_table(table=Order, fields=['id', 'revenue'])
        rows = [[order1.id, 5.5], [order2.id, None]]
        query.update(rows)

        orders = list(Order.objects.order_by('id'))
        self.assertEqual(5.5, orders[0].revenue)
        self.assertIsNone(orders[1].revenue)
