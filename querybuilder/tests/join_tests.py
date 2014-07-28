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
            condition='other_table.test_id = tests_account.id'
        )

        query_str = query.get_sql()
        expected_query = (
            'SELECT tests_account.* '
            'FROM tests_account '
            'JOIN other_table ON other_table.test_id = tests_account.id'
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
            condition='other_table.test_id = tests_account.id'
        )

        query_str = query.get_sql()
        expected_query = (
            'SELECT other_table.field_one AS other_table__field_one, '
            'other_table.field_two AS other_table__field_two '
            'FROM tests_account '
            'JOIN other_table ON other_table.test_id = tests_account.id'
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
            'SELECT tests_account.* '
            'FROM tests_account '
            'JOIN tests_order ON tests_order.account_id = tests_account.id'
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
            'SELECT tests_order.* '
            'FROM tests_order '
            'JOIN tests_account ON tests_account.id = tests_order.account_id'
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
            'SELECT tests_account.* '
            'FROM tests_account '
            'JOIN tests_user ON tests_user.id = tests_account.user_id'
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
            'SELECT tests_user.* '
            'FROM tests_user '
            'JOIN tests_account ON tests_account.user_id = tests_user.id'
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
            'SELECT tests_account.one, '
            'tests_account.two, '
            'tests_order.one AS three, '
            'tests_order.two AS four '
            'FROM tests_account '
            'JOIN tests_order ON tests_order.account_id = tests_account.id'
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
            'SELECT tests_account.*, '
            'tests_order.* '
            'FROM tests_account '
            'JOIN tests_order ON tests_order.account_id = tests_account.id'
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
            'SELECT tests_account.*, '
            'tests_order.id, '
            'tests_order.account_id, '
            'tests_order.revenue, '
            'tests_order.margin, '
            'tests_order.margin_percent, '
            'tests_order.time '
            'FROM tests_account '
            'JOIN tests_order ON tests_order.account_id = tests_account.id'
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
            'SELECT tests_account.*, '
            'tests_order.id AS order__id, '
            'tests_order.margin AS order__margin '
            'FROM tests_account '
            'JOIN tests_order ON tests_order.account_id = tests_account.id'
        )
        self.assertEqual(query_str, expected_query, get_comparison_str(query_str, expected_query))
