import contextlib
import json
import psycopg2


def jsonify_cursor(django_cursor):
    """
    Adjust an already existing cursor to ensure it will return structured types (list or dict)
    from jsonb columns instead of strings. Django 3.1.1+ returns strings for raw queries.
    https://code.djangoproject.com/ticket/31956
    https://code.djangoproject.com/ticket/31973
    https://www.psycopg.org/docs/extras.html#psycopg2.extras.register_default_jsonb
    """

    # The thing that is returned by connection.cursor() is (normally) a Django object
    # of type CursorWrapper that itself has the "real" cursor as a property called cursor.
    # However, it could be a CursorDebugWrapper instead, or it could be an outer wrapper
    # wrapping one of those. For example django-debug-toolbar wraps CursorDebugWrapper in
    # a NormalCursorWrapper. The django-db-readonly package wraps the Django CursorWrapper
    # in a ReadOnlyCursorWrapper. I'm not sure if they ever nest multiple levels. I tried
    # looping with `while isinstance(inner_cursor, CursorWrapper)`, but it seems that the
    # outer wrapper is not necessarily a subclass of the Django wrapper. My next best option
    # is to make the assumption that we need to get to the last property called `cursor`,
    # basically assuming that any wrapper is going to have a property called `cursor`
    # that is the real cursor or the next-level wrapper.
    # Another option might be to check the class of inner_cursor to see if it is the real
    # database cursor. That would require importing more django libraries, and probably
    # having to handle some changes in those libraries over different versions.

    # We expect that there is always at least one wrapper, but we might as well handle
    # the possibility that we get passed the inner cursor.
    inner_cursor = django_cursor

    while hasattr(inner_cursor, 'cursor'):
        inner_cursor = inner_cursor.cursor

    # Hopefully we have the right thing now, but try/catch so we can get a little better info
    # if it is not. Another option might be an isinstance, or another function that tests the cursor?
    try:
        psycopg2.extras.register_default_jsonb(conn_or_curs=inner_cursor, loads=json.loads)
    except TypeError as e:
        raise Exception(f'jsonify_cursor: conn_or_curs was actually a {type(inner_cursor)}: {e}')


def dejsonify_cursor(django_cursor):
    """
    Re-adjust a cursor that was "jsonified" so it no longer performs the json.loads.
    """

    inner_cursor = django_cursor

    while hasattr(inner_cursor, 'cursor'):
        inner_cursor = inner_cursor.cursor

    # Hopefully we have the right thing now, but try/catch so we can get a little better info
    # if it is not. Another option might be an isinstance, or another function that tests the cursor?
    try:
        psycopg2.extras.register_default_jsonb(conn_or_curs=inner_cursor, loads=str)
    except TypeError as e:
        raise Exception(f'jsonify_cursor: conn_or_curs was actually a {type(inner_cursor)}: {e}')


@contextlib.contextmanager
def json_cursor(django_database_connection):
    """
    Cast json fields into their specific types to account for django bugs
    https://code.djangoproject.com/ticket/31956
    https://code.djangoproject.com/ticket/31973
    https://www.psycopg.org/docs/extras.html#psycopg2.extras.register_default_jsonb
    """
    with django_database_connection.cursor() as cursor:
        jsonify_cursor(cursor)
        yield cursor
        dejsonify_cursor(cursor)
