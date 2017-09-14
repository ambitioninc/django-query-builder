from django.test.utils import override_settings
from django import VERSION
from django_dynamic_fixture import G

from querybuilder.logger import Logger
from querybuilder.query import Query
from querybuilder.tests.models import Uniques, User
from querybuilder.tests.query_tests import QueryTestCase


@override_settings(DEBUG=True)
class TestUpsert(QueryTestCase):

    def setUp(self):
        self.logger = Logger()
        self.logger.start_logging()

    def test_upsert_json_field(self):
        """
        Only runs for django 1.9 because the jsonfield project uses an incorrect db prep value
        """
        if VERSION[0] != 1 or VERSION[1] < 9:
            return

        items = [
            Uniques(field1='1.1', field2='1.2', field3='1.3', field6='1.6', field7='1.7', field8={
                'one': 'two'
            }),
        ]

        Query().from_table(Uniques).upsert(
            items,
            unique_fields=['field1'],
            update_fields=['field3', 'field4', 'field5', 'field8']
        )

    def test_upsert(self):
        """
        Verifies that records get upserted correctly. Skipping this test now until travis-ci supports 9.5 addon.
        """
        items = [
            Uniques(field1='1.1', field2='1.2', field3='1.3', field6='1.6', field7='1.7'),
        ]

        Query().from_table(Uniques).upsert(
            items,
            unique_fields=['field1'],
            update_fields=['field3', 'field4', 'field5']
        )

        model = Uniques.objects.get()
        self.assertEqual(model.field1, '1.1')
        self.assertEqual(model.field2, '1.2')
        self.assertEqual(model.field3, '1.3')
        self.assertEqual(model.field4, 'default_value')
        self.assertEqual(model.field5, None)
        self.assertEqual(model.field6, '1.6')
        self.assertEqual(model.field7, '1.7')
        self.assertEqual(model.field8, {})

        items = [
            Uniques(
                field1='1.1',
                field2='1.2 edited',
                field3='1.3 edited',
                field4='not default',
                field5='new value',
                field6='1.6',
                field7='1.7'
            ),
        ]

        Query().from_table(Uniques).upsert(
            items,
            unique_fields=['field1'],
            update_fields=['field3', 'field4', 'field5']
        )

        # Only fields 3, 4, 5 should be updated
        model = Uniques.objects.get()
        self.assertEqual(model.field1, '1.1')
        self.assertEqual(model.field2, '1.2')
        self.assertEqual(model.field3, '1.3 edited')
        self.assertEqual(model.field4, 'not default')
        self.assertEqual(model.field5, 'new value')
        self.assertEqual(model.field6, '1.6')
        self.assertEqual(model.field7, '1.7')

        # Include a new record and an existing record
        items = [
            Uniques(field1='1.1', field2='1.2', field3='1.3', field6='1.6', field7='1.7'),
            Uniques(
                field1='2.1',
                field2='2.2',
                field3='2.3',
                field4='not default',
                field5='not null',
                field6='2.6',
                field7='2.7'
            ),
        ]

        Query().from_table(Uniques).upsert(
            items,
            unique_fields=['field1'],
            update_fields=['field3', 'field4', 'field5']
        )

        # Both records should exist and have different data
        models = list(Uniques.objects.order_by('id'))

        self.assertEqual(models[0].field1, '1.1')
        self.assertEqual(models[0].field2, '1.2')
        self.assertEqual(models[0].field3, '1.3')
        self.assertEqual(models[0].field4, 'default_value')
        self.assertEqual(models[0].field5, None)
        self.assertEqual(models[0].field6, '1.6')
        self.assertEqual(models[0].field7, '1.7')

        self.assertEqual(models[1].field1, '2.1')
        self.assertEqual(models[1].field2, '2.2')
        self.assertEqual(models[1].field3, '2.3')
        self.assertEqual(models[1].field4, 'not default')
        self.assertEqual(models[1].field5, 'not null')
        self.assertEqual(models[1].field6, '2.6')
        self.assertEqual(models[1].field7, '2.7')

    def test_upsert_pk(self):
        """
        Makes sure upserting is possible when the only uniqueness constraint is the pk.
        """
        user1 = G(User, email='user1')
        user1.email = 'user1change'
        user2 = User(email='user2')
        user3 = User(email='user3')

        self.assertEqual(User.objects.count(), 1)
        Query().from_table(User).upsert(
            [user1, user2, user3],
            unique_fields=['id'],
            update_fields=['email'],
        )
        self.assertEqual(User.objects.count(), 3)

        users = list(User.objects.order_by('id'))

        self.assertEqual(users[0].email, 'user1change')
        self.assertEqual(users[1].email, 'user2')
        self.assertEqual(users[2].email, 'user3')

    def test_upsert_pk_return_dicts(self):
        """
        Makes sure upserting is possible when the only uniqueness constraint is the pk. Should return dicts.
        """
        user1 = G(User, email='user1')
        user1.email = 'user1change'
        user2 = User(email='user2')
        user3 = User(email='user3')

        self.assertEqual(User.objects.count(), 1)
        rows = Query().from_table(User).upsert(
            [user1, user2, user3],
            unique_fields=['id'],
            update_fields=['email'],
            return_rows=True,
        )
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(len(rows), 3)

        # Check ids
        for row in rows:
            self.assertIsNotNone(row['id'])

        # Check emails
        email_set = {
            row['email'] for row in rows
        }
        self.assertEqual(email_set, {'user1change', 'user2', 'user3'})

        # Check fields from db
        users = list(User.objects.order_by('id'))
        self.assertEqual(users[0].email, 'user1change')
        self.assertEqual(users[1].email, 'user2')
        self.assertEqual(users[2].email, 'user3')

    def test_upsert_pk_return_models(self):
        """
        Makes sure upserting is possible when the only uniqueness constraint is the pk. Should return models.
        """
        user1 = G(User, email='user1')
        user1.email = 'user1change'
        user2 = User(email='user2')
        user3 = User(email='user3')

        self.assertEqual(User.objects.count(), 1)
        records = Query().from_table(User).upsert(
            [user1, user2, user3],
            unique_fields=['id'],
            update_fields=['email'],
            return_models=True,
        )
        self.assertEqual(len(records), 3)

        # Check ids
        for record in records:
            self.assertIsNotNone(record.id)

        # Check emails
        email_set = {
            record.email for record in records
        }
        self.assertEqual(email_set, {'user1change', 'user2', 'user3'})

        # Check fields from db
        users = list(User.objects.order_by('id'))
        self.assertEqual(users[0].email, 'user1change')
        self.assertEqual(users[1].email, 'user2')
        self.assertEqual(users[2].email, 'user3')

    def test_upsert_custom_db_column(self):
        """
        Makes sure upserting a model containing a field with a custom db_column name works.
        """

        model = Uniques(field1='1', custom_field_name='test')

        Query().from_table(Uniques).upsert(
            [model],
            unique_fields=['field1'],
            update_fields=[]
        )

        saved_model = Uniques.objects.get()

        self.assertEqual(saved_model.custom_field_name, 'test')

        saved_model.custom_field_name = 'edited'

        Query().from_table(Uniques).upsert(
            [saved_model],
            unique_fields=['field1'],
            update_fields=['custom_field_name']
        )

        updated_model = Uniques.objects.get()
        self.assertEqual(updated_model.custom_field_name, 'edited')

        rows = Query().from_table(Uniques).select()
        self.assertEqual(rows[0]['actual_db_column_name'], 'edited')
