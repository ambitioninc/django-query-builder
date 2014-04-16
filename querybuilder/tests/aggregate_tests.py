from querybuilder.fields import CountField, AvgField, MaxField, MinField, StdDevField, SumField, VarianceField
from querybuilder.query import Query
from querybuilder.tests.models import Order, User
from querybuilder.tests.query_tests import QueryTestCase, get_comparison_str


class AggregateTest(QueryTestCase):
    def test_count_id(self):
        query = Query().from_table(
            table='test_table',
            fields=[
                CountField('id')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.id) AS id_count FROM test_table'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_count_all(self):
        query = Query().from_table(
            table='test_table',
            fields=[
                CountField('*')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.*) AS all_count FROM test_table'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_count_id_alias(self):
        query = Query().from_table(
            table='test_table',
            fields=[{
                'num': CountField('id')
            }]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.id) AS num FROM test_table'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_avg(self):
        query = Query().from_table(
            table=Order,
            fields=[
                AvgField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT AVG(tests_order.margin) AS margin_avg FROM tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_max(self):
        query = Query().from_table(
            table=Order,
            fields=[
                MaxField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT MAX(tests_order.margin) AS margin_max FROM tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_min(self):
        query = Query().from_table(
            table=Order,
            fields=[
                MinField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT MIN(tests_order.margin) AS margin_min FROM tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_stddev(self):
        query = Query().from_table(
            table=Order,
            fields=[
                StdDevField('margin'),
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT STDDEV(tests_order.margin) AS margin_stddev FROM tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_sum(self):
        query = Query().from_table(
            table=Order,
            fields=[
                SumField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT SUM(tests_order.margin) AS margin_sum FROM tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_variance(self):
        query = Query().from_table(
            table=Order,
            fields=[
                VarianceField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT VARIANCE(tests_order.margin) AS margin_variance FROM tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_count(self):
        query = Query().from_table(
            User
        )
        received = query.count()
        expected = len(User.objects.all())
        self.assertEqual(
            received,
            expected,
            'Expected {0} but received {1}'.format(
                expected,
                received
            )
        )

    def test_max(self):
        query = Query().from_table(
            User
        )
        received = query.max('id')
        expected = User.objects.all().order_by('-id')[0].id
        self.assertEqual(
            received,
            expected,
            'Expected {0} but received {1}'.format(
                expected,
                received
            )
        )

    def test_min(self):
        query = Query().from_table(
            User
        )
        received = query.min('id')
        expected = User.objects.all().order_by('id')[0].id
        self.assertEqual(
            received,
            expected,
            'Expected {0} but received {1}'.format(
                expected,
                received
            )
        )

    def test_sum(self):
        query = Query().from_table(
            Order
        )
        received = query.sum('margin')
        expected = sum([order.margin for order in Order.objects.all()])
        self.assertEqual(
            received,
            expected,
            'Expected {0} but received {1}'.format(
                expected,
                received
            )
        )

    def test_average(self):
        query = Query().from_table(
            Order
        )
        received = query.avg('margin')
        items = [order.margin for order in Order.objects.all()]
        average = 0
        if len(items):
            average = sum(items) / len(items)
        expected = average
        self.assertEqual(
            received,
            expected,
            'Expected {0} but received {1}'.format(
                expected,
                received
            )
        )
