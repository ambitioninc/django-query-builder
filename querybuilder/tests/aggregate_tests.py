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
        expected_query = 'SELECT COUNT(test_table.id) AS "id_count" FROM test_table'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_count_distinct(self):
        query = Query().from_table(
            table='test_table',
            fields=[
                CountField('name', distinct=True)
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(DISTINCT test_table.name) AS "name_count" FROM test_table'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_count_all(self):
        query = Query().from_table(
            table='test_table',
            fields=[
                CountField('*')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.*) AS "all_count" FROM test_table'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_count_id_alias(self):
        query = Query().from_table(
            table='test_table',
            fields=[{
                'num': CountField('id')
            }]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.id) AS "num" FROM test_table'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_avg(self):
        query = Query().from_table(
            table=Order,
            fields=[
                AvgField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT AVG(querybuilder_tests_order.margin) AS "margin_avg" FROM querybuilder_tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_max_field(self):
        """
        Verifies that the MAX function is generated correctly in a query
        """
        query = Query().from_table(
            table=Order,
            fields=[
                MaxField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT MAX(querybuilder_tests_order.margin) AS "margin_max" FROM querybuilder_tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_min_field(self):
        """
        Verifies that the MinField generates correct MIN sql
        """
        query = Query().from_table(
            table=Order,
            fields=[
                MinField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT MIN(querybuilder_tests_order.margin) AS "margin_min" FROM querybuilder_tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_stddev(self):
        query = Query().from_table(
            table=Order,
            fields=[
                StdDevField('margin'),
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT STDDEV(querybuilder_tests_order.margin) AS "margin_stddev" FROM querybuilder_tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_sum_field(self):
        """
        Tests that the SumField generates correct sql
        """
        query = Query().from_table(
            table=Order,
            fields=[
                SumField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT SUM(querybuilder_tests_order.margin) AS "margin_sum" FROM querybuilder_tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_variance(self):
        query = Query().from_table(
            table=Order,
            fields=[
                VarianceField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT VARIANCE(querybuilder_tests_order.margin) AS "margin_variance" FROM querybuilder_tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_count(self):
        query = Query().from_table(
            User,
            ['one', 'two']
        ).order_by('id')
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
        self.assertEqual(query.get_count_query().get_sql(), 'SELECT COUNT(querybuilder_tests_user.*) AS "all_count" FROM querybuilder_tests_user')

        # Make sure the copy didn't modify the original
        self.assertEqual(len(query.tables[0].fields), 2)
        self.assertEqual(len(query.sorters), 1)

    def test_max(self):
        """
        Tests that the max() function properly gets the max value from the query
        """
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
        """
        Tests the min() function
        """
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
        """
        Tests the sum() function on a field
        """
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
        """
        Tests the avg function
        """
        query = Query().from_table(
            Order
        )
        received = query.avg('margin')
        items = [order.margin for order in Order.objects.all()]
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
