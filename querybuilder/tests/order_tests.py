from querybuilder.query import Query
from querybuilder.tests.query_tests import QueryTestCase, get_comparison_str


class OrderByTest(QueryTestCase):
    def test_order_by_single_asc(self):
        query = Query().from_table(
            table='test_table'
        ).order_by(
            'field_one'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table ORDER BY field_one ASC'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_order_by_many_asc(self):
        query = Query().from_table(
            table='test_table'
        ).order_by(
            'field_one'
        ).order_by(
            'field_two'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table ORDER BY field_one ASC, field_two ASC'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_order_by_single_desc(self):
        query = Query().from_table(
            table='test_table'
        ).order_by(
            '-field_one'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table ORDER BY field_one DESC'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_order_by_many_desc(self):
        query = Query().from_table(
            table='test_table'
        ).order_by(
            '-field_one'
        ).order_by(
            '-field_two'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table ORDER BY field_one DESC, field_two DESC'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
