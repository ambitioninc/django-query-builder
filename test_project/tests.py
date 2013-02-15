import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "test_project.settings")
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


class TestOrderBy(unittest.TestCase):

    def test_order_by_single_asc(self):
        query = Query().from_table(
            table='test_table'
        ).order_by(
            'field_one'
        )
        query_str = query.get_sql()
        print query_str
        print query.get_sql(debug=True)
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
    pass

    # def test_limit(self):
    #     raise NotImplementedError
    #
    # def test_offset(self):
    #     raise NotImplementedError
    #
    # def test_limit_with_offset(self):
    #     raise NotImplementedError
