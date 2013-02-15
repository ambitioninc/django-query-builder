import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_project.settings")
from django.db.models.sql import OR, AND
from django.db.models import Q, Count
from test_project.models import Account
from django.utils import unittest
from querybuilder.query import Query


class TestSelect(unittest.TestCase):

    def test_select_all_from_string(self):
        query = Query().from_table(
            table='test_table'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_select_all_from_string_alias(self):
        query = Query().from_table(
            table={
                'table_alias': 'test_table'
            }
        )
        query_str = query.get_sql()
        expected_query = 'SELECT table_alias.* FROM test_table AS table_alias'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_select_all_from_model(self):
        query = Query().from_table(
            table=Account
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_project_account.* FROM test_project_account'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_select_all_from_model_alias(self):
        query = Query().from_table(
            table={
                'table_alias': Account
            }
        )
        query_str = query.get_sql()
        expected_query = 'SELECT table_alias.* FROM test_project_account AS table_alias'
        self.assertEqual(query_str, expected_query, '{0}\n!=\n{1}'.format(query_str, expected_query))

    def test_select_fields_from_string(self):
        query = Query().from_table(
            table='test_table',
            fields=[
                'field_one',
                'field_two',
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.field_one, test_table.field_two FROM test_table'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_select_fields_from_string_alias(self):
        query = Query().from_table(
            table={
                'table_alias': 'test_table'
            },
            fields=[
                'field_one',
                'field_two',
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT table_alias.field_one, table_alias.field_two FROM test_table AS table_alias'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_select_fields_from_model(self):
        query = Query().from_table(
            table=Account,
            fields=[
                'field_one',
                'field_two',
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_project_account.field_one, test_project_account.field_two FROM test_project_account'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_select_fields_from_model_alias(self):
        query = Query().from_table(
            table={
                'table_alias': Account
            },
            fields=[
                'field_one',
                'field_two',
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT table_alias.field_one, table_alias.field_two FROM test_project_account AS table_alias'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_select_fields_alias_from_string(self):
        query = Query().from_table(
            table='test_table',
            fields=[{
                'field_alias_one': 'field_one'
            }, {
                'field_alias_two': 'field_two'
            }]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.field_one AS field_alias_one, test_table.field_two AS field_alias_two FROM test_table'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_select_fields_alias_from_string_alias(self):
        query = Query().from_table(
            table={
                'table_alias': 'test_table'
            },
            fields=[{
                'field_alias_one': 'field_one'
            }, {
                'field_alias_two': 'field_two'
            }]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT table_alias.field_one AS field_alias_one, table_alias.field_two AS field_alias_two FROM test_table AS table_alias'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_select_fields_alias_from_model(self):
        query = Query().from_table(
            table=Account,
            fields=[{
                'field_alias_one': 'field_one'
            }, {
                'field_alias_two': 'field_two'
            }]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_project_account.field_one AS field_alias_one, test_project_account.field_two AS field_alias_two FROM test_project_account'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_select_fields_alias_from_model_alias(self):
        query = Query().from_table(
            table={
                'table_alias': Account
            },
            fields=[{
                'field_alias_one': 'field_one'
            }, {
                'field_alias_two': 'field_two'
            }]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT table_alias.field_one AS field_alias_one, table_alias.field_two AS field_alias_two FROM test_project_account AS table_alias'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_select_fields_two_tables(self):
        query = Query().from_table(
            table=Account,
            fields=[
                'field_one',
                'field_two'
            ]
        ).from_table(
            table='second_table',
            fields=[
                'field_three',
                'field_four'
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_project_account.field_one, test_project_account.field_two, second_table.field_three, second_table.field_four FROM test_project_account, second_table'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_select_fields_two_tables_alias(self):
        query = Query().from_table(
            table={
                'table_one': Account
            },
            fields=[{
                'f1': 'field_one'
            }, {
                'f2': 'field_two'
            }]
        ).from_table(
            table={
                'table_two': 'second_table'
            },
            fields=[{
                'f3': 'field_three'
            },{
                'f4': 'field_four'
            }]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT table_one.field_one AS f1, table_one.field_two AS f2, table_two.field_three AS f3, table_two.field_four AS f4 FROM test_project_account AS table_one, second_table AS table_two'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_select_fields_same_two_tables(self):
        query = Query().from_table(
            table=Account,
            fields=[
                'field_one',
                'field_two'
            ]
        ).from_table(
            table=Account,
            fields=[
                'field_three',
                'field_four'
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_project_account.field_one, test_project_account.field_two, T0.field_three, T0.field_four FROM test_project_account, test_project_account AS T0'
        self.assertEqual(query_str, expected_query, '\n{0}\n!=\n{1}'.format(query_str, expected_query))


class TestJoins(unittest.TestCase):

    def test_join_str(self):
        query = Query().from_table(
            table='test_table'
        ).join(
            'other_table',
            fields=None,
            condition='other_table.test_id = test_table.id'
        )

        query_str = query.get_sql()
        print query_str
        expected_query = 'SELECT test_table.* FROM test_table JOIN other_table ON other_table.test_id = test_table.id'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

class TestWheres(unittest.TestCase):

    def test_where_eq(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            one='two'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s)'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_where_not_eq(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            one='two'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(one = %(A0)s)))'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_where_eq_explicit(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            one__eq='two'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s)'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_where_not_eq_explicit(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            one__eq='two'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(one = %(A0)s)))'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_where_gt(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            field_name__gt=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (field_name > %(A0)s)'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_where_not_gt(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            field_name__gt=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(field_name > %(A0)s)))'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_where_gte(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            field_name__gte=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (field_name >= %(A0)s)'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_where_not_gte(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            field_name__gte=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(field_name >= %(A0)s)))'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_where_lt(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            field_name__lt=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (field_name < %(A0)s)'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_where_not_lt(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            field_name__lt=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(field_name < %(A0)s)))'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_where_lte(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            field_name__lte=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (field_name <= %(A0)s)'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_where_not_lte(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            field_name__lte=10
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(field_name <= %(A0)s)))'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_where_contains(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            field_name__contains='some value'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (field_name LIKE %(A0)s)'
        self.assertEqual(query_str, expected_query, 'Queries did not match')
        self.assertEqual(query._where.args['A0'], '%some value%', 'Value is not correct')

    def test_where_not_contains(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            field_name__contains='some value'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(field_name LIKE %(A0)s)))'
        self.assertEqual(query_str, expected_query, 'Queries did not match')
        self.assertEqual(query._where.args['A0'], '%some value%', 'Value is not correct')

    def test_where_startswith(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            field_name__startswith='some value'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (field_name LIKE %(A0)s)'
        self.assertEqual(query_str, expected_query, 'Queries did not match')
        self.assertEqual(query._where.args['A0'], 'some value%', 'Value is not correct')

    def test_where_not_startswith(self):
        query = Query().from_table(
            table='test_table'
        ).where(~Q(
            field_name__startswith='some value'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE ((NOT(field_name LIKE %(A0)s)))'
        self.assertEqual(query_str, expected_query, 'Queries did not match')
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
        self.assertEqual(query_str, expected_query, 'Queries did not match')

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
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_where_or(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            one='two'
        )).where(Q(
            three='four'
        ), OR)

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s OR three = %(A1)s)'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

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
        self.assertEqual(query_str, expected_query, 'Queries did not match')

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
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s AND (three = %(A1)s OR five = %(A2)s))'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

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
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s AND ((NOT(three = %(A1)s)) OR five = %(A2)s))'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

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
            '(((one = %(A0)s AND two > %(A1)s AND (NOT(three >= %(A2)s))) OR ((NOT(four < %(A3)s))) ',
            'OR five <= %(A4)s) AND (six LIKE %(A5)s) AND (NOT(seven LIKE %(A6)s)) AND ',
            '((eight = %(A7)s AND nine = %(A8)s) OR ten = %(A9)s OR (NOT(eleven = %(A10)s))))'
        ])
        self.assertEqual(query_str, expected_query, 'Queries did not match')


class TestGroupBy(unittest.TestCase):

    def test_count_id(self):
        query = Query().from_table(
            table='test_table',
            fields=[
                Count('id')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.id) AS count_id FROM test_table'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_count_all(self):
        query = Query().from_table(
            table='test_table',
            fields=[
                Count('*')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.*) AS count_all FROM test_table'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_count_id_alias(self):
        query = Query().from_table(
            table='test_table',
            fields=[{
                'num': Count('id')
            }]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.id) AS num FROM test_table'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_group_by_id(self):
        query = Query().from_table(
            table='test_table',
            fields=[{
                'num': Count('id')
            }]
        ).group_by(
            field='id'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.id) AS num FROM test_table GROUP BY id'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_group_by_table_id(self):
        query = Query().from_table(
            table='test_table',
            fields=[{
                'num': Count('id')
            }]
        ).group_by(
            field='id',
            table='test_table',
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.id) AS num FROM test_table GROUP BY test_table.id'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_group_by_many_table_id(self):
        query = Query().from_table(
            table='test_table',
            fields=[{
                'num': Count('id')
            }]
        ).group_by(
            field='id',
            table='test_table',
        ).group_by(
            field='id2',
            table='test_table',
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.id) AS num FROM test_table GROUP BY test_table.id, test_table.id2'
        self.assertEqual(query_str, expected_query, 'Queries did not match')


class TestOrderBy(unittest.TestCase):

    def test_order_by_single_asc(self):
        query = Query().from_table(
            table='test_table'
        ).order_by(
            'field_one'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table ORDER BY field_one ASC'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

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
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_order_by_single_desc(self):
        query = Query().from_table(
            table='test_table'
        ).order_by(
            '-field_one'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table ORDER BY field_one DESC'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

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
        self.assertEqual(query_str, expected_query, 'Queries did not match')


class TestLimit(unittest.TestCase):

    def test_limit(self):
        query = Query().from_table(
            table='test_table'
        ).limit(10)
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table LIMIT 10'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_offset(self):
        query = Query().from_table(
            table='test_table'
        ).limit(
            offset=10
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table OFFSET 10'
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_limit_with_offset(self):
        query = Query().from_table(
            table='test_table'
        ).limit(
            limit=5,
            offset=20
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table LIMIT 5 OFFSET 20'
        self.assertEqual(query_str, expected_query, 'Queries did not match')
