from django.test import TestCase
from django.db.models.sql import OR
from django.db.models import Q
from querybuilder.fields import Year, Month, Hour, Minute, Second, NoneTime, AllTime, CountField, AvgField, VarianceField, SumField, StdDevField, MinField, MaxField
from querybuilder.logger import Logger, LogManager
from test_project.models import Account, Order, User
from querybuilder.query import Query


def get_comparison_str(item1, item2):
    return 'Items are not equal.\nGot:\n{0}\nExpected:\n{1}'.format(item1, item2)


class TestSelect(TestCase):
    def test_select_all_from_string(self):
        query = Query().from_table(
            table='test_table'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_select_all_from_string_alias(self):
        query = Query().from_table(
            table={
                'table_alias': 'test_table'
            }
        )
        query_str = query.get_sql()
        expected_query = 'SELECT table_alias.* FROM test_table AS table_alias'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_select_all_from_model(self):
        query = Query().from_table(
            table=Account
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_project_account.* FROM test_project_account'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

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
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

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
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

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
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

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
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

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
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

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
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

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
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

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
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

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
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

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
            }, {
                'f4': 'field_four'
            }]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT table_one.field_one AS f1, table_one.field_two AS f2, table_two.field_three AS f3, table_two.field_four AS f4 FROM test_project_account AS table_one, second_table AS table_two'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

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


class TestJoins(TestCase):
    def test_join_str_to_str(self):
        query = Query().from_table(
            table='test_table'
        ).join(
            'other_table',
            condition='other_table.test_id = test_table.id'
        )

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table JOIN other_table ON other_table.test_id = test_table.id'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_join_model_to_str(self):
        query = Query().from_table(
            table=Account
        ).join(
            'other_table',
            condition='other_table.test_id = test_project_account.id'
        )

        query_str = query.get_sql()
        expected_query = 'SELECT test_project_account.* FROM test_project_account JOIN other_table ON other_table.test_id = test_project_account.id'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    # TODO: the foreign key join should do an extra query and
    # merge the results in python afterwards
    def test_join_model_foreign_key(self):
        query = Query().from_table(
            table=Account
        ).join(
            Order,
        )

        query_str = query.get_sql()
        expected_query = 'SELECT test_project_account.* FROM test_project_account JOIN test_project_order ON test_project_order.account_id = test_project_account.id'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_join_model_foreign_key_reverse(self):
        query = Query().from_table(
            table=Order
        ).join(
            Account,
        )

        query_str = query.get_sql()
        expected_query = 'SELECT test_project_order.* FROM test_project_order JOIN test_project_account ON test_project_account.id = test_project_order.account_id'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_join_model_one_to_one(self):
        query = Query().from_table(
            table=Account
        ).join(
            User,
        )

        query_str = query.get_sql()
        expected_query = 'SELECT test_project_account.* FROM test_project_account JOIN test_project_user ON test_project_user.id = test_project_account.user_id'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_join_model_one_to_one_reverse(self):
        query = Query().from_table(
            table=User
        ).join(
            Account,
        )

        query_str = query.get_sql()
        expected_query = 'SELECT test_project_user.* FROM test_project_user JOIN test_project_account ON test_project_account.user_id = test_project_user.id'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_join_model_fields(self):
        query = Query().from_table(
            table=Account,
            fields=[
                'one',
                'two',
            ]
        ).join(
            Order,
            fields=[{
                'three': 'one'
            }, {
                'four': 'two'
            }],
            prefix_fields=False,
        )

        query_str = query.get_sql()
        expected_query = 'SELECT test_project_account.one, test_project_account.two, test_project_order.one AS three, test_project_order.two AS four FROM test_project_account JOIN test_project_order ON test_project_order.account_id = test_project_account.id'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_join_model_fields_all(self):
        query = Query().from_table(
            table=Account,
            fields=[
                '*',
            ]
        ).join(
            Order,
            fields=[
                '*'
            ],
            prefix_fields=False,
            extract_fields=False
        )

        query_str = query.get_sql()
        expected_query = 'SELECT test_project_account.*, test_project_order.* FROM test_project_account JOIN test_project_order ON test_project_order.account_id = test_project_account.id'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_join_model_fields_extract(self):
        query = Query().from_table(
            table=Account,
            fields=[
                '*',
            ]
        ).join(
            Order,
            fields=[
                '*'
            ],
            prefix_fields=False
        )

        query_str = query.get_sql()
        expected_query = 'SELECT test_project_account.*, test_project_order.id, test_project_order.account_id, test_project_order.revenue, test_project_order.margin, test_project_order.margin_percent, test_project_order.time FROM test_project_account JOIN test_project_order ON test_project_order.account_id = test_project_account.id'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_join_model_fields_prefix(self):
        query = Query().from_table(
            table=Account,
            fields=[
                '*',
            ]
        ).join(
            Order,
            fields=[
                'id',
                'margin',
            ],
        )

        query_str = query.get_sql()
        expected_query = 'SELECT test_project_account.*, test_project_order.id AS order__id, test_project_order.margin AS order__margin FROM test_project_account JOIN test_project_order ON test_project_order.account_id = test_project_account.id'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))


class TestWheres(TestCase):
    def test_where_eq(self):
        query = Query().from_table(
            table='test_table'
        ).where(Q(
            one='two'
        ))

        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s)'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

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
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s OR three = %(A1)s)'
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
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s AND (three = %(A1)s OR five = %(A2)s))'
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
        expected_query = 'SELECT test_table.* FROM test_table WHERE (one = %(A0)s AND ((NOT(three = %(A1)s)) OR five = %(A2)s))'
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
            '(((one = %(A0)s AND two > %(A1)s AND (NOT(three >= %(A2)s))) OR ((NOT(four < %(A3)s))) ',
            'OR five <= %(A4)s) AND (six LIKE %(A5)s) AND (NOT(seven LIKE %(A6)s)) AND ',
            '((eight = %(A7)s AND nine = %(A8)s) OR ten = %(A9)s OR (NOT(eleven = %(A10)s))))'
        ])
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))


class TestAggregates(TestCase):

    def test_count_id(self):
        query = Query().from_table(
            table='test_table',
            fields=[
                CountField('id')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.id) AS count_id FROM test_table'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_count_all(self):
        query = Query().from_table(
            table='test_table',
            fields=[
                CountField('*')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT COUNT(test_table.*) AS count_all FROM test_table'
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
        expected_query = 'SELECT AVG(test_project_order.margin) AS avg_margin FROM test_project_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_max(self):
        query = Query().from_table(
            table=Order,
            fields=[
                MaxField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT MAX(test_project_order.margin) AS max_margin FROM test_project_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_min(self):
        query = Query().from_table(
            table=Order,
            fields=[
                MinField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT MIN(test_project_order.margin) AS min_margin FROM test_project_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_stddev(self):
        query = Query().from_table(
            table=Order,
            fields=[
                StdDevField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT STDDEV(test_project_order.margin) AS stddev_margin FROM test_project_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_sum(self):
        query = Query().from_table(
            table=Order,
            fields=[
                SumField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT SUM(test_project_order.margin) AS sum_margin FROM test_project_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_variance(self):
        query = Query().from_table(
            table=Order,
            fields=[
                VarianceField('margin')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT VARIANCE(test_project_order.margin) AS variance_margin FROM test_project_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))


class TestGroupBy(TestCase):

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
        expected_query = 'SELECT COUNT(test_table.id) AS num FROM test_table GROUP BY id'
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
        expected_query = 'SELECT COUNT(test_table.id) AS num FROM test_table GROUP BY test_table.id'
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
        expected_query = 'SELECT COUNT(test_table.id) AS num FROM test_table GROUP BY test_table.id, test_table.id2'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))


class TestOrderBy(TestCase):
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


class TestLimit(TestCase):
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


class TestDates(TestCase):
    fixtures = [
        'test_project/test_data.json'
    ]

    def test_year(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Year('time')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT CAST(extract(year from test_project_order.time) as INT) AS time__year FROM test_project_order'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_year_auto(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Year('time', auto=True)
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT CAST(extract(year from test_project_order.time) as INT) AS time__year, CAST(extract(epoch from date_trunc(\'year\', test_project_order.time)) as INT) AS time__epoch FROM test_project_order GROUP BY time__year, time__epoch ORDER BY time__epoch ASC'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_year_auto_desc(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Year('time', auto=True, desc=True)
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT CAST(extract(year from test_project_order.time) as INT) AS time__year, CAST(extract(epoch from date_trunc(\'year\', test_project_order.time)) as INT) AS time__epoch FROM test_project_order GROUP BY time__year, time__epoch ORDER BY time__epoch DESC'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_month_auto(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Month('time', auto=True)
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT CAST(extract(year from test_project_order.time) as INT) AS time__year, CAST(extract(month from test_project_order.time) as INT) AS time__month, CAST(extract(epoch from date_trunc(\'month\', test_project_order.time)) as INT) AS time__epoch FROM test_project_order GROUP BY time__year, time__month, time__epoch ORDER BY time__epoch ASC'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_hour_auto(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Hour('time', auto=True)
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT CAST(extract(year from test_project_order.time) as INT) AS time__year, CAST(extract(month from test_project_order.time) as INT) AS time__month, CAST(extract(day from test_project_order.time) as INT) AS time__day, CAST(extract(hour from test_project_order.time) as INT) AS time__hour, CAST(extract(epoch from date_trunc(\'hour\', test_project_order.time)) as INT) AS time__epoch FROM test_project_order GROUP BY time__year, time__month, time__day, time__hour, time__epoch ORDER BY time__epoch ASC'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_minute_auto(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Minute('time', auto=True)
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT CAST(extract(year from test_project_order.time) as INT) AS time__year, CAST(extract(month from test_project_order.time) as INT) AS time__month, CAST(extract(day from test_project_order.time) as INT) AS time__day, CAST(extract(hour from test_project_order.time) as INT) AS time__hour, CAST(extract(minute from test_project_order.time) as INT) AS time__minute, CAST(extract(epoch from date_trunc(\'minute\', test_project_order.time)) as INT) AS time__epoch FROM test_project_order GROUP BY time__year, time__month, time__day, time__hour, time__minute, time__epoch ORDER BY time__epoch ASC'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_second_auto(self):
        query = Query().from_table(
            table=Order,
            fields=[
                Second('time', auto=True)
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT CAST(extract(year from test_project_order.time) as INT) AS time__year, CAST(extract(month from test_project_order.time) as INT) AS time__month, CAST(extract(day from test_project_order.time) as INT) AS time__day, CAST(extract(hour from test_project_order.time) as INT) AS time__hour, CAST(extract(minute from test_project_order.time) as INT) AS time__minute, CAST(extract(second from test_project_order.time) as INT) AS time__second, CAST(extract(epoch from date_trunc(\'second\', test_project_order.time)) as INT) AS time__epoch FROM test_project_order GROUP BY time__year, time__month, time__day, time__hour, time__minute, time__second, time__epoch ORDER BY time__epoch ASC'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_group_none(self):
        query = Query().from_table(
            table=Order,
            fields=[
                NoneTime('time')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT CAST(extract(epoch from test_project_order.time) as INT) AS time__epoch FROM test_project_order GROUP BY time__epoch ORDER BY time__epoch ASC'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_group_all(self):
        query = Query().from_table(
            table=Order,
            fields=[
                AllTime('time')
            ]
        )
        query_str = query.get_sql()
        expected_query = 'SELECT CAST(extract(epoch from MIN(test_project_order.time)) as INT) AS time__epoch FROM test_project_order ORDER BY time__epoch ASC'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))


class TestModels(TestCase):
    fixtures = [
        'test_project/test_data.json'
    ]

    def test_single_model(self):
        query = Query().from_table(
            Account
        )
        rows = query.select(True)

        self.assertGreater(len(rows), 0, 'No records')

        for row in rows:
            self.assertIsInstance(row, Account, 'Row is not model instance')

    def test_joined_model_foreign(self):
        query = Query().from_table(
            Account
        ).join(
            right_table=Order,
            fields=[
                '*'
            ]
        )

        rows = query.select(True)

        self.assertGreater(len(rows), 0, 'No records')
        # TODO make sure this isn't running a query for each access of model.model

        logger = Logger()
        logger.start_logging()
        for row in rows:
            self.assertIsInstance(row, Account, 'Record is not model instance')
            self.assertIs(hasattr(row, 'order'), True, 'Row does not have nested model')
            self.assertIsInstance(row.order, Order, 'Nested record is not model instance')
        self.assertEqual(logger.count(), 0, 'Queries were executed when none should')

    def test_joined_model_foreign_reverse(self):
        query = Query().from_table(
            Order
        ).join(
            right_table=Account,
            fields=[
                '*'
            ]
        )
        rows = query.select(True)

        self.assertGreater(len(rows), 0, 'No records')

        logger = Logger()
        logger.start_logging()
        for row in rows:
            self.assertIsInstance(row, Order, 'Record is not model instance')
            self.assertIs(hasattr(row, 'account'), True, 'Row does not have nested model')
            self.assertIsInstance(row.account, Account, 'Nested record is not model instance')
        self.assertEqual(logger.count(), 0, 'Queries were executed when none should')

    def test_joined_model_one_to_one(self):
        query = Query().from_table(
            Account
        ).join(
            right_table=User,
            fields=[
                '*'
            ]
        )

        rows = query.select(True)

        self.assertGreater(len(rows), 0, 'No records')

        logger = Logger()
        logger.start_logging()
        for row in rows:
            self.assertIsInstance(row, Account, 'Record is not model instance')
            self.assertIs(hasattr(row, 'user'), True, 'Row does not have nested model')
            self.assertIsInstance(row.user, User, 'Nested record is not model instance')
        self.assertEqual(logger.count(), 0, 'Queries were executed when none should')

    def test_joined_model_one_to_one_reverse(self):
        query = Query().from_table(
            User
        ).join(
            right_table=Account,
            fields=[
                '*'
            ]
        )

        rows = query.select(True)

        self.assertGreater(len(rows), 0, 'No records')

        logger = Logger()
        logger.start_logging()
        for row in rows:
            self.assertIsInstance(row, User, 'Record is not model instance')
            self.assertIs(hasattr(row, 'account'), True, 'Row does not have nested model')
            self.assertIsInstance(row.account, Account, 'Nested record is not model instance')
        self.assertEqual(logger.count(), 0, 'Queries were executed when none should')


class TestWindowFunctions(TestCase):
    fixtures = [
        'test_project/test_data.json'
    ]

    # def test_rank(self):
    #     query = Query().from_table(
    #         Order,
    #         fields=[
    #             Rank
    #         ]
    #     )
    #     pprint(query.select())


class TestLogger(TestCase):
    fixtures = [
        'test_project/test_data.json'
    ]

    def test_logger(self):
        logger_one = Logger('one')
        logger_two = Logger('two')

        logger_one.start_logging()
        query = Query().from_table(Account)
        query.select()

        self.assertEqual(logger_one.count(), 1, 'Incorrect number of queries')

        query.select()
        logger_two.start_logging()
        query.select()
        logger_one.stop_logging()
        query.select()

        self.assertEqual(logger_one.count(), 3, 'Incorrect number of queries')
        self.assertEqual(logger_two.count(), 2, 'Incorrect number of queries')

        query.select()
        logger_one.start_logging()
        query.select()

        self.assertEqual(logger_one.count(), 4, 'Incorrect number of queries')
        self.assertEqual(logger_two.count(), 4, 'Incorrect number of queries')

        query.select()
        logger_two.clear_log()
        query.select()

        self.assertEqual(logger_one.count(), 6, 'Incorrect number of queries')
        self.assertEqual(logger_two.count(), 1, 'Incorrect number of queries')

    def test_log_manager(self):
        self.assertEqual(len(LogManager.loggers), 0, 'Incorrect number of loggers')
        logger_one = LogManager.get_logger('one')
        self.assertEqual(len(LogManager.loggers), 1, 'Incorrect number of loggers')
        logger_one = LogManager.get_logger('one')
        self.assertEqual(len(LogManager.loggers), 1, 'Incorrect number of loggers')
        LogManager.get_logger('two')
        self.assertEqual(len(LogManager.loggers), 2, 'Incorrect number of loggers')

        logger_one.start_logging()
        query = Query().from_table(Account)
        query.select()

        self.assertEqual(logger_one.count(), 1, 'Incorrect number of queries')
        LogManager.disable_logging()
        query.select()
        self.assertEqual(logger_one.count(), 1, 'Incorrect number of queries')
        LogManager.enable_logging()
        query.select()
        self.assertEqual(logger_one.count(), 2, 'Incorrect number of queries')
