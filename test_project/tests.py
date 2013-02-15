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
        self.assertEqual(query_str, expected_query, 'Queries did not match')

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


class TestOrderBy(unittest.TestCase):

    def test_order_by_single_asc(self):
        query = Query().from_table(
            table='test_table'
        ).order_by(
            'field_one'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table ORDER BY field_one ASC'
        print query_str
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_order_by_args_asc(self):
        query = Query().from_table(
            table='test_table'
        ).order_by(
            'field_one',
            'field_two'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table ORDER BY field_one ASC, field_two ASC'
        print query_str
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_order_by_chained_asc(self):
        query = Query().from_table(
            table='test_table'
        ).order_by(
            'field_one'
        ).order_by(
            'field_two'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table ORDER BY field_one ASC, field_two ASC'
        print query_str
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_order_by_single_desc(self):
        query = Query().from_table(
            table='test_table'
        ).order_by(
            '-field_one'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table ORDER BY field_one DESC'
        print query_str
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_order_by_args_desc(self):
        query = Query().from_table(
            table='test_table'
        ).order_by(
            '-field_one',
            '-field_two'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table ORDER BY field_one DESC, field_two DESC'
        print query_str
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    def test_order_by_chained_desc(self):
        query = Query().from_table(
            table='test_table'
        ).order_by(
            '-field_one'
        ).order_by(
            '-field_two'
        )
        query_str = query.get_sql()
        expected_query = 'SELECT test_table.* FROM test_table ORDER BY field_one DESC, field_two DESC'
        print query_str
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
