Usage Examples
==============

These examples are meant to provide some basic usage scenarios for what is possible with querybuilder. More advanced
examples will be added in the future.


Selecting records as dictionaries
---------------------------------

The simplest query is to just specify a table name to select from. By default, all fields ('*') will be used
for the field list.
Select all fields from a table:

.. code-block:: python

    from querybuilder.query import Query

    query = Query().from_table('account')
    query.select()
    # [{"id": 1, "name": "Person 1"}, {"id": 2, "name": "Person 2"}]
    query.get_sql()
    # "SELECT account.* FROM account"


If all fields are not needed, it is possible to specify fields by name.
Select specific fields:

.. code-block:: python

    from querybuilder.query import Query

    query = Query().from_table('account', ['name'])
    query.select()
    # [{"name": "Person 1"}, {"name": "Person 2"}]
    query.get_sql()
    # "SELECT account.name FROM account"


It is possible to use a django model class instead of a table name. This is not only more convenient, but it also
lets querybuilder know meta data about your table to do some automatic generation as seen in later examples.
Select from a django model:

.. code-block:: python

    from querybuilder.query import Query
    from querybuilder.tests.models import User

    query = Query().from_table(User)
    query.select()
    # [{"id": 1, "email": "user1@test.com"}, {"id": 2, "email": "user2@test.com"}]
    query.get_sql()
    # "SELECT tests_user.* FROM tests_user"


All of the fields can be explicitly selected by passing the extract_fields flag
Explicitly select all fields:

.. code-block:: python

    from querybuilder.query import Query
    from querybuilder.tests.models import User

    query = Query().from_table(User, extract_fields=True)
    query.select()
    # [{"id": 1, "email": "user1@test.com"}, {"id": 2, "email": "user2@test.com"}]
    query.get_sql()
    # "SELECT tests_user.id, tests_user.email FROM tests_user"


All tables, fields, and nested queries can be aliased so you can reference them by another name.
Alias a table and fields:

.. code-block:: python

    from querybuilder.query import Query

    query = Query().from_table({
        'my_table': User
    }, [{
        'the_id': 'id'
    }, {
        'the_email': 'email'
    }])
    query.select()
    # [{"the_id": 1, "the_email": "user1@test.com"}, {"the_id": 2, "the_email": "user2@test.com"}]
    query.get_sql()
    # "SELECT my_table.id AS the_id, my_table.email AS the_email FROM tests_user AS my_table"


Selecting from inner queries is just as simple as selecting from a table. The inner query can be aliased and
query builder with set up the nested queries using a WITH clause
Select from Query:

.. code-block:: python

    from querybuilder.query import Query
    from querybuilder.tests.models import User

    inner_query = Query().from_table(User)
    query = Query().from_table({
        'inner_query': inner_query
    })
    query.select()
    # [{"id": 1, "email": "user1@test.com"}, {"id": 2, "email": "user2@test.com"}]
    query.get_sql()
    # WITH inner_query AS (SELECT tests_user.* FROM tests_user) SELECT inner_query.* FROM inner_query

This simple example is meant to demonstrate that query nesting is possible, but the usefulness is really
demonstrated in the more complex examples.


Sorting
-------
Select all fields using a django model and order by id desc:

.. code-block:: python

    from querybuilder.query import Query

    query = Query().from_table(User).order_by('-id')
    query.select()
    # [{"id": 2, "email": "user2@test.com"}, {"id": 1, "email": "user1@test.com"}]
    query.get_sql()
    # "SELECT tests_user.* FROM tests_user ORDER BY id DESC"


Sort direction can also be specified by passing a flag:

.. code-block:: python

    from querybuilder.query import Query

    query = Query().from_table(User).order_by('id', desc=True)
    query.get_sql()
    # "SELECT tests_user.* FROM tests_user ORDER BY id DESC"


Limit and Offset
----------------
Limiting the result set is possible by specifying a limit value and an optional offset value

.. code-block:: python

    from querybuilder.query import Query

    query = Query().from_table(User).limit(1)
    query.select()
    # [{"id": 1, "email": "user1@test.com"}]
    query.get_sql()
    # "SELECT tests_user.* FROM tests_user LIMIT 1"

    query = Query().from_table(User).limit(1, 1)
    query.select()
    # [{"id": 2, "email": "user2@test.com"}]
    query.get_sql()
    # "SELECT tests_user.* FROM tests_user LIMIT 1, 1"


Filtering
---------
Specifying a where clause is similar to django's filtering system.

.. code-block:: python

    query = Query().from_table(User).where(id=1)
    query.select()
    # [{"id": 1, "email": "user1@test.com"}]
    query.get_sql()
    # "SELECT tests_user.* FROM tests_user WHERE (id = %(A0s)"
    query.get_args()
    # {'A0': 1}

The actual query arguments are passed into django's cursor.execute function to be escaped properly.

Multiple where clauses can be chained together, or multiple clauses can be passed to a single where call:

.. code-block:: python

    query = Query().from_table(User).where(id__eq=1, id__lt=5)
    query.get_sql()
    # SELECT tests_user.* FROM tests_user WHERE (id > %(A0)s AND id < %(A1)s)
    query.get_args()
    # {'A1': 5, 'A0': 1}

    query = Query().from_table(User).where(id__eq=1).where(id__lt=5)
    query.get_sql()
    # SELECT tests_user.* FROM tests_user WHERE (id > %(A0)s AND id < %(A1)s)
    query.get_args()
    # {'A1': 5, 'A0': 1}

By default, the conditions are ANDed together, but they can be ORed as well.

.. code-block:: python

    query = Query().from_table(User).where(id__eq=1).where(id__eq=5, where_type='OR')
    query.get_sql()
    # SELECT tests_user.* FROM tests_user WHERE ((id = %(A0)s) OR (id = %(A1)s))
    query.get_args()
    # {'A1': 5, 'A0': 1}

This is actually using django's Q object internally, so any complex Q object can be passed in as an argument

.. code-block:: python

    condition = Q(id=1) | Q(id=5)
    query = Query().from_table(User).where(condition)
    query.get_sql()
    # SELECT tests_user.* FROM tests_user WHERE ((id = %(A0)s) OR (id = %(A1)s))
    query.get_args()
    # {'A1': 5, 'A0': 1}


Other supported comparisons:
eq
gt
gte
lt
lte
contains
startswith


Aggregates
----------


Joins
-----


Date functions
--------------


Window functions
----------------


Inner queries
-------------

.. code-block:: python

    from querybuilder.query import Query

    inner_query = Query().from_table(Account)
    outer_query = Query().from_table(inner_query)

Connection Setup
----------------

Arbitrary django connections can be passed into the Query constructor to connect to alternate databases.

.. code-block:: python

    from django.db import connections
    from querybuilder.query import Query

    connections.all()
    #[<django.db.backends.postgresql_psycopg2.base.DatabaseWrapper at 0x1127b4390>,
    # <django.db.backends.postgresql_psycopg2.base.DatabaseWrapper at 0x1127b44d0>]

    Query(connections.all()[0]).from_table('auth_user').count()
    # 15L
    Query(connections.all()[1]).from_table('auth_user').count()
    # 223L

Reference Material
------------------
* http://www.postgresql.org/docs/9.1/static/functions-window.html
