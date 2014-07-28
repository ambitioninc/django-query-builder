from django.db.models import Q
from querybuilder.logger import Logger
from querybuilder.query import Query
from querybuilder.tests.models import Account, Order, User
from querybuilder.tests.query_tests import QueryTestCase, get_comparison_str


class SelectTest(QueryTestCase):

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
        expected_query = 'SELECT tests_account.* FROM tests_account'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_select_all_from_model_alias(self):
        query = Query().from_table(
            table={
                'table_alias': Account
            }
        )
        query_str = query.get_sql()
        expected_query = 'SELECT table_alias.* FROM tests_account AS table_alias'
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
        expected_query = 'SELECT tests_account.field_one, tests_account.field_two FROM tests_account'
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
        expected_query = 'SELECT table_alias.field_one, table_alias.field_two FROM tests_account AS table_alias'
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
        expected_query = (
            'SELECT test_table.field_one AS field_alias_one, '
            'test_table.field_two AS field_alias_two '
            'FROM test_table'
        )
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
        expected_query = (
            'SELECT table_alias.field_one AS field_alias_one, '
            'table_alias.field_two AS field_alias_two '
            'FROM test_table '
            'AS table_alias'
        )
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
        expected_query = (
            'SELECT tests_account.field_one AS field_alias_one, '
            'tests_account.field_two AS field_alias_two '
            'FROM tests_account'
        )
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
        expected_query = (
            'SELECT table_alias.field_one AS field_alias_one, '
            'table_alias.field_two AS field_alias_two '
            'FROM tests_account '
            'AS table_alias'
        )
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
        expected_query = (
            'SELECT tests_account.field_one, '
            'tests_account.field_two, '
            'second_table.field_three, '
            'second_table.field_four '
            'FROM tests_account, second_table'
        )
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
        expected_query = (
            'SELECT table_one.field_one AS f1, '
            'table_one.field_two AS f2, '
            'table_two.field_three AS f3, '
            'table_two.field_four AS f4 '
            'FROM tests_account AS table_one, '
            'second_table AS table_two'
        )
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
        expected_query = (
            'SELECT tests_account.field_one, '
            'tests_account.field_two, '
            'T1.field_three, '
            'T1.field_four '
            'FROM tests_account, tests_account AS T1'
        )
        self.assertEqual(query_str, expected_query, '\n{0}\n!=\n{1}'.format(query_str, expected_query))


class InnerQueryTest(QueryTestCase):
    def test_inner(self):
        inner_query = Query().from_table(
            Account
        )
        query = Query().from_table(
            inner_query
        )

        query_str = query.get_sql()
        expected_query = 'WITH T0 AS (SELECT tests_account.* FROM tests_account) SELECT T0.* FROM T0'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

        inner_query = Query().from_table(
            Account
        )

        query = Query().with_query(inner_query, 's3').from_table('s3')
        query_str = query.get_sql()
        expected_query = 'WITH s3 AS (SELECT tests_account.* FROM tests_account) SELECT s3.* FROM s3'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_inner_alias(self):
        inner_query = Query().from_table(
            Account
        )
        query = Query().from_table({
            'Q0': inner_query
        })

        query_str = query.get_sql()
        expected_query = 'WITH Q0 AS (SELECT tests_account.* FROM tests_account) SELECT Q0.* FROM Q0'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_inner_args(self):
        inner_query = Query().from_table(
            Account
        ).where(
            Q(id__gt=1) & Q(id__lt=10)
        )
        query = Query().from_table(
            inner_query
        )

        query_str = query.get_sql()
        expected_query = (
            'WITH T0 AS '
            '(SELECT tests_account.* FROM tests_account WHERE (id > %(T0A0)s AND id < %(T0A1)s)) '
            'SELECT T0.* FROM T0'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_inner_outer_args(self):
        inner_query = Query().from_table(
            Account
        ).where(
            Q(id__gt=1) & Q(id__lt=10)
        )
        query = Query().from_table(
            inner_query
        ).where(
            ~Q(id=0)
        )

        query_str = query.get_sql()
        expected_query = (
            'WITH T0 AS '
            '(SELECT tests_account.* FROM tests_account WHERE (id > %(T0A0)s AND id < %(T0A1)s)) '
            'SELECT T0.* FROM T0 WHERE ((NOT(id = %(A0)s)))'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_inner_outer_args_many(self):
        inner_query = Query().from_table(
            Account
        ).where(
            Q(id__gt=1) & Q(id__lt=10)
        )

        inner_query2 = Query().from_table(
            Account
        ).where(
            Q(id__gt=1) & Q(id__lt=10)
        )

        query = Query().from_table(
            inner_query
        ).from_table(
            inner_query2
        ).where(
            ~Q(id=0)
        )

        query_str = query.get_sql()
        expected_query = (
            'WITH T1 AS '
            '(SELECT tests_account.* FROM tests_account WHERE (id > %(T1A0)s AND id < %(T1A1)s)), '
            'T0 AS ('
            'SELECT tests_account.* '
            'FROM tests_account '
            'WHERE (id > %(T0A0)s AND id < %(T0A1)s)) '
            'SELECT T0.*, T1.* '
            'FROM T0, T1 '
            'WHERE ((NOT(id = %(A0)s)))'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_three_levels(self):
        inner_inner_query = Query().from_table(
            Account
        ).where(
            Q(id__gt=1) & Q(id__lt=10)
        )

        inner_inner_query2 = Query().from_table(
            Account
        ).where(
            Q(id__gt=1) & Q(id__lt=10)
        )

        inner_query = Query().from_table(
            Account
        ).where(
            Q(id__gt=1) & Q(id__lt=10)
        )

        inner_query2 = Query().from_table(
            inner_inner_query
        ).from_table(
            inner_inner_query2
        ).where(
            Q(id__gt=1) & Q(id__lt=10)
        )

        query = Query().from_table(
            inner_query
        ).from_table(
            inner_query2
        ).where(
            ~Q(id=0)
        )
        query_str = query.get_sql()
        expected_query = (
            'WITH T1T1 AS (SELECT tests_account.* FROM tests_account WHERE (id > %(T1T1A0)s AND id < %(T1T1A1)s)), '
            'T1T0 AS (SELECT tests_account.* FROM tests_account WHERE (id > %(T1T0A0)s AND id < %(T1T0A1)s)), '
            'T1 AS (SELECT T1T0.*, T1T1.* FROM T1T0, T1T1 WHERE (id > %(T1A0)s AND id < %(T1A1)s)), '
            'T0 AS (SELECT tests_account.* FROM tests_account WHERE (id > %(T0A0)s AND id < %(T0A1)s)) '
            'SELECT T0.*, T1.* FROM T0, T1 WHERE ((NOT(id = %(A0)s)))'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))


class ModelTest(QueryTestCase):
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
            ],
            prefix_fields=True
        )
        rows = query.select(True)

        self.assertGreater(len(rows), 0, 'No records')

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
            ],
            prefix_fields=True
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
            ],
            prefix_fields=True
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
            ],
            prefix_fields=True
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


class DistinctTest(QueryTestCase):
    def test_distinct(self):
        query = Query().from_table(
            table=Account
        ).distinct()

        query_str = query.get_sql()
        expected_query = 'SELECT DISTINCT tests_account.* FROM tests_account'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

        query.distinct(use_distinct=False)

        query_str = query.get_sql()
        expected_query = 'SELECT tests_account.* FROM tests_account'
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
