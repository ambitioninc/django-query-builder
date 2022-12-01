import contextlib
import json
import psycopg2


@contextlib.contextmanager
def json_cursor(django_database_connection):
    """
    Cast json fields into their specific types to account for django bugs
    https://code.djangoproject.com/ticket/31956
    https://code.djangoproject.com/ticket/31973
    https://www.psycopg.org/docs/extras.html#psycopg2.extras.register_default_jsonb
    """
    with django_database_connection.cursor() as cursor:
        psycopg2.extras.register_default_jsonb(conn_or_curs=cursor.cursor, loads=json.loads)
        yield cursor
