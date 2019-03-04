from django.db.models import Q
from django.db.models.sql import OR
from querybuilder.query import Query
from querybuilder.tests.models import Account
from querybuilder.tests.query_tests import QueryTestCase, get_comparison_str


class WhereTest(QueryTestCase):

    def test_where_eq(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            one='two'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_named_arg(self):
        query = Query().from_table(
            table='test_table'
        ).where(
            one='two'
        )

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_many_named_arg(self):
        query = Query().from_table(
            table='test_table'
        ).where(
            one='two',
            three='four'
        )

        query_str = query.get_sql()
        expected_queries = [
            'SELECT test_table.* FROM test_table WHERE (three = %(A0)s AND one = %(A1)s)',
            'SELECT test_table.* FROM test_table WHERE (one = %(A0)s AND three = %(A1)s)'
        ]
        self.assertIn(query_str, expected_queries)

    def test_where_not_eq(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            one='two'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(one = %(A0)s)))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_eq_explicit(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            one__eq='two'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_not_eq_explicit(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            one__eq='two'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(one = %(A0)s)))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_gt(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            field_name__gt=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (field_name > %(A0)s)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_not_gt(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            field_name__gt=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(field_name > %(A0)s)))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_gte(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            field_name__gte=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (field_name >= %(A0)s)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_not_gte(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            field_name__gte=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(field_name >= %(A0)s)))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_lt(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            field_name__lt=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (field_name < %(A0)s)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_not_lt(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            field_name__lt=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(field_name < %(A0)s)))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_lte(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            field_name__lte=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (field_name <= %(A0)s)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_not_lte(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            field_name__lte=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(field_name <= %(A0)s)))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_in_single(self):
        query = Query().from_table(
            table=Account
        ).where(Q(
            id__in=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT querybuilder_tests_account.* FROM querybuilder_tests_account WHERE (id IN (%(A0)s))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_in_csv(self):
        query = Query().from_table(
            table=Account
        ).where(Q(
            id__in='10,11,12'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT querybuilder_tests_account.* FROM querybuilder_tests_account WHERE (id IN (%(A0)s,%(A1)s,%(A2)s))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_in_list(self):
        query = Query().from_table(
            table=Account
        ).where(Q(
            id__in=[10, 11, 12]
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT querybuilder_tests_account.* FROM querybuilder_tests_account WHERE (id IN (%(A0)s,%(A1)s,%(A2)s))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_contains(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            field_name__contains='some value'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (field_name LIKE %(A0)s)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
        self.assertEqual(query._where.args['A0'], '%some value%', 'Value is not correct')

    def test_where_icontains(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            field_name__icontains='some value'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (field_name ILIKE %(A0)s)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
        self.assertEqual(query._where.args['A0'], '%some value%', 'Value is not correct')

    def test_where_not_contains(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            field_name__contains='some value'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(field_name LIKE %(A0)s)))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
        self.assertEqual(query._where.args['A0'], '%some value%', 'Value is not correct')

    def test_where_not_icontains(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            field_name__icontains='some value'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(field_name ILIKE %(A0)s)))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
        self.assertEqual(query._where.args['A0'], '%some value%', 'Value is not correct')

    def test_where_startswith(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            field_name__startswith='some value'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (field_name LIKE %(A0)s)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
        self.assertEqual(query._where.args['A0'], 'some value%', 'Value is not correct')

    def test_where_not_startswith(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            field_name__startswith='some value'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(field_name LIKE %(A0)s)))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
        self.assertEqual(query._where.args['A0'], 'some value%', 'Value is not correct')

    def test_where_and(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            one='two'
        )).where(Q(
            three='four'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s AND three = %(A1)s)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_and_combined(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            one='two'
        ) & Q(
            three='four'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s AND three = %(A1)s)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_or(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            one='two'
        )).where(Q(
            three='four'
        ), OR)

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((one = %(A0)s) OR (three = %(A1)s))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_combined_or(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            one='two'
        ) | Q(
            three='four'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((one = %(A0)s OR three = %(A1)s))'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_and_with_combined_or(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            one='two'
        )).where(Q(
            three='four'
        ) | Q(
            five='six'
        ))

        query_str = query.get_sql()
        expected_query = (
            'SELECT test_table.* '
            'FROM test_table '
            'WHERE (one = %(A0)s AND (three = %(A1)s OR five = %(A2)s))'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_and_with_not_combined_or(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            one='two'
        )).where(~Q(
            three='four'
        ) | Q(
            five='six'
        ))

        query_str = query.get_sql()
        expected_query = (
            'SELECT test_table.* '
            'FROM test_table '
            'WHERE (one = %(A0)s AND ((NOT(three = %(A1)s)) OR five = %(A2)s))'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_where_complex(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            one=1
        )).where(Q(
            two__gt=2
        )).where(~Q(
            three__gte=3
        )).where(~Q(
            four__lt=4
        ), OR).where(Q(
            five__lte=5
        ), OR).where(Q(
            six__contains='six'
        )).where(~Q(
            seven__startswith='seven'
        )).where(Q(
            eight=8
        ) & Q(
            nine=9
        ) | Q(
            ten=10
        ) | ~Q(
            eleven=11
        ))

        query_str = query.get_sql()
        expected_query = ''.join([
            'SELECT test_table.* FROM test_table WHERE ',
            '(((one = %(A0)s AND two > %(A1)s AND (NOT(three >= %(A2)s))) OR (NOT(four < %(A3)s)) ',
            'OR five <= %(A4)s) AND (six LIKE %(A5)s) AND (NOT(seven LIKE %(A6)s)) AND ',
            '((eight = %(A7)s AND nine = %(A8)s) OR ten = %(A9)s OR (NOT(eleven = %(A10)s))))'
        ])
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
