import json

# constant for jsonb column type in postgressql - setting explicitly instead of pulling
# from psycopg2 in order to reduce reliance on it (so we can move towards psycopg3)
JSONB_OID = 3802


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