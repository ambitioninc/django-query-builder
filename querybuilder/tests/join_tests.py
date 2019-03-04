from querybuilder.tests.models import Account, Order, User
from querybuilder.query import Query
from querybuilder.tests.query_tests import QueryTestCase, get_comparison_str


class JoinTest(QueryTestCase):

    def test_join_str_to_str(self):
        query = Query().from_table(
            table='test_table'
        ).join(
            'other_table',
            condition='other_table.test_id = test_table.id'
        )

        query_str = query.get_sql()
        expected_query = (
            'SELECT test_table.* '
            'FROM test_table '
            'JOIN other_table ON other_table.test_id = test_table.id'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_join_model_to_str(self):
        query = Query().from_table(
            table=Account
        ).join(
            'other_table',
            condition='other_table.test_id = querybuilder_tests_account.id'
        )

        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_account.* '
            'FROM querybuilder_tests_account '
            'JOIN other_table ON other_table.test_id = querybuilder_tests_account.id'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_no_fields_and_fields(self):
        query = Query().from_table(
            table=Account,
            fields=None
        ).join(
            'other_table',
            fields=[
                'field_one',
                'field_two'
            ],
            prefix_fields=True,
            condition='other_table.test_id = querybuilder_tests_account.id'
        )

        query_str = query.get_sql()
        expected_query = (
            'SELECT other_table.field_one AS "other_table__field_one", '
            'other_table.field_two AS "other_table__field_two" '
            'FROM querybuilder_tests_account '
            'JOIN other_table ON other_table.test_id = querybuilder_tests_account.id'
        )
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
        expected_query = (
            'SELECT querybuilder_tests_account.* '
            'FROM querybuilder_tests_account '
            'JOIN querybuilder_tests_order ON querybuilder_tests_order.account_id = querybuilder_tests_account.id'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_join_model_foreign_key_reverse(self):
        query = Query().from_table(
            table=Order
        ).join(
            Account,
        )

        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_order.* '
            'FROM querybuilder_tests_order '
            'JOIN querybuilder_tests_account ON querybuilder_tests_account.id = querybuilder_tests_order.account_id'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_join_model_one_to_one(self):
        query = Query().from_table(
            table=Account
        ).join(
            User,
        )

        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_account.* '
            'FROM querybuilder_tests_account '
            'JOIN querybuilder_tests_user ON querybuilder_tests_user.id = querybuilder_tests_account.user_id'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))

    def test_join_model_one_to_one_reverse(self):
        query = Query().from_table(
            table=User
        ).join(
            Account,
        )

        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_user.* '
            'FROM querybuilder_tests_user '
            'JOIN querybuilder_tests_account ON querybuilder_tests_account.user_id = querybuilder_tests_user.id'
        )
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
            }]
        )

        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_account.one, '
            'querybuilder_tests_account.two, '
            'querybuilder_tests_order.one AS "three", '
            'querybuilder_tests_order.two AS "four" '
            'FROM querybuilder_tests_account '
            'JOIN querybuilder_tests_order ON querybuilder_tests_order.account_id = querybuilder_tests_account.id'
        )
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
            extract_fields=False
        )

        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_account.*, '
            'querybuilder_tests_order.* '
            'FROM querybuilder_tests_account '
            'JOIN querybuilder_tests_order ON querybuilder_tests_order.account_id = querybuilder_tests_account.id'
        )
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
            ]
        )

        query_str = query.get_sql()
        expected_query = (
            'SELECT querybuilder_tests_account.*, '
            'querybuilder_tests_order.id, '
            'querybuilder_tests_order.account_id, '
            'querybuilder_tests_order.revenue, '
            'querybuilder_tests_order.margin, '
            'querybuilder_tests_order.margin_percent, '
            'querybuilder_tests_order.time '
            'FROM querybuilder_tests_account '
            'JOIN querybuilder_tests_order ON querybuilder_tests_order.account_id = querybuilder_tests_account.id'
        )
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
            prefix_fields=True
        )

        query_str = query.get_sql()

        expected_query = (
            'SELECT querybuilder_tests_account.*, '
            'querybuilder_tests_order.id AS "order__id", '
            'querybuilder_tests_order.margin AS "order__margin" '
            'FROM querybuilder_tests_account '
            'JOIN querybuilder_tests_order ON querybuilder_tests_order.account_id = querybuilder_tests_account.id'
        )
        self.assertEqual(query_str, expected_query)
