Usage Examples
==============

Selecting records as dictionaries
---------------------------------

Select all fields from a table:

.. code-block:: python

    from querybuilder.query import Query

    query = Query().from_table('account')
    query.select()
    # [{"id": 1, "name": "Person 1"}, {"id": 2, "name": "Person 2"}]
    query.get_sql()
    # "SELECT account.* FROM account"

== ========
id name
== ========
1  Person 1
2  Person 2
== ========

Alias a table and fields:

.. code-block:: python

    from querybuilder.query import Query

    query = Query().from_table(
        table={
            'my_table': Account
        },
        fields=[{
            'the_id': 'id'
        }, {
            'the_name': 'name'
        }]
    )
    query.select()
    # [{"the_id": 1, "the_name": "Person 1"}, {"the_id": 2, "the_name": "Person 2"}]
    query.get_sql()
    # "SELECT my_table.id AS the_id, my_table.name AS the_name FROM account AS my_table"

====== ========
the_id the_name
====== ========
1      Person 1
2      Person 2
====== ========



Selecting records as models
---------------------------
Select all fields from a table:

.. code-block:: python

    from querybuilder.query import Query

    query = Query().from_table('account')
    query.select(return_models=True)
    # [<Account: Account object>, <Account: Account object>]
    query.get_sql()
    # "SELECT account.* FROM account"


Sorting
-------
Select all fields using a django model and order by id desc:

.. code-block:: python

    from querybuilder.query import Query

    query = Query().from_table(Account).order_by('-id')
    query.select()
    # [{"id": 2, "name": "Person 2"}, {"id": 1, "name": "Person 1"}]
    query.get_sql()
    # "SELECT account.* FROM account ORDER BY id DESC"

== ========
id name
== ========
2  Person 2
1  Person 1
== ========

Limit and Offset
----------------
Select specific fields and sort with a limit:

.. code-block:: python

    from querybuilder.query import Query

    query = Query().from_table(
        table=Account,
        fields=['name']
    ).order_by(
        '-id'
    ).limit(
        1
    )
    query.select()
    # [{"name": "Person 2"}]
    query.get_sql()
    # "SELECT account.* FROM account ORDER BY id DESC LIMIT 1"

+----------+
| name     |
+==========+
| Person 2 |
+----------+

Filtering
---------
eq
gt
gte
lt
lte
~
&
|
contains
startswith

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

Reference Material
------------------
* http://www.postgresql.org/docs/9.1/static/functions-window.html
