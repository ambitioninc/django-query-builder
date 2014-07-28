from querybuilder.logger import Logger, LogManager
from querybuilder.query import Query
from querybuilder.tests.models import Account
from querybuilder.tests.query_tests import QueryTestCase


class InsertTest(QueryTestCase):

    def setUp(self):
        self.logger = Logger()
        self.logger.start_logging()

    def tearDown(self):
        super(InsertTest, self).tearDown()
        LogManager.loggers = {}

    def test_insert_single_row(self):
        query = Query().from_table(
            table=Account,
            fields=[
                'user_id',
                'first_name',
                'last_name'
            ]
        )

        rows = [
            [1, 'Test', 'User']
        ]

        sql, sql_params = query.get_insert_sql(rows)

        self.assertEqual(
            sql,
            (
                'INSERT INTO tests_account (user_id, first_name, last_name) VALUES (%s, %s, %s)'
            )
        )
        self.assertEqual(sql_params[0], 1)
        self.assertEqual(sql_params[1], 'Test')
        self.assertEqual(sql_params[2], 'User')

        query.insert(rows)
        sql = self.logger.get_log()[0]['sql']
        self.assertEqual(sql, "INSERT INTO tests_account (user_id, first_name, last_name) VALUES (1, 'Test', 'User')")

    def test_insert_multiple_rows(self):
        query = Query().from_table(
            table=Account,
            fields=[
                'user_id',
                'first_name',
                'last_name'
            ]
        )

        rows = [
            [1, 'Test', 'User'],
            [2, 'Test2', 'User2'],
        ]

        sql, sql_params = query.get_insert_sql(rows)

        self.assertEqual(
            sql,
            'INSERT INTO tests_account (user_id, first_name, last_name) VALUES (%s, %s, %s), (%s, %s, %s)'
        )
        self.assertEqual(sql_params[0], 1)
        self.assertEqual(sql_params[1], 'Test')
        self.assertEqual(sql_params[2], 'User')
        self.assertEqual(sql_params[3], 2)
        self.assertEqual(sql_params[4], 'Test2')
        self.assertEqual(sql_params[5], 'User2')

        query.insert(rows)
        sql = self.logger.get_log()[0]['sql']
        self.assertEqual(
            sql,
            ("INSERT INTO tests_account (user_id, first_name, last_name) "
             "VALUES (1, 'Test', 'User'), (2, 'Test2', 'User2')")
        )
