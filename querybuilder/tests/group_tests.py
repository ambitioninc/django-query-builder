from querybuilder.fields import CountField
from querybuilder.query import Query
from querybuilder.tests.query_tests import QueryTestCase, get_comparison_str


class GroupByTest(QueryTestCase):

    def test_group_by_id(self):
        query = Query().from_table(
            table='test_table',
            fields=[{
                'num': CountField('id')
            }]
        ).group_by(
            field='id'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.id) AS "num" FROM test_table GROUP BY id'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_group_by_table_id(self):
        query = Query().from_table(
            table='test_table',
            fields=[{
                'num': CountField('id')
            }]
        ).group_by(
            field='id',
            table='test_table',
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.id) AS "num" FROM test_table GROUP BY test_table.id'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_group_by_many_table_id(self):
        query = Query().from_table(
            table='test_table',
            fields=[{
                'num': CountField('id')
            }]
        ).group_by(
            field='id',
            table='test_table',
        ).group_by(
            field='id2',
            table='test_table',
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.id) AS "num" FROM test_table GROUP BY test_table.id, test_table.id2'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
