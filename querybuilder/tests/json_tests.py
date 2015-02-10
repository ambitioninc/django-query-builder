from django.test.testcases import TestCase
from django.test.utils import override_settings
from querybuilder.fields import JsonField
from querybuilder.query import Query
from querybuilder.tests.models import MetricRecord


@override_settings(DEBUG=True)
class TestUpdate(TestCase):

    def test_one(self):
        metric_record = MetricRecord(data={
            'one': 1,
            'two': 'two',
        })
        metric_record.save()

        one_field = JsonField('data', key='one', alias='my_one_alias')
        two_field = JsonField('data', key='two', alias='my_two_alias')

        query = Query().from_table(MetricRecord, fields=[two_field]).where(**{
            two_field.get_where_key(): 'one'
        })
        self.assertEqual(
            query.get_sql(),
            (
                'SELECT tests_metricrecord.data->\'two\' AS my_two_alias FROM tests_metricrecord '
                'WHERE (tests_metricrecord.data->>\'two\' = %(A0)s)'
            )
        )
        self.assertEqual(query.select(), [])

        query = Query().from_table(MetricRecord, fields=[two_field]).where(**{
            two_field.get_where_key(): 'two'
        })
        self.assertEqual(
            query.get_sql(),
            (
                'SELECT tests_metricrecord.data->\'two\' AS my_two_alias FROM tests_metricrecord '
                'WHERE (tests_metricrecord.data->>\'two\' = %(A0)s)'
            )
        )
        self.assertEqual(query.select(), [{'my_two_alias': 'two'}])

        query = Query().from_table(MetricRecord, fields=[one_field]).where(**{
            one_field.get_where_key(): '1'
        })
        self.assertEqual(
            query.get_sql(),
            (
                'SELECT tests_metricrecord.data->\'one\' AS my_one_alias FROM tests_metricrecord '
                'WHERE (tests_metricrecord.data->>\'one\' = %(A0)s)'
            )
        )
        self.assertEqual(query.select(), [{'my_one_alias': 1}])

        query = Query().from_table(MetricRecord, fields=[one_field]).where(**{
            one_field.get_where_key(): '2'
        })
        self.assertEqual(
            query.get_sql(),
            (
                'SELECT tests_metricrecord.data->\'one\' AS my_one_alias FROM tests_metricrecord '
                'WHERE (tests_metricrecord.data->>\'one\' = %(A0)s)'
            )
        )
        self.assertEqual(query.select(), [])
