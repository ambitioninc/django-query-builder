from django.test.utils import override_settings

from querybuilder.logger import Logger
from querybuilder.query import Query
from querybuilder.tests.models import Uniques
from querybuilder.tests.query_tests import QueryTestCase


@override_settings(DEBUG=True)
class TestUpdate(QueryTestCase):

    def setUp(self):
        self.logger = Logger()
        self.logger.start_logging()

    def test_upsert(self):
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
