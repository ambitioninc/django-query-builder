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
        print query_str
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
        print query_str
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
        print query_str
        self.assertEqual(query_str, expected_query, 'Queries did not match')

    # def test_select_fields_alias_from_string(self):
    #     raise NotImplementedError
    #
    # def test_select_fields_alias_from_string_alias(self):
    #     raise NotImplementedError
    #
    # def test_select_fields_alias_from_model(self):
    #     raise NotImplementedError
    #
    # def test_select_fields_alias_from_model_alias(self):
    #     raise NotImplementedError


class TestOrderBy(unittest.TestCase):
    pass

    # def test_order_by_single_asc(self):
    #     raise NotImplementedError
    #
    # def test_order_by_list_asc(self):
    #     raise NotImplementedError
    #
    # def test_order_by_args_asc(self):
    #     raise NotImplementedError
    #
    # def test_order_by_single_desc(self):
    #     raise NotImplementedError
    #
    # def test_order_by_list_desc(self):
    #     raise NotImplementedError
    #
    # def test_order_by_args_desc(self):
    #     raise NotImplementedError
    #
    # def test_order_by_chained(self):
    #     raise NotImplementedError


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
