from django.db import connection

from querybuilder.cursor import json_cursor
from querybuilder.tests.base import QuerybuilderTestCase
from querybuilder.tests.models import MetricRecord


class JsonCursorTests(QuerybuilderTestCase):
    def test_json_cursor(self):
        data = {'one': 1, 'two': 2}
        MetricRecord.objects.create(data=data)
        with json_cursor(connection) as cursor:
            cursor.execute(f'select data from {MetricRecord._meta.db_table}')
            record = cursor.fetchone()
            self.assertEqual(record[0], data)
