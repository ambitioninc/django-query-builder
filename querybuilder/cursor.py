import contextlib
import json
# from psycopg2.extras import register_default_jsonb
# from psycopg2._json import JSONB_OID

# constant for jsonb column type in postgressql - setting explicitly instead of pulling
# from psycopg2 in order to reduce reliance on it (so we can move towards psycopg3)
JSONB_OID = 3802


# def jsonify_cursor(django_cursor, enabled=True):
#     """
#     Adjust an already existing cursor to ensure it will return structured types (list or dict)
#     from jsonb columns instead of strings. Django 3.1.1+ returns strings for raw queries.
#     https://code.djangoproject.com/ticket/31956
#     https://code.djangoproject.com/ticket/31973
#     https://www.psycopg.org/docs/extras.html#psycopg2.extras.register_default_jsonb
#     """
#
#     # The thing that is returned by connection.cursor() is (normally) a Django object
#     # of type CursorWrapper that itself has the "real" cursor as a property called cursor.
#     # However, it could be a CursorDebugWrapper instead, or it could be an outer wrapper
#     # wrapping one of those. For example django-debug-toolbar wraps CursorDebugWrapper in
#     # a NormalCursorWrapper. The django-db-readonly package wraps the Django CursorWrapper
#     # in a ReadOnlyCursorWrapper. I'm not sure if they ever nest multiple levels. I tried
#     # looping with `while isinstance(inner_cursor, CursorWrapper)`, but it seems that the
#     # outer wrapper is not necessarily a subclass of the Django wrapper. My next best option
#     # is to make the assumption that we need to get to the last property called `cursor`,
#     # basically assuming that any wrapper is going to have a property called `cursor`
#     # that is the real cursor or the next-level wrapper.
#     # Another option might be to check the class of inner_cursor to see if it is the real
#     # database cursor. That would require importing more django libraries, and probably
#     # having to handle some changes in those libraries over different versions.
#
#     # This register_default_jsonb functionality in psycopg2 does not itself have a "deregister"
#     # capability. So to deregister, we pass in a different value for the loads method; in this
#     # case just the str() built-in, which just returns the value passed in. Note that passing
#     # None for loads does NOT do a deregister; it uses the default value, which as it turns out
#     # is json.loads anyway!
#     loads_func = json.loads if enabled else str
#
#     # We expect that there is always at least one wrapper, but we might as well handle
#     # the possibility that we get passed the inner cursor.
#     inner_cursor = django_cursor
#
#     while hasattr(inner_cursor, 'cursor'):
#         inner_cursor = inner_cursor.cursor
#
#     # Hopefully we have the right thing now, but try/catch so we can get a little better info
#     # if it is not. Another option might be an isinstance, or another function that tests the cursor?
#     try:
#         register_default_jsonb(conn_or_curs=inner_cursor, loads=loads_func)
#     except TypeError as e:
#         raise Exception(f'jsonify_cursor: conn_or_curs was actually a {type(inner_cursor)}: {e}')
#
#
# def dejsonify_cursor(django_cursor):
#     """
#     Re-adjust a cursor that was "jsonified" so it no longer performs the json.loads().
#     """
#     jsonify_cursor(django_cursor, enabled=False)
#
#
# @contextlib.contextmanager
# def json_cursor(django_database_connection):
#     """
#     Cast json fields into their specific types to account for django bugs
#     https://code.djangoproject.com/ticket/31956
#     https://code.djangoproject.com/ticket/31973
#     https://www.psycopg.org/docs/extras.html#psycopg2.extras.register_default_jsonb
#     """
#     with django_database_connection.cursor() as cursor:
#         jsonify_cursor(cursor)
#         yield cursor
#         # This should really not be necessary, because the cursor context manager will
#         # be closing the cursor on __exit__ anyway. But just in case.
#         dejsonify_cursor(cursor)
#

def json_fetch_all_as_dict(cursor):
    """
    Iterates over a result set and converts each row to a dictionary.
    The cursor passed in is assumed to have just executed a raw Postgresql query.
    If the cursor's columns include any with the jsonb type, the process includes
    examining every value from those columns. If the value is a string, a json.loads()
    is attempted on the value, because in Django 3.1.1 and later, this is not
    handled automatically for raw sql as it was before. There is no compatibility
    issue running with older Django versions because if the value is not a string,
    (e.g. it has already been converted to a list or dict), the loads() is skipped.
    Note that JSON decoding errors are ignored (and the original result value is provided)
    because it is possible that the query involved an actual json query, say on a single
    string property of the underlying column data. In that case, the column type is
    still jsonb, but the result value is a string as it should be. This ignoring of
    errors is the same logic used in json handling in Django's from_db_value() method.

    :return: A list of dictionaries where each row is a dictionary
    :rtype: list of dict
    """

    colnames = [col.name for col in cursor.description]
    coltypes = [col.type_code for col in cursor.description]
    # Identify any jsonb columns in the query, by column index
    jsonbcols = [i for i, x in enumerate(coltypes) if x == JSONB_OID]

    # Optimize with a simple comprehension if we know there are no jsonb columns to handle.
    if not jsonbcols:
        return [
            dict(zip(colnames, row))
            for row in cursor.fetchall()
        ]

    # If there are jsonb columns, intercept the result rows and run a json.loads() on any jsonb
    # columns that are presenting as strings.
    # In Django 3.1.0 they would already be a json type (e.g. dict or list) but in Django 3.1.1 it changes
    # and raw sql queries return strings for jsonb columns.
    # https://docs.djangoproject.com/en/4.0/releases/3.1.1/
    results = []

    for row in cursor.fetchall():
        rowvals = list(row)
        for colindex in jsonbcols:
            if type(rowvals[colindex]) is str:  # need to check type to avoid attempting to jsonify a None
                try:
                    rowvals[colindex] = json.loads(rowvals[colindex])
                # It is possible that we are selecting a sub-value from the json in the column. I.e.
                # we got here because it IS a jsonb column, but what we selected is not json and will
                # fail to parse. In that case, we already have the value we want in place.
                except json.JSONDecodeError:
                    pass
        results.append(dict(zip(colnames, rowvals)))
    return results
