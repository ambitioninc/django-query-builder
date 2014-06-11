from querybuilder.query import Query
from querybuilder.tests.query_tests import QueryTestCase, get_comparison_str


class LimitTest(QueryTestCase):
    def test_limit(self):
        query = Query().from_table(
            table='test_table'
        ).limit(10)
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table LIMIT 10'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_offset(self):
        query = Query().from_table(
            table='test_table'
        ).limit(
            offset=10
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table OFFSET 10'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_limit_with_offset(self):
        query = Query().from_table(
            table='test_table'
        ).limit(
            limit=5,
            offset=20
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table LIMIT 5 OFFSET 20'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
