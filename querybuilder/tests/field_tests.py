import datetime
from fleming import unix_time, floor

from querybuilder.fields import SimpleField, LagDifferenceField, LeadDifferenceField, AllTime, SumField, Week
from querybuilder.query import Query, QueryWindow
from querybuilder.tests.models import Order
from querybuilder.tests.query_tests import QueryTestCase


class FieldTest(QueryTestCase):
    def test_cast(self):
        """
        Tests that the cast sql is generated and that the resulting value is of that type
        """
        query = Query().from_table(
            table=Order,
            fields=[SimpleField(field='revenue', cast='INT')]
        ).order_by('revenue').limit(1)
        expected_query = 'SELECT CAST(tests_order.revenue AS INT) FROM tests_order ORDER BY revenue ASC LIMIT 1'
        self.assertEqual(expected_query, query.get_sql())
        rows = query.select()
        self.assertEqual(1, len(rows))
        self.assertEqual(type(rows[0]['revenue']), int)

    def test_get_alias(self):
        """
        Tests the different cases of getting the alias of a field
        """
        field = SimpleField(field='revenue')
        query = Query().from_table(table=Order, fields=[field])
        expected_query = 'SELECT tests_order.revenue FROM tests_order'
        self.assertEqual(expected_query, query.get_sql())

        field.auto_alias = 'my_auto_alias'
        query = Query().from_table(table=Order, fields=[field])
        expected_query = 'SELECT tests_order.revenue AS "my_auto_alias" FROM tests_order'
        self.assertEqual(expected_query, query.get_sql())

        field.alias = 'my_alias'
        query = Query().from_table(table=Order, fields=[field])
        expected_query = 'SELECT tests_order.revenue AS "my_alias" FROM tests_order'
        self.assertEqual(expected_query, query.get_sql())

        query = Query().from_table(
            table=Order,
            fields=[field],
            prefix_fields=True,
            field_prefix='my_field_prefix',
        )
        expected_query = 'SELECT tests_order.revenue AS "my_field_prefix__my_alias" FROM tests_order'
        self.assertEqual(expected_query, query.get_sql())

        field.alias = None
        field.auto_alias = None
        query = Query().from_table(
            table=Order,
            fields=[field],
            prefix_fields=True,
            field_prefix='my_field_prefix',
        )
        expected_query = 'SELECT tests_order.revenue AS "my_field_prefix__revenue" FROM tests_order'
        self.assertEqual(expected_query, query.get_sql())

    def lead_lag_difference_test(self):
        query = Query().from_table(
            table=Order,
            fields=[
                'margin',
                LagDifferenceField('margin', over=QueryWindow().order_by('-margin')),
                LeadDifferenceField('margin', over=QueryWindow().order_by('-margin')),
            ]
        )
        expected_query = (
            'SELECT tests_order.margin, '
            '((tests_order.margin) - (LAG(tests_order.margin, 1) '
            'OVER (ORDER BY margin DESC))) AS "margin_lag", '
            '((tests_order.margin) - (LEAD(tests_order.margin, 1) '
            'OVER (ORDER BY margin DESC))) AS "margin_lead" '
            'FROM tests_order'
        )
        self.assertEqual(expected_query, query.get_sql())
        rows = query.select()
        self.assertEqual(4, len(rows))
        self.assertEqual(None, rows[0]['margin_lag'])
        self.assertEqual(500.0, rows[0]['margin_lead'])
        self.assertEqual(-75.0, rows[3]['margin_lag'])
        self.assertEqual(None, rows[3]['margin_lead'])

    def date_part_field_test(self):
        """
        Tests the different options of DatePartField objects
        """
        # test with no cast
        query = Query().from_table(
            table=Order,
            fields=[
                AllTime('time'),
                SumField('margin')
            ]
        )
        expected_query = (
            'SELECT CAST(0 AS INT) AS "time__epoch", '
            'SUM(tests_order.margin) AS "margin_sum" '
            'FROM tests_order'
        )
        self.assertEqual(expected_query, query.get_sql())
        rows = query.select()
        self.assertEqual(1, len(rows))
        self.assertEqual(825.0, rows[0]['margin_sum'])
        self.assertEqual(0, rows[0]['time__epoch'])

    # def test_cast(self):
    #     """
    #     Verified a value is casted to a float
    #     """
    #     query = Query().from_table(
    #         table=Order,
    #         fields=[
    #             AllTime('time', cast='FLOAT'),
    #             SumField('margin')
    #         ]
    #     )
    #     expected_query = (
    #         'SELECT CAST(0 AS FLOAT) AS time__epoch, '
    #         'SUM(tests_order.margin) AS margin_sum '
    #         'FROM tests_order'
    #     )
    #     self.assertEqual(expected_query, query.get_sql())
    #     rows = query.select()
    #     self.assertEqual(1, len(rows))
    #     self.assertEqual(825.0, rows[0]['margin_sum'])
    #     self.assertEqual(float, type(rows[0]['time__epoch']))
    #     self.assertEqual(0.0, rows[0]['time__epoch'])

    def test_week_grouping(self):
        """
        Verifies that the week grouping query and result is correct
        """
        query = Query().from_table(
            table=Order,
            fields=[
                Week('time', auto=True),
                SumField('margin')
            ]
        )
        expected_query = (
            'SELECT CAST(EXTRACT(year FROM tests_order.time) AS INT) AS "time__year", '
            'CAST(EXTRACT(week FROM tests_order.time) AS INT) AS "time__week", '
            'CAST(EXTRACT(epoch FROM date_trunc(\'week\', tests_order.time)) AS INT) AS "time__epoch", '
            'SUM(tests_order.margin) AS "margin_sum" '
            'FROM tests_order '
            'GROUP BY time__year, time__week, time__epoch '
            'ORDER BY time__epoch ASC'
        )
        self.assertEqual(expected_query, query.get_sql())
        rows = query.select()
        self.assertEqual(1, len(rows))
        week_dt = datetime.datetime(2012, 10, 19)
        week_unix_time = unix_time(floor(week_dt, week=1))
        self.assertEqual(825.0, rows[0]['margin_sum'])
        self.assertEqual(week_unix_time, rows[0]['time__epoch'])
        self.assertEqual(2012, rows[0]['time__year'])
        self.assertEqual(42, rows[0]['time__week'])
