from querybuilder.fields import (
    RankField, RowNumberField, DenseRankField, PercentRankField, CumeDistField, NTileField, LagField,
    LeadField, FirstValueField, LastValueField, NthValueField, NumStdDevField
)
from querybuilder.query import QueryWindow, Query
from querybuilder.tests.models import Order
from querybuilder.tests.query_tests import QueryTestCase, get_comparison_str


class QueryWindowTest(QueryTestCase):
    def test_query_window(self):
        query_window = QueryWindow()
        query_str = query_window.get_sql()
        expected_query = 'OVER ()'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_query_window_partition(self):
        query_window = QueryWindow().partition_by('field_one')
        query_str = query_window.get_sql()
        expected_query = 'OVER (PARTITION BY field_one)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_query_window_order(self):
        query_window = QueryWindow().order_by('field_one')
        query_str = query_window.get_sql()
        expected_query = 'OVER (ORDER BY field_one ASC)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_query_window_partition_order(self):
        query_window = QueryWindow().partition_by(
            'field_one'
        ).order_by(
            'field_one'
        )
        query_str = query_window.get_sql()
        expected_query = 'OVER (PARTITION BY field_one ORDER BY field_one ASC)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_query_window_partition_order_many(self):
        query_window = QueryWindow().partition_by(
            'field_one'
        ).partition_by(
            'field_two'
        ).order_by(
            'field_one'
        ).order_by(
            '-field_two'
        )
        query_str = query_window.get_sql()
        expected_query = 'OVER (PARTITION BY field_one, field_two ORDER BY field_one ASC, field_two DESC)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))


class WindowFunctionTest(QueryTestCase):
    def test_rank_no_over(self):
        query = Query().from_table(
            table=Order,
            fields=[
                RankField()
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT RANK() AS "rank" FROM querybuilder_tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_rank_over(self):
        query = Query().from_table(
            table=Order,
            fields=[
                RankField(
                    over=QueryWindow()
                )
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT RANK() OVER () AS "rank" FROM querybuilder_tests_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_rank_over_order(self):
        query = Query().from_table(
            table=Order,
            fields=[
                'id',
                RankField(
                    over=QueryWindow().order_by(
                        'id'
                    )
                )
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.id, RANK() OVER (ORDER BY id ASC) AS "rank" FROM querybuilder_tests_order'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_rank_over_partition(self):
        query = Query().from_table(
            table=Order,
            fields=[
                'id',
                RankField(
                    over=QueryWindow().partition_by(
                        'account_id'
                    )
                )
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.id, RANK() OVER (PARTITION BY account_id) AS "rank" FROM '
            'querybuilder_tests_order'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_row_number(self):
        query = Query().from_table(
            table=Order,
            fields=[
                '*',
                RowNumberField(
                    over=QueryWindow().order_by(
                        '-margin'
                    )
                )
            ]
        ).order_by(
            'row_number'
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.*, '
            'ROW_NUMBER() OVER (ORDER BY margin DESC) AS "row_number" '
            'FROM querybuilder_tests_order '
            'ORDER BY row_number '
            'ASC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_rank(self):
        query = Query().from_table(
            table=Order,
            fields=[
                'id',
                RankField(
                    over=QueryWindow().partition_by(
                        'account_id'
                    ).order_by(
                        'id'
                    )
                )
            ]
        ).order_by(
            '-rank'
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.id, '
            'RANK() OVER (PARTITION BY account_id ORDER BY id ASC) AS "rank" '
            'FROM querybuilder_tests_order '
            'ORDER BY rank '
            'DESC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_dense_rank(self):
        query = Query().from_table(
            table=Order,
            fields=[
                '*',
                DenseRankField(
                    over=QueryWindow().order_by(
                        '-margin'
                    )
                )
            ]
        ).order_by(
            'dense_rank'
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.*, '
            'DENSE_RANK() OVER (ORDER BY margin DESC) AS "dense_rank" '
            'FROM querybuilder_tests_order '
            'ORDER BY dense_rank '
            'ASC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_rank_percent(self):
        query = Query().from_table(
            table=Order,
            fields=[
                '*',
                PercentRankField(
                    over=QueryWindow().order_by(
                        '-margin'
                    )
                )
            ]
        ).order_by(
            'percent_rank'
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.*, '
            'PERCENT_RANK() OVER (ORDER BY margin DESC) AS "percent_rank" '
            'FROM querybuilder_tests_order '
            'ORDER BY percent_rank '
            'ASC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_cume_dist(self):
        query = Query().from_table(
            table=Order,
            fields=[
                '*',
                CumeDistField(
                    over=QueryWindow().order_by(
                        '-margin'
                    )
                )
            ]
        ).order_by(
            'cume_dist'
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.*, '
            'CUME_DIST() OVER (ORDER BY margin DESC) AS "cume_dist" '
            'FROM querybuilder_tests_order '
            'ORDER BY cume_dist '
            'ASC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_ntile(self):
        query = Query().from_table(
            table=Order,
            fields=[
                '*',
                NTileField(
                    num_buckets=2,
                    over=QueryWindow().order_by(
                        '-margin'
                    )
                )
            ]
        ).order_by(
            'ntile'
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.*, '
            'NTILE(2) OVER (ORDER BY margin DESC) AS "ntile" '
            'FROM querybuilder_tests_order '
            'ORDER BY ntile '
            'ASC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_lag(self):
        query = Query().from_table(
            table=Order,
            fields=[
                '*',
                LagField(
                    'margin',
                    over=QueryWindow().order_by(
                        '-margin'
                    )
                )
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.*, '
            'LAG(querybuilder_tests_order.margin, 1) OVER (ORDER BY margin DESC) AS "margin_lag" '
            'FROM querybuilder_tests_order'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_lag_default(self):
        query = Query().from_table(
            table=Order,
            fields=[
                '*',
                LagField(
                    'margin',
                    default=0,
                    over=QueryWindow().order_by(
                        '-margin'
                    )
                )
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.*, '
            'LAG(querybuilder_tests_order.margin, 1, \'0\') OVER (ORDER BY margin DESC) AS "margin_lag" '
            'FROM querybuilder_tests_order'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_lead(self):
        query = Query().from_table(
            table=Order,
            fields=[
                '*',
                LeadField(
                    'margin',
                    over=QueryWindow().order_by(
                        '-margin'
                    )
                )
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.*, '
            'LEAD(querybuilder_tests_order.margin, 1) OVER (ORDER BY margin DESC) AS "margin_lead" '
            'FROM querybuilder_tests_order'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_first_value(self):
        query = Query().from_table(
            table=Order,
            fields=[
                '*',
                FirstValueField(
                    'margin',
                    over=QueryWindow().order_by(
                        '-margin'
                    )
                )
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.*, '
            'FIRST_VALUE(querybuilder_tests_order.margin) OVER (ORDER BY margin DESC) AS "margin_first_value" '
            'FROM querybuilder_tests_order'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_last_value(self):
        query = Query().from_table(
            table=Order,
            fields=[
                '*',
                LastValueField(
                    'margin',
                    over=QueryWindow().order_by(
                        'margin'
                    )
                )
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.*, '
            'LAST_VALUE(querybuilder_tests_order.margin) OVER (ORDER BY margin ASC) AS "margin_last_value" '
            'FROM querybuilder_tests_order'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_nth_value(self):
        query = Query().from_table(
            table=Order,
            fields=[
                '*',
                NthValueField(
                    'margin',
                    n=2,
                    over=QueryWindow().order_by(
                        '-margin'
                    )
                )
            ]
        )
        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.*, '
            'NTH_VALUE(querybuilder_tests_order.margin, 2) OVER (ORDER BY margin DESC) AS "margin_nth_value" '
            'FROM querybuilder_tests_order'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_num_stddev(self):
        query = Query().from_table(
            table=Order,
            fields=[
                '*',
                NumStdDevField(
                    'margin',
                    over=QueryWindow()
                )
            ]
        ).order_by(
            '-margin_num_stddev'
        )

        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.*, '
            '(CASE WHEN (STDDEV(querybuilder_tests_order.margin) OVER ()) <> 0 '
            'THEN ((querybuilder_tests_order.margin - ('
            'AVG(querybuilder_tests_order.margin) OVER ())) / (STDDEV(querybuilder_tests_order.margin) OVER ())) '
            'ELSE 0 '
            'END) '
            'AS "margin_num_stddev" '
            'FROM querybuilder_tests_order '
            'ORDER BY margin_num_stddev '
            'DESC'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
