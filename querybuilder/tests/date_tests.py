from querybuilder.fields import Year, Month, Hour, Minute, Second, NoneTime, AllTime
from querybuilder.query import Query
from querybuilder.tests.models import Order
from querybuilder.tests.query_tests import QueryTestCase, get_comparison_str


class DateTest(QueryTestCase):
    def test_year(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Year('time')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT CAST(EXTRACT(year FROM querybuilder_tests_order.time) AS INT) AS "time__year" FROM querybuilder_tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_year_auto(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Year('time', auto=True)
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT CAST(EXTRACT(year FROM querybuilder_tests_order.time) AS INT) AS "time__year", '
            'CAST(EXTRACT(epoch FROM date_trunc(\'year\', querybuilder_tests_order.time)) AS INT) AS "time__epoch" '
            'FROM querybuilder_tests_order '
            'GROUP BY time__year, time__epoch '
            'ORDER BY time__epoch ASC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_year_auto_desc(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Year('time', auto=True, desc=True)
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT CAST(EXTRACT(year FROM querybuilder_tests_order.time) AS INT) AS "time__year", '
            'CAST(EXTRACT(epoch FROM date_trunc(\'year\', querybuilder_tests_order.time)) AS INT) AS "time__epoch" '
            'FROM querybuilder_tests_order '
            'GROUP BY time__year, time__epoch '
            'ORDER BY time__epoch DESC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_month_auto(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Month('time', auto=True)
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT CAST(EXTRACT(year FROM querybuilder_tests_order.time) AS INT) AS "time__year", '
            'CAST(EXTRACT(month FROM querybuilder_tests_order.time) AS INT) AS "time__month", '
            'CAST(EXTRACT(epoch FROM date_trunc(\'month\', querybuilder_tests_order.time)) AS INT) AS "time__epoch" '
            'FROM querybuilder_tests_order '
            'GROUP BY time__year, time__month, time__epoch '
            'ORDER BY time__epoch ASC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_hour_auto(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Hour('time', auto=True)
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT CAST(EXTRACT(year FROM querybuilder_tests_order.time) AS INT) AS "time__year", '
            'CAST(EXTRACT(month FROM querybuilder_tests_order.time) AS INT) AS "time__month", '
            'CAST(EXTRACT(day FROM querybuilder_tests_order.time) AS INT) AS "time__day", '
            'CAST(EXTRACT(hour FROM querybuilder_tests_order.time) AS INT) AS "time__hour", '
            'CAST(EXTRACT(epoch FROM date_trunc(\'hour\', querybuilder_tests_order.time)) AS INT) AS "time__epoch" '
            'FROM querybuilder_tests_order '
            'GROUP BY time__year, time__month, time__day, time__hour, time__epoch '
            'ORDER BY time__epoch ASC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_minute_auto(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Minute('time', auto=True)
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT CAST(EXTRACT(year FROM querybuilder_tests_order.time) AS INT) AS "time__year", '
            'CAST(EXTRACT(month FROM querybuilder_tests_order.time) AS INT) AS "time__month", '
            'CAST(EXTRACT(day FROM querybuilder_tests_order.time) AS INT) AS "time__day", '
            'CAST(EXTRACT(hour FROM querybuilder_tests_order.time) AS INT) AS "time__hour", '
            'CAST(EXTRACT(minute FROM querybuilder_tests_order.time) AS INT) AS "time__minute", '
            'CAST(EXTRACT(epoch FROM date_trunc(\'minute\', querybuilder_tests_order.time)) AS INT) AS "time__epoch" '
            'FROM querybuilder_tests_order '
            'GROUP BY time__year, time__month, time__day, time__hour, time__minute, time__epoch '
            'ORDER BY time__epoch ASC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_second_auto(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Second('time', auto=True)
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT CAST(EXTRACT(year FROM querybuilder_tests_order.time) AS INT) AS "time__year", '
            'CAST(EXTRACT(month FROM querybuilder_tests_order.time) AS INT) AS "time__month", '
            'CAST(EXTRACT(day FROM querybuilder_tests_order.time) AS INT) AS "time__day", '
            'CAST(EXTRACT(hour FROM querybuilder_tests_order.time) AS INT) AS "time__hour", '
            'CAST(EXTRACT(minute FROM querybuilder_tests_order.time) AS INT) AS "time__minute", '
            'CAST(EXTRACT(second FROM querybuilder_tests_order.time) AS INT) AS "time__second", '
            'CAST(EXTRACT(epoch FROM date_trunc(\'second\', querybuilder_tests_order.time)) AS INT) AS "time__epoch" '
            'FROM querybuilder_tests_order '
            'GROUP BY time__year, time__month, time__day, time__hour, time__minute, time__second, time__epoch '
            'ORDER BY time__epoch ASC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_group_none(self):
        query = Query().from_table(
            table=Order,
            fields=[
                NoneTime('time')
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT CAST(EXTRACT(epoch FROM querybuilder_tests_order.time) AS INT) AS "time__epoch" '
            'FROM querybuilder_tests_order '
            'GROUP BY time__epoch '
            'ORDER BY time__epoch ASC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_group_all(self):
        query = Query().from_table(
            table=Order,
            fields=[
                AllTime('time')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT CAST(0 AS INT) AS "time__epoch" FROM querybuilder_tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
