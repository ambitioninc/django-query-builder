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


A field object can also be passed in the field list so any other field options can be included. This is especially
useful for custom fields, aggregates, and date part fields.

.. code-block:: python

    query = Query().from_table(User, [
        SimpleField('id', alias='the_id'),
        {'the_email': SimpleField('email')}
    ])
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


Fields
------
All fields in querybuilder inherit from the base Field class. Some field types like SimpleField only have a name
specified, but more complex fields like aggregates and date parts provide much more functionality. Custom fields
can easily be created by extending one of these field classes as demonstrated later in the examples.


Aggregates
----------
A full list of available fields is available in the Field API documentation. Some more examples are in the
field_tests.py file. Some more examples will be added to demonstrate why these are useful. To become more familiar
with window functions and how these are used, check out the postgres docs
http://www.postgresql.org/docs/9.3/static/functions-window.html

.. code-block:: python

    query = Query().from_table(Order, [SumField('revenue')])
    query.get_sql()
    # SELECT SUM(tests_order.revenue) AS revenue_sum FROM tests_order

    query = Query().from_table(Order, ['*', RowNumberField('revenue', over=QueryWindow().order_by('margin'))])
    query.get_sql()
    # SELECT tests_order.*, ROW_NUMBER() OVER (ORDER BY margin ASC) AS revenue_row_number FROM tests_order

    query = Query().from_table(
        Order,
        ['*', RowNumberField('revenue', over=QueryWindow().order_by('margin').partition_by('account_id'))]
    )
    query.get_sql()
    # SELECT tests_order.*, ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY margin ASC) AS revenue_row_number
    # FROM tests_order




CustomFields
------------
It is possible to create your own custom field and use it in a query by extending a field class.

.. code-block:: python

    class MultiplyField(MultiField):
        def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, multiply_by=1):
            super(MultiplyField, self).__init__(field, table, alias, cast, distinct)
            self.multiply_by = multiply_by
            self.auto_alias = '{0}_{1}'.format(self.field.name, 'mult')

        def get_select_sql(self):
            return '({0}*{1})'.format(self.get_field_identifier(), self.multiply_by)

    query = Query().from_table(Order, ['revenue', MultiplyField('revenue', multiply_by=2)])
    query.get_sql()
    # SELECT tests_order.revenue, (tests_order.revenue*2) AS revenue_mult FROM tests_order


Date functions
--------------
Several date part functions exist in order to extract date parts (year, month, day, hour, minute, second).

.. code-block:: python

    query = Query().from_table(Order, [Day('time')])
    query.get_sql()
    # SELECT CAST(EXTRACT(day FROM tests_order.time) AS INT) AS time__day FROM tests_order
    query.select()
    # [{'time__day': 19}, {'time__day': 19}, {'time__day': 19}, {'time__day': 19}]


A more useful way to use these functions is to pass the auto=True flag. This is used if you want to group records
by specific date parts. Normally, to group by day, you would have to extract year, month, and day then group by
year, month, and day in addition to any other grouping criteria.

.. code-block:: python

    query = Query().from_table(Order, [SumField('revenue'), Day('time', auto=True)])
    query.get_sql()
    # SELECT SUM(tests_order.revenue) AS revenue_sum,
    # CAST(EXTRACT(year FROM tests_order.time) AS INT) AS time__year,
    # CAST(EXTRACT(month FROM tests_order.time) AS INT) AS time__month,
    # CAST(EXTRACT(day FROM tests_order.time) AS INT) AS time__day,
    # CAST(EXTRACT(epoch FROM date_trunc('day', tests_order.time)) AS INT) AS time__epoch
    # FROM tests_order GROUP BY time__year, time__month, time__day, time__epoch ORDER BY time__epoch ASC
    query.select()
    # [{'time__day': 19, 'time__month': 10, 'revenue_sum': 1800.0, 'time__year': 2012, 'time__epoch': 1350604800}]


Providing additional grouping criteria is simple. Let's say you want to see this data grouped per account:

.. code-block:: python

    query = Query().from_table(Order, ['account_id', SumField('revenue'), Day('time', auto=True)]).group_by('account_id')
    query.get_sql()
    # SELECT tests_order.account_id,
    # SUM(tests_order.revenue) AS revenue_sum,
    # CAST(EXTRACT(year FROM tests_order.time) AS INT) AS time__year,
    # CAST(EXTRACT(month FROM tests_order.time) AS INT) AS time__month,
    # CAST(EXTRACT(day FROM tests_order.time) AS INT) AS time__day,
    # CAST(EXTRACT(epoch FROM date_trunc('day', tests_order.time)) AS INT) AS time__epoch
    # FROM tests_order GROUP BY time__year, time__month, time__day, time__epoch, account_id ORDER BY time__epoch ASC
    query.select()
    # [
    #     {'account_id': 1, 'time__day': 19, 'time__month': 10, 'time__year': 2012, 'time__epoch': 1350604800, 'revenue_sum': 300.0},
    #     {'account_id': 2, 'time__day': 19, 'time__month': 10, 'time__year': 2012, 'time__epoch': 1350604800, 'revenue_sum': 1500.0}
    # ]


Going off of this same example, lets say you wanted to rank the accounts:

.. code-block:: python

    query = Query().from_table(Order, ['account_id', SumField('revenue'), Day('time', auto=True)]).group_by('account_id')
    rank_query = Query().from_table(query, ['account_id', RankField(over=QueryWindow().order_by('-revenue_sum'))])
    rank_query.get_sql()
    # WITH T0 AS (
    # SELECT tests_order.account_id,
    # SUM(tests_order.revenue) AS revenue_sum,
    # CAST(EXTRACT(year FROM tests_order.time) AS INT) AS time__year,
    # CAST(EXTRACT(month FROM tests_order.time) AS INT) AS time__month,
    # CAST(EXTRACT(day FROM tests_order.time) AS INT) AS time__day,
    # CAST(EXTRACT(epoch FROM date_trunc('day', tests_order.time)) AS INT) AS time__epoch
    # FROM tests_order
    # GROUP BY time__year, time__month, time__day, time__epoch, account_id
    # ORDER BY time__epoch ASC)
    # SELECT T0.account_id, RANK() OVER (ORDER BY revenue_sum DESC) AS rank FROM T0
    rank_query.select()
    # [{'account_id': 2, 'rank': 1L}, {'account_id': 1, 'rank': 2L}]

This obviously is not an efficient query for large data sets, but it can be convenient in many cases.


Joins
-----

Json Fields
-----------
Filtering and ordering by json fields is currently in an experimental phase.

Queryset example:

.. code-block:: python
    from querybuilder.query import JsonQueryset

    records = JsonQueryset(model=MetricRecord).filter(**{'data->field_name': 'my_value'}).order_by('data->my_sort_field')

Custom field example:

.. code-block:: python
    from querybuilder.fields import JsonField

    my_field = JsonField('data', key='field_name', alias='my_field_alias')
    query = Query().from_table(MetricRecord, fields=[my_field]).where(**{
        my_field.get_where_key(): 'my_value'
    })


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
* http://www.postgresql.org/docs/9.3/static/functions-window.html
