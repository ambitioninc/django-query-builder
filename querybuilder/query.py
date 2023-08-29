from copy import deepcopy

from django import VERSION
from django.db import connection as default_django_connection
from django.db.models import Q, AutoField
from django.db.models.query import QuerySet
from django.db.models.constants import LOOKUP_SEP
from django.apps import apps
get_model = apps.get_model
import six

from querybuilder.fields import FieldFactory, CountField, MaxField, MinField, SumField, AvgField
from querybuilder.helpers import set_value_for_keypath, copy_instance
from querybuilder.tables import TableFactory, ModelTable, QueryTable
from querybuilder.utils import json_fetch_all_as_dict


SERIAL_DTYPES = ['serial', 'bigserial']


class Join(object):
    """
    Represents the JOIN clauses of a Query. The join can be of any join type.
    """

    def __init__(self, right_table=None, fields=None, condition=None, join_type='JOIN',
                 schema=None, left_table=None, owner=None, extract_fields=True,
                 prefix_fields=True, field_prefix=None):
        """
        Initializes the default values and assigns any passed params

        :param right_table: The table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance
        :type right_table: str or dict or :class:`Table <querybuilder.tables.Table>`

        :param fields: The fields to select from ``table``. Defaults to None. This can be
            a single field, a tuple of fields, or a list of fields. Each field can be a string
            or ``Field`` instance
        :type fields: str or tuple or list or :class:`Field <querybuilder.fields.Field>`

        :param condition: The join condition specifying the fields being joined. If the two tables being
            joined are instances of ``ModelTable`` then the condition should be created automatically.
        :type condition: str

        :param join_type: The type of join (JOIN, LEFT JOIN, INNER JOIN, etc). Defaults to 'JOIN'
        :type join_type: str

        :param schema: This is not implemented, but it will be a string of the db schema name
        :type schema: str

        :param left_table: The left table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance. Defaults to the first table
            in the query.
        :type left_table: str or dict or :class:`Table <querybuilder.tables.Table>` or None

        :param owner: A reference to the query managing this Join object
        :type owner: :class:`Query <querybuilder.query.Query>`

        :param extract_fields: If True and joining with a ``ModelTable``, then '*'
            fields will be converted to individual fields for each column in the table. Defaults
            to True.
        :type extract_fields: bool

        :param prefix_fields: If True, then the joined table will have each of its field names
            prefixed with the field_prefix. If no field_prefix is specified, a name will be
            generated based on the join field name. This is usually used with nesting results
            in order to create models in python or javascript. Defaults to True.
        :type prefix_fields: bool

        :param field_prefix: The field prefix to be used in front of each field name if prefix_fields
            is set to True. If no field_prefix is set, one will be automatically created based on
            the join field name.
        :type field_prefix: str
        """
        self.owner = owner
        self.left_table = None
        self.right_table = None
        # self.table_join_name = None
        self.prefix_fields = prefix_fields
        self.condition = condition
        self.join_type = join_type
        self.schema = schema

        self.set_left_table(left_table=left_table)
        self.set_right_table(TableFactory(
            table=right_table,
            fields=fields,
            extract_fields=extract_fields,
            prefix_fields=prefix_fields,
            owner=self.owner,
            field_prefix=field_prefix,
        ))

    def get_sql(self):
        """
        Generates the JOIN sql for the join tables and join condition

        :rtype: str
        :return: the JOIN sql for the join tables and join condition
        """
        return '{0} {1} ON {2}'.format(self.join_type, self.right_table.get_sql(), self.get_condition())

    def set_left_table(self, left_table=None):
        """
        Sets the left table for this join clause. If no table is specified, the first table
        in the query will be used

        :type left_table: str or dict or :class:`Table <querybuilder.tables.Table>` or None
        :param left_table: The left table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance. Defaults to the first table
            in the query.
        """
        if left_table:
            self.left_table = TableFactory(
                table=left_table,
                owner=self.owner,
            )
        else:
            self.left_table = self.get_left_table()

    def get_left_table(self):
        """
        Returns the left table if one was specified, otherwise the first
        table in the query is returned

        :rtype: :class:`Table <querybuilder.tables.Table>`
        :return: the left table if one was specified, otherwise the first table in the query
        """
        if self.left_table:
            return self.left_table
        if len(self.owner.tables):
            return self.owner.tables[0]

    def get_all_related_objects(self, table):
        """
        Fix for django 1.10 to replace deprecated code. Keep support for django 1.7
        """
        # Django 1.7 method
        if hasattr(table.model._meta, 'get_all_related_objects'):
            return table.model._meta.get_all_related_objects()
        else:
            # Django > 1.7
            return [
                f for f in table.model._meta.get_fields()
                if (f.one_to_many or f.one_to_one) and f.auto_created and not f.concrete
            ]

    def set_right_table(self, table):
        """
        Sets the right table for this join clause and try to automatically set the condition
        if one isn't specified
        """
        self.right_table = table
        if self.left_table is None:
            return

        # find table prefix
        if type(self.left_table) is ModelTable and type(self.right_table) is ModelTable:
            # loop through fields to find the field for this model

            # check if this join type is for a related field
            for field in self.get_all_related_objects(self.left_table):
                related_model = field.model
                if hasattr(field, 'related_model'):
                    related_model = field.related_model
                if related_model == self.right_table.model:
                    if self.right_table.field_prefix is None:
                        self.right_table.field_prefix = field.get_accessor_name()
                        if len(self.right_table.field_prefix) > 4 and self.right_table.field_prefix[-4:] == '_set':
                            self.right_table.field_prefix = self.right_table.field_prefix[:-4]
                    return

            # check if this join type is for a foreign key
            for field in self.left_table.model._meta.fields:
                if (
                    field.get_internal_type() == 'OneToOneField' or field.get_internal_type() == 'ForeignKey'
                ):
                    if field.remote_field.model == self.right_table.model:
                        if self.right_table.field_prefix is None:
                            self.right_table.field_prefix = field.name
                        return

    def get_condition(self):
        """
        Determines the condition to be used in the condition part of the join sql.

        :return: The condition for the join clause
        :rtype: str or None
        """
        if self.condition:
            return self.condition

        if type(self.right_table) is ModelTable and type(self.right_table) is ModelTable:
            # loop through fields to find the field for this model

            # check if this join type is for a related field
            for field in self.get_all_related_objects(self.right_table):
                related_model = field.model
                if hasattr(field, 'related_model'):
                    related_model = field.related_model
                if related_model == self.left_table.model:
                    table_join_field = field.field.column
                    # self.table_join_name = field.get_accessor_name()
                    condition = '{0}.{1} = {2}.{3}'.format(
                        self.right_table.get_identifier(),
                        self.right_table.model._meta.pk.name,
                        self.left_table.get_identifier(),
                        table_join_field,
                    )
                    return condition

            # check if this join type is for a foreign key
            for field in self.right_table.model._meta.fields:
                if (
                    field.get_internal_type() == 'OneToOneField' or field.get_internal_type() == 'ForeignKey'
                ):
                    if field.remote_field.model == self.left_table.model:
                        table_join_field = field.column
                        # self.table_join_name = field.name
                        condition = '{0}.{1} = {2}.{3}'.format(
                            self.right_table.get_identifier(),
                            table_join_field,
                            self.left_table.get_identifier(),
                            self.left_table.model._meta.pk.name
                        )
                        return condition
        return None


# TODO: make an expression table and expression field maybe
class Expression(object):

    def __init__(self, str):
        self.str = str


class Where(object):
    """
    Represents the WHERE clause of a Query. The filter data is contained inside of django
    Q objects and methods are provided to interface with them.

    Properties:

        arg_index: int
            The numeric index that is automatically assigned to query parameters

        arg_prefix: str
            A prefix for the arg names used to namespace inner queries. This is set
            by the Query object

        args: dict
            A dictionary mapping the arg keys to the actual values. This is the data
            that is passed into cursor.execute

        wheres: Q
            A django Q object that can contain many nested Q objects that are used to
            determine all of the where conditions and nested where conditions
    """

    comparison_map = {
        'exact': '=',
        'eq': '=',
        'gt': '>',
        'gte': '>=',
        'lt': '<',
        'lte': '<=',
        'contains': 'LIKE',
        'icontains': 'ILIKE',
        'startswith': 'LIKE',
        'in': 'IN',
    }

    def __init__(self):
        """
        Initializes default variables
        """
        self.arg_index = 0
        self.arg_prefix = ''
        self.args = {}
        self.wheres = Q()

    def get_sql(self):
        """
        Builds and returns the WHERE portion of the sql

        :return: the WHERE portion of the sql
        :rtype: str
        """
        # reset arg index and args
        self.arg_index = 0
        self.args = {}

        # build the WHERE sql portion if needed
        if len(self.wheres):
            where = self.build_where_part(self.wheres)
            return 'WHERE {0} '.format(where)
        return ''

    def get_condition_operator(self, operator):
        """
        Gets the comparison operator from the Where class's comparison_map

        :return: the comparison operator from the Where class's comparison_map
        :rtype: str
        """
        return Where.comparison_map.get(operator, None)

    def get_condition_value(self, operator, value):
        """
        Gets the condition value based on the operator and value

        :param operator: the condition operator name
        :type operator: str
        :param value: the value to be formatted based on the condition operator
        :type value: object

        :return: the comparison operator from the Where class's comparison_map
        :rtype: str
        """
        if operator in ('contains', 'icontains'):
            value = '%{0}%'.format(value)
        elif operator == 'startswith':
            value = '{0}%'.format(value)
        return value

    def build_where_part(self, wheres):
        """
        Recursive method that builds the where parts. Any Q objects that have children will
        also be built with ``self.build_where_part()``

        :rtype: str
        :return: The composed where string
        """
        where_parts = []

        # loop through each child of the Q condition
        for where in wheres.children:

            # if this child is another Q object, recursively build the where part
            if type(where) is Q:
                where_parts.append(self.build_where_part(where))
            elif type(where) is tuple:
                # build the condition for this where part
                # get the field name and value
                field_name = where[0]
                value = where[1]

                # set the default operator
                operator_str = 'eq'
                operator = '='

                # break apart the field name on double underscores
                field_parts = field_name.split('__')
                if len(field_parts) > 1:
                    # get the operator based on the last element split from the double underscores
                    operator_str = field_parts[-1]
                    operator = self.get_condition_operator(operator_str)
                    if operator is None:
                        operator = '='
                        field_name = '__'.join(field_parts)
                    else:
                        field_name = '__'.join(field_parts[:-1])

                # check if we are comparing to null
                if value is None:
                    # change the operator syntax to IS
                    operator = 'IS'

                # set up the condition string format
                condition = '{0} {1} ?'.format(field_name, operator)

                # apply the NOT if this condition is negated
                if wheres.negated:
                    condition = 'NOT({0})'.format(condition)

                # check if this value is multiple values
                if operator_str == 'in':

                    # make sure value is a list
                    if type(value) is not list:

                        # convert to string in case it is a number
                        value = str(value)

                        # split on commas
                        value = value.split(',')

                    # Ensure that we have a value in the list
                    if len(value) == 0:
                        value = [None]

                    if type(value) is Expression:
                        condition = condition.replace('?', value.str)
                    else:
                        # assign each query param to a named arg
                        named_args = []
                        for value_item in value:
                            named_arg = self.set_arg(value_item)
                            named_args.append('%({0})s'.format(named_arg))
                        # replace the ? in the query with the arg placeholder
                        condition = condition.replace('?', '({0})'.format(','.join(named_args)), 1)
                else:
                    # get the value based on the operator
                    value = self.get_condition_value(operator_str, value)

                    if type(value) is Expression:
                        condition = condition.replace('?', value.str)
                    else:
                        named_arg = self.set_arg(value)
                        # replace the ? in the query with the arg placeholder
                        condition = condition.replace('?', '%({0})s'.format(named_arg), 1)

                # add the condition to the where sql
                where_parts.append(condition)

        # join all where parts together
        joined_parts = ' {0} '.format(wheres.connector).join(where_parts)

        # wrap the where parts in parentheses
        return '({0})'.format(joined_parts)

    def set_arg(self, value):
        """
        Set the query param in self.args based on the prefix and arg index
        and auto increment the arg_index

        :return: the string placeholder for the arg
        :rtype: str
        """
        named_arg = '{0}A{1}'.format(self.arg_prefix, self.arg_index)
        self.args[named_arg] = value
        self.arg_index += 1
        return named_arg


class Group(object):
    """
    Represents a group by clause used in a Query
    """

    def __init__(self, field=None, table=None):
        """
        :param field: This can be a string of a field name, a dict of {'alias': field}, or
            a ``Field`` instance
        :type field: str or dict or :class:`Field <querybuilder.fields.Field>`

        :param table: Optional. This can be a string of a table name, a dict of {'alias': table}, or
            a ``Table`` instance. A table only needs to be supplied in more complex queries where
            the field name is ambiguous.
        :type table: str or dict or :class:`Table <querybuilder.tables.Table>`
        """
        self.field = FieldFactory(field)
        self.table = TableFactory(table)
        if self.table and self.field.table is None:
            self.field.set_table(self.table)

    def get_name(self):
        """
        Gets the name to reference the grouped field

        :return: the name to reference the grouped field
        :rtype: str
        """
        return self.field.get_identifier()


class Sorter(object):
    """
    Used internally by the Query class to set ORDER BY clauses on the query.
    """

    def __init__(self, field=None, table=None, desc=False):
        """
        Initializes the instance variables

        :type field: str or dict or :class:`Field <querybuilder.fields.Field>`
        :param field: This can be a string of a field name, a dict of {'alias': field}, or
            a ``Field`` instance

        :type table: str or dict or :class:`Table <querybuilder.tables.Table>`
        :param table: Optional. This can be a string of a table name, a dict of {'alias': table}, or
            a ``Table`` instance. A table only needs to be supplied in more complex queries where
            the field name is ambiguous.

        :param desc: Set to True to sort by this field in DESC order or False to sort by this field
            in ASC order. Defaults to False.
        :type desc: bool
        """
        self.desc = desc
        self.field = FieldFactory(field)
        self.table = TableFactory(table)

        # if the field is not associated with a table but a table was
        # passed in, set the field's table to the passed table
        if self.table and self.field.table is None:
            self.field.set_table(self.table)

        # if the specified field is a string with '-' at the beginning
        # the '-' needs to be removed and this sorter needs to be
        # set to desc
        if isinstance(self.field.field, six.string_types) and str(self.field.field[0]) == '-':
            self.desc = True
            self.field.field = self.field.field[1:]
            self.field.name = self.field.name[1:]

    def get_name(self, use_alias=True):
        """
        Gets the name to reference the sorted field

        :return: the name to reference the sorted field
        :rtype: str
        """
        if self.desc:
            direction = 'DESC'
        else:
            direction = 'ASC'

        if use_alias:
            return '{0} {1}'.format(self.field.get_identifier(), direction)
        return '{0} {1}'.format(self.field.get_select_sql(), direction)


class Limit(object):
    """
    Used internally by the Query class to set a limit and/or offset on the query.
    """

    def __init__(self, limit=None, offset=None):
        """
        Initializes the instance variables

        :param limit: the number of rows to return
        :type limit: int

        :param offset: the number of rows to start returning rows from
        :type limit: int
        """
        self.limit = limit
        self.offset = offset

    def get_sql(self):
        """
        Generates the sql used for the limit clause of a Query

        :return: the sql for the limit clause of a Query
        :rtype: str
        """
        sql = ''
        if self.limit and self.limit > 0:
            sql += 'LIMIT {0} '.format(self.limit)
        if self.offset and self.offset > 0:
            sql += 'OFFSET {0} '.format(self.offset)
        return sql


class Query(object):
    """
    A Query instance represents an actual query that will be executed. It provides
    methods for selecting fields from tables, inner queries, joins, filtering,
    limiting, and sorting. Different types of queries can be executed, such as:
    select, update, delete, create, and explain.

    Properties:

        sql: str
            The query generated by calling ``self.get_sql()`` This is used for
            caching purposes.

        tables: list of Table
            A list of ``Table`` instances this query is selecting from

        joins: list of Join
            A list of ``Join`` instances this query is joining on

        _where: Where
            A ``Where`` instance containing filtering data for this query

        groups: list of Group
            A list of ``Group`` instances that determine the GROUP BY clause for this query

        sorters: list of Sorter
            A list of ``Sorter`` instances that determine the ORDER BY clause for this query

        _limit: Limit
            An instance of ``Limit`` This will only exist if a limit has been specified for the query

        table_prefix: str
            A ``str`` that determines how to prefix inner queries of this query

    """
    enable_safe_limit = False
    safe_limit = 1000

    def init_defaults(self):
        """
        Sets the default values for this instance
        """
        self.sql = ''
        self.tables = []
        self.joins = []
        self._where = Where()
        self.groups = []
        self.sorters = []
        self._limit = None
        self.table_prefix = ''
        self.is_inner = False
        self.with_tables = []
        self._distinct = False
        self.distinct_ons = []
        self.field_names = []
        self.field_names_pk = None
        self.values = []

    def __init__(self, connection=None):
        """
        Initializes this instance by calling ``self.init_defaults``

        :type connection: :class:`DatabaseWrapper <django:django.db.backends.BaseDatabaseWrapper>`
        :parameter connection: A Django database connection. This can be used to connect to
            databases other than your default database.

        .. code-block:: python

            from django.db import connections
            from querybuilder.query import Query

            Query(connections.all()[0]).from_table('auth_user').count()
            # 15L
            Query(connections.all()[1]).from_table('auth_user').count()
            # 223L

        """
        self.connection = connection or default_django_connection

        self.init_defaults()

    def get_cursor(self):
        """
        Get a cursor for the Query's connection

        :rtype: :class:`CursorDebugWrapper <django:django.db.backends.util.CursorDebugWrapper>`
        :returns: A database cursor
        """
        cursor = self.connection.cursor()
        # Do not set up the cursor in psycopg2 to run json.loads on jsonb columns here. Do it
        # right before we run a select, and then set it back after that.
        # jsonify_cursor(cursor)
        return cursor

    def from_table(self, table=None, fields='*', schema=None, **kwargs):
        """
        Adds a ``Table`` and any optional fields to the list of tables
        this query is selecting from.

        :type table: str or dict or :class:`Table <querybuilder.tables.Table>`
            or :class:`Query <querybuilder.query.Query>` or
            :class:`ModelBase <django:django.db.models.base.ModelBase>`
        :param table: The table to select fields from. This can be a string of the table
            name, a dict of {'alias': table}, a ``Table`` instance, a Query instance, or a
            django Model instance

        :type fields: str or tuple or list or Field
        :param fields: The fields to select from ``table``. Defaults to '*'. This can be
            a single field, a tuple of fields, or a list of fields. Each field can be a string
            or ``Field`` instance

        :type schema: str
        :param schema: This is not implemented, but it will be a string of the db schema name

        :param kwargs: Any additional parameters to be passed into the constructor of ``TableFactory``

        :return: self
        :rtype: :class:`Query <querybuilder.query.Query>`
        """
        # self.mark_dirty()

        self.tables.append(TableFactory(
            table=table,
            fields=fields,
            schema=schema,
            owner=self,
            **kwargs
        ))

        return self

    def insert_into(self, table=None, field_names=None, values=None, **kwargs):
        """
        Bulk inserts a list of values into a table

        :type table: str or dict or :class:`Table <querybuilder.tables.Table>`
            or :class:`Query <querybuilder.query.Query>` or :class:`ModelBase <django:django.db.models.base.ModelBase>`
        :param table: The table to select fields from. This can be a string of the table
            name, a dict of {'alias': table}, a ``Table`` instance, a Query instance, or a
            django Model instance

        :type field_names: list
        :param field_names: A list of ordered field names that relate to the data in the values list

        :type values: list of list
        :param values: A list each values list with the values in the same order as the field names

        :param kwargs: Any additional parameters to be passed into the constructor of ``TableFactory``

        :return: self
        :rtype: :class:`Query <querybuilder.query.Query>`
        """
        table = TableFactory(
            table=table,
            **kwargs
        )
        self.tables.append(table)

        self.field_names = field_names
        self.values = values

        return self

    def update_table(self, table=None, field_names=None, values=None, pk=None, **kwargs):
        """
        Bulk updates rows in a table

        :type table: str or dict or :class:`Table <querybuilder.tables.Table>`
            or :class:`Query <querybuilder.query.Query>` or :class:`ModelBase <django:django.db.models.base.ModelBase>`
        :param table: The table to select fields from. This can be a string of the table
            name, a dict of {'alias': table}, a ``Table`` instance, a Query instance, or a
            django Model instance

        :type field_names: list
        :param field_names: A list of ordered field names that relate to the data in the values list

        :type values: list of list
        :param values: A list each values list with the values in the same order as the field names

        :type pk: int
        :param pk: The name of the primary key in the table and field_names

        :param kwargs: Any additional parameters to be passed into the constructor of ``TableFactory``

        :rtype: :class:`Query <querybuilder.query.Query>`
        :return: self
        """
        table = TableFactory(
            table=table,
            **kwargs
        )
        self.tables.append(table)

        self.field_names = field_names
        self.values = values
        self.field_names_pk = pk

    # TODO: add docs
    # TODO: add tests for custom with clauses
    def with_query(self, query=None, alias=None):
        """

        :return: self
        :rtype: :class:`Query <querybuilder.query.Query>`
        """
        self.with_tables.append(TableFactory(query, alias=alias))
        return self

    def join(self, right_table=None, fields=None, condition=None, join_type='JOIN',
             schema=None, left_table=None, extract_fields=True, prefix_fields=False, field_prefix=None,
             allow_duplicates=False):
        """
        Joins a table to another table based on a condition and adds fields from the joined table
        to the returned fields.

        :type right_table: str or dict or :class:`Table <querybuilder.tables.Table>`
        :param right_table: The table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance

        :type fields: str or tuple or list or :class:`Field <querybuilder.fields.Field>`
        :param fields: The fields to select from ``right_table``. Defaults to `None`. This can be
            a single field, a tuple of fields, or a list of fields. Each field can be a string
            or ``Field`` instance

        :type condition: str
        :param condition: The join condition specifying the fields being joined. If the two tables being
            joined are instances of ``ModelTable`` then the condition should be created automatically.

        :type join_type: str
        :param join_type: The type of join (JOIN, LEFT JOIN, INNER JOIN, etc). Defaults to 'JOIN'

        :type schema: str
        :param schema: This is not implemented, but it will be a string of the db schema name

        :type left_table: str or dict or Table
        :param left_table: The left table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance. Defaults to the first table
            in the query.

        :type extract_fields: bool
        :param extract_fields: If True and joining with a ``ModelTable``, then '*'
            fields will be converted to individual fields for each column in the table. Defaults
            to True.

        :type prefix_fields: bool
        :param prefix_fields: If True, then the joined table will have each of its field names
            prefixed with the field_prefix. If not field_prefix is specified, a name will be
            generated based on the join field name. This is usually used with nesting results
            in order to create models in python or javascript. Defaults to True.

        :type field_prefix: str
        :param field_prefix: The field prefix to be used in front of each field name if prefix_fields
            is set to True. If no field_prefix is set, one will be automatically created based on
            the join field name.

        :rtype: :class:`Query <querybuilder.query.Query>`
        :return: self
        """
        # self.mark_dirty()
        # TODO: fix bug when joining from simple table to model table with no condition
        # it assumes left_table.model

        # if there is no left table, assume the query's first table
        # TODO: add test for auto left table to replace old auto left table
        # if left_table is None and len(self.tables):
        #     left_table = self.tables[0]

        # left_table = TableFactory(left_table)
        # right_table = TableFactory(right_table)

        # create the join item
        new_join_item = Join(
            left_table=left_table,
            right_table=right_table,
            fields=fields,
            condition=condition,
            join_type=join_type,
            schema=schema,
            owner=self,
            extract_fields=extract_fields,
            prefix_fields=prefix_fields,
            field_prefix=field_prefix,
        )

        # check if this table is already joined upon
        # TODO: add test for this
        if allow_duplicates is False:
            for join_item in self.joins:
                if join_item.right_table.get_identifier() == new_join_item.right_table.get_identifier():
                    if join_item.left_table.get_identifier() == new_join_item.left_table.get_identifier():
                        return self

        self.joins.append(new_join_item)

        return self

    def join_left(self, right_table=None, fields=None, condition=None, join_type='LEFT JOIN',
                  schema=None, left_table=None, extract_fields=True, prefix_fields=False,
                  field_prefix=None, allow_duplicates=False):
        """
        Wrapper for ``self.join`` with a default join of 'LEFT JOIN'

        :type right_table: str or dict or :class:`Table <querybuilder.tables.Table>`
        :param right_table: The table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance

        :type fields: str or tuple or list or :class:`Field <querybuilder.fields.Field>`
        :param fields: The fields to select from ``right_table``. Defaults to `None`. This can be
            a single field, a tuple of fields, or a list of fields. Each field can be a string
            or ``Field`` instance

        :type condition: str
        :param condition: The join condition specifying the fields being joined. If the two tables being
            joined are instances of ``ModelTable`` then the condition should be created automatically.

        :type join_type: str
        :param join_type: The type of join (JOIN, LEFT JOIN, INNER JOIN, etc). Defaults to 'JOIN'

        :type schema: str
        :param schema: This is not implemented, but it will be a string of the db schema name

        :type left_table: str or dict or :class:`Table <querybuilder.tables.Table>`
        :param left_table: The left table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance. Defaults to the first table
            in the query.

        :type extract_fields: bool
        :param extract_fields: If True and joining with a ``ModelTable``, then '*'
            fields will be converted to individual fields for each column in the table. Defaults
            to True.

        :type prefix_fields: bool
        :param prefix_fields: If True, then the joined table will have each of its field names
            prefixed with the field_prefix. If not field_prefix is specified, a name will be
            generated based on the join field name. This is usually used with nesting results
            in order to create models in python or javascript. Defaults to True.

        :type field_prefix: str
        :param field_prefix: The field prefix to be used in front of each field name if prefix_fields
            is set to True. If no field_prefix is set, one will be automatically created based on
            the join field name.

        :return: self
        :rtype: :class:`Query <querybuilder.query.Query>`
        """
        return self.join(
            right_table=right_table,
            fields=fields,
            condition=condition,
            join_type=join_type,
            schema=schema,
            left_table=left_table,
            extract_fields=extract_fields,
            prefix_fields=prefix_fields,
            field_prefix=field_prefix,
            allow_duplicates=allow_duplicates
        )

    def where(self, q=None, where_type='AND', **kwargs):
        """
        Adds a where condition as a Q object to the query's ``Where`` instance.

        :type q: :class:`Q <django:django.db.models.Q>`
        :param q: A django ``Q`` instance. This will be added to the query's ``Where`` object. If no
            Q object is passed, the kwargs will be examined for params to be added to Q objects

        :param where_type: str
        :param where_type: The connection type of the where condition ('AND', 'OR')

        :return: self
        :rtype: :class:`Query <querybuilder.query.Query>`
        """
        # self.mark_dirty()
        if q is not None:
            self._where.wheres.add(q, where_type)
        if len(kwargs):
            for key, value in kwargs.items():
                q = Q(**{
                    key: value
                })
                self._where.wheres.add(q, where_type)
        return self

    def group_by(self, field=None, table=None, allow_duplicates=False):
        """
        Adds a group by clause to the query by adding a ``Group`` instance to the query's
        groups list

        :type field: str or dict or :class:`Field <querybuilder.fields.Field>`
        :param field: This can be a string of a field name, a dict of {'alias': field}, or
            a ``Field`` instance

        :type table: str or dict or :class:`Table <querybuilder.table.Table>`
        :param table: Optional. This can be a string of a table name, a dict of {'alias': table}, or
            a ``Table`` instance. A table only needs to be supplied in more complex queries where
            the field name is ambiguous.

        :return: self
        :rtype: :class:`Query <querybuilder.query.Query>`
        """
        new_group_item = Group(
            field=field,
            table=table,
        )

        if allow_duplicates is False:
            for group_item in self.groups:
                if group_item.field.get_identifier() == new_group_item.field.get_identifier():
                    return self

        self.groups.append(new_group_item)

        return self

    def order_by(self, field=None, table=None, desc=False):
        """
        Adds an order by clause to the query by adding a ``Sorter`` instance to the query's
        sorters list

        :type field: str or dict or :class:`Field <querybuilder.fields.Field>`
        :param field: This can be a string of a field name, a dict of {'alias': field}, or
            a ``Field`` instance

        :type table: str or dict or :class:`Table <querybuilder.table.Table>`
        :param table: Optional. This can be a string of a table name, a dict of {'alias': table}, or
            a ``Table`` instance. A table only needs to be supplied in more complex queries where
            the field name is ambiguous.

        :type desc: bool
        :param desc: Set to True to sort by this field in DESC order or False to sort by this field
            in ASC order. Defaults to False.

        :rtype: :class:`Query <querybuilder.query.Query>`
        :return: self
        """
        self.sorters.append(Sorter(
            field=field,
            table=table,
            desc=desc
        ))
        return self

    def limit(self, limit=None, offset=None):
        """
        Sets a limit and/or offset to the query to limit the number of rows returned.

        :type limit: int
        :param limit: The number of rows to return

        :type offset: int
        :param offset: The offset from the start of the record set where rows should start being returned

        :rtype: :class:`Query <querybuilder.query.Query>`
        :return: self
        """
        self._limit = Limit(
            limit=limit,
            offset=offset
        )
        return self

    def distinct(self, use_distinct=True):
        """
        Adds a distinct clause to the query

        :type use_distinct: bool
        :param use_distinct: Whether or not to include the distinct clause

        :rtype: :class:`Query <querybuilder.query.Query>`
        :return: self
        """
        self._distinct = use_distinct
        return self

    def distinct_on(self, *fields):
        for field in fields:
            self.distinct_ons.append(FieldFactory(field))
        return self

    def check_name_collisions(self):
        """
        Checks if there are any tables referenced by the same identifier and updated the
        auto_alias accordingly. This is called when generating the sql for a query
        and should only be called internally.
        """
        table_index = 0
        table_names = {}
        for table in self.tables + self.with_tables:
            table_prefix = 'T{0}'.format(table_index)
            auto_alias = '{0}{1}'.format(self.table_prefix, table_prefix)

            identifier = table.get_identifier()
            if identifier is None or identifier in table_names:
                table.auto_alias = auto_alias
            table_names[identifier] = True

            # prefix inner query args and update self args
            if type(table) is QueryTable:
                table.query.prefix_args(auto_alias)
                table.query.table_prefix = auto_alias

            table_index += 1

    def prefix_args(self, prefix):
        """
        Adds an argument prefix to the query's ``Where`` object. This should only
        be called internally.
        """
        self._where.arg_prefix = prefix

    def get_sql(self, debug=False, use_cache=True):
        """
        Generates the sql for this query and returns the sql as a string.

        :type debug: bool
        :param debug: If True, the sql will be returned in a format that is easier to read and debug.
            Defaults to False

        :type use_cache: bool
        :param use_cache: If True, the query will returned the cached sql if it exists rather
            then generating the sql again. If False, the sql will be generated again. Defaults to True.

        :rtype: str
        :return: The generated sql for this query
        """
        # TODO: enable caching
        # if self.sql and use_cache and not debug:
        #     return self.sql

        # auto alias any naming collisions
        self.check_name_collisions()

        # if debugging, return the debug formatted sql
        if debug:
            return self.format_sql()

        # build each part of the query
        sql = ''
        sql += self.build_withs()
        sql += self.build_select_fields()
        sql += self.build_from_table()
        sql += self.build_joins()
        sql += self.build_where()
        sql += self.build_groups()
        sql += self.build_order_by()
        sql += self.build_limit()

        # remove any whitespace from the beginning and end of the sql
        self.sql = sql.strip()

        return self.sql

    def get_insert_sql(self, rows):
        field_names_sql = '({0})'.format(', '.join(self.get_field_names()))
        row_values = []
        sql_args = []
        for row in rows:
            placeholders = []
            for value in row:
                sql_args.append(value)
                placeholders.append('%s')
            row_values.append('({0})'.format(', '.join(placeholders)))
        row_values_sql = ', '.join(row_values)

        self.sql = 'INSERT INTO {0} {1} VALUES {2}'.format(
            self.tables[0].get_identifier(),
            field_names_sql,
            row_values_sql
        )

        return self.sql, sql_args

    def should_not_cast_value(self, field_object):
        """
        In Django 4.1 on PostgreSQL, AutoField, BigAutoField, and SmallAutoField are now created as identity
        columns rather than serial columns with sequences.
        """
        db_type = field_object.db_type(self.connection)
        if db_type in SERIAL_DTYPES:
            return True
        if (VERSION[0] == 4 and VERSION[1] >= 1) or VERSION[0] >= 5:
            if getattr(field_object, 'primary_key', None) and getattr(field_object, 'serialize', None) is False:
                return True
        return False

    def get_update_sql(self, rows):
        """
        Returns SQL UPDATE for rows ``rows``

        .. code-block:: sql

            UPDATE table_name
            SET
                field1 = new_values.field1
                field2 = new_values.field2
            FROM (
                VALUES
                    (1, 'value1', 'value2'),
                    (2, 'value1', 'value2')
            ) AS new_values (id, field1, field2)
            WHERE table_name.id = new_values.id;

        """
        field_names = self.get_field_names()
        pk = field_names[0]
        update_field_names = field_names[1:]

        num_columns = len(rows[0])
        if num_columns < 2:
            raise Exception('At least 2 fields must be passed to get_update_sql')

        all_null_indices = [
            all(row[index] is None for row in rows)
            for index in range(1, num_columns)
        ]

        field_names_sql = '({0})'.format(', '.join(field_names))

        row_values = []
        sql_args = []

        # Loop over each row and put the %s placeholder for each field
        for i, row in enumerate(rows):

            # Build a list of each field's placeholder
            placeholders = []

            # If this is the first row, add casting information so the db knows the field types
            if i == 0 and hasattr(self.tables[0], 'model'):
                for field_index, value in enumerate(row):
                    # Append the value
                    sql_args.append(value)

                    # Figure out how to cast it
                    field_object = self.tables[0].model._meta.get_field(field_names[field_index])
                    db_type = field_object.db_type(self.connection)

                    # Don't cast serial types
                    if self.should_not_cast_value(field_object):
                        placeholders.append('%s')
                    else:
                        # Cast the placeholder to the data type
                        placeholders.append('%s::{0}'.format(db_type))
            else:
                for value in row:
                    sql_args.append(value)
                    placeholders.append('%s')
            row_values.append('({0})'.format(', '.join(placeholders)))
        row_values_sql = ', '.join(row_values)

        # build field list for SET portion
        set_field_list = [
            '{0} = NULL'.format(field_name)
            if all_null_indices[idx] else '{0} = new_values.{0}'.format(field_name)
            for idx, field_name in enumerate(update_field_names)
        ]
        set_field_list_sql = ', '.join(set_field_list)

        self.sql = 'UPDATE {0} SET {1} FROM (VALUES {2}) AS new_values {3} WHERE {0}.{4} = new_values.{4}'.format(
            self.tables[0].get_identifier(),
            set_field_list_sql,
            row_values_sql,
            field_names_sql,
            pk
        )

        return self.sql, sql_args

    def get_upsert_sql(
        self,
        rows,
        unique_fields,
        update_fields,
        auto_field_name=None,
        only_insert=False,
        return_rows=True
    ):
        """
        Generates the postgres specific sql necessary to perform an upsert (ON CONFLICT)

        INSERT INTO table_name (field1, field2)
        VALUES (1, 'two')
        ON CONFLICT (unique_field) DO UPDATE SET field2 = EXCLUDED.field2;
        """
        ModelClass = self.tables[0].model

        # Use all fields except pk unless the uniqueness constraint is the pk field. Null pk field rows will be
        # excluded in the upsert method before calling this method
        all_fields = [field for field in ModelClass._meta.fields if field.column != auto_field_name]
        if auto_field_name in unique_fields and not only_insert:
            all_fields = [field for field in ModelClass._meta.fields]

        all_field_names = [field.column for field in all_fields]
        all_field_names_sql = ', '.join(all_field_names)

        # Convert field names to db column names
        unique_fields = [
            ModelClass._meta.get_field(unique_field)
            for unique_field in unique_fields
        ]
        update_fields = [
            ModelClass._meta.get_field(update_field)
            for update_field in update_fields
        ]

        unique_field_names_sql = ', '.join([
            field.column for field in unique_fields
        ])
        update_fields_sql = ', '.join([
            '{0} = EXCLUDED.{0}'.format(field.column)
            for field in update_fields
        ])

        row_values = []
        sql_args = []

        for row in rows:
            placeholders = []
            for field in all_fields:
                # Convert field value to db value
                # Use attname here to support fields with custom db_column names
                sql_args.append(field.get_db_prep_save(getattr(row, field.attname), self.connection))
                placeholders.append('%s')
            row_values.append('({0})'.format(', '.join(placeholders)))
        row_values_sql = ', '.join(row_values)

        if update_fields:
            self.sql = 'INSERT INTO {0} ({1}) VALUES {2} ON CONFLICT ({3}) DO UPDATE SET {4} {5}'.format(
                self.tables[0].get_identifier(),
                all_field_names_sql,
                row_values_sql,
                unique_field_names_sql,
                update_fields_sql,
                'RETURNING *' if return_rows else ''
            )
        else:
            self.sql = 'INSERT INTO {0} ({1}) VALUES {2} ON CONFLICT ({3}) {4} {5}'.format(
                self.tables[0].get_identifier(),
                all_field_names_sql,
                row_values_sql,
                unique_field_names_sql,
                'DO UPDATE SET {0}=EXCLUDED.{0}'.format(unique_fields[0].column),
                'RETURNING *' if return_rows else ''
            )

        return self.sql, sql_args

    def format_sql(self):
        """
        Builds the sql in a format that is easy for humans to read and debug

        :return: The formatted sql for this query
        :rtype: str
        """
        # TODO: finish adding the other parts of the sql generation
        sql = ''

        # build SELECT
        select_segment = self.build_select_fields()
        select_segment = select_segment.replace('SELECT ', '', 1)
        fields = [field.strip() for field in select_segment.split(',')]
        sql += 'SELECT\n\t{0}\n'.format(',\n\t'.join(fields))

        # build FROM
        from_segment = self.build_from_table()
        from_segment = from_segment.replace('FROM ', '', 1)
        tables = [table.strip() for table in from_segment.split(',')]
        sql += 'FROM\n\t{0}\n'.format(',\n\t'.join(tables))

        # build ORDER BY
        order_by_segment = self.build_order_by()
        if len(order_by_segment):
            order_by_segment = order_by_segment.replace('ORDER BY ', '', 1)
            sorters = [sorter.strip() for sorter in order_by_segment.split(',')]
            sql += 'ORDER BY\n\t{0}\n'.format(',\n\t'.join(sorters))

        # build LIMIT
        limit_segment = self.build_limit()
        if len(limit_segment):
            if 'LIMIT' in limit_segment:
                limit_segment = limit_segment.replace('LIMIT ', 'LIMIT\n\t', 1)
                if 'OFFSET' in limit_segment:
                    limit_segment = limit_segment.replace('OFFSET ', '\nOFFSET\n\t', 1)
            elif 'OFFSET' in limit_segment:
                limit_segment = limit_segment.replace('OFFSET ', 'OFFSET\n\t', 1)
            sql += limit_segment

        return sql

    def get_field_names(self):
        """
        Builds a list of the field names for all tables and joined tables by calling
        ``get_field_names()`` on each table

        :return: list of field names
        :rtype: list of str
        """
        field_names = []
        for table in self.tables:
            field_names.extend(table.get_field_names())
        for join_item in self.joins:
            field_names.extend(join_item.right_table.get_field_names())
        return field_names

    def get_field_identifiers(self):
        """
        Builds a list of the field identifiers for all tables and joined tables by calling
        ``get_field_identifiers()`` on each table

        :return: list of field identifiers
        :rtype: list of str
        """
        field_identifiers = []
        for table in self.tables:
            field_identifiers += table.get_field_identifiers()
        for join_item in self.joins:
            field_identifiers += join_item.right_table.get_field_identifiers()
        return field_identifiers

    def build_insert_into(self):
        pass

    def build_withs(self):
        if self.is_inner:
            return ''

        withs = []
        for inner_query in self.with_tables + self.get_inner_queries():
            withs.append(inner_query.get_with_sql())
        if len(withs):
            withs.reverse()
            return 'WITH {0} '.format(', '.join(withs))
        return ''

    def get_inner_queries(self, query=None):
        inner_queries = []
        if query is None:
            query = self
        for table in query.tables:
            if type(table) is QueryTable:
                inner_queries.append(table)
                inner_queries += self.get_inner_queries(table.query)

        return inner_queries

    def build_select_fields(self):
        """
        Generates the sql for the SELECT portion of the query

        :return: the SELECT portion of the query
        :rtype: str
        """
        field_sql = []

        # get the field sql for each table
        for table in self.tables:
            field_sql += table.get_field_sql()

        # get the field sql for each join table
        for join_item in self.joins:
            field_sql += join_item.right_table.get_field_sql()

        # combine all field sql separated by a comma
        sql = 'SELECT {0}{1} '.format(self.get_distinct_sql(), ', '.join(field_sql))
        return sql

    def get_distinct_sql(self):
        if self._distinct and self.distinct_ons:
            raise ValueError('Cannot combine distinct and distinct_on')
        if self._distinct:
            return 'DISTINCT '
        if self.distinct_ons:
            return 'DISTINCT ON ({0}) '.format(', '.join(f.get_sql() for f in self.distinct_ons))
        return ''

    def build_from_table(self):
        """
        Generates the sql for the FROM portion of the query

        :return: the FROM portion of the query
        :rtype: str
        """
        table_parts = []

        # get the table sql for each table
        for table in self.tables:
            sql = table.get_sql()
            if len(sql):
                table_parts.append(sql)

        # combine all table sql separated by a comma
        sql = 'FROM {0} '.format(', '.join(table_parts))

        return sql

    def build_joins(self):
        """
        Generates the sql for the JOIN portion of the query

        :return: the JOIN portion of the query
        :rtype: str
        """
        join_parts = []

        # get the sql for each join object
        for join_item in self.joins:
            join_parts.append(join_item.get_sql())

        # if there are any joins, combine them
        if len(join_parts):
            combined_joins = ' '.join(join_parts)
            return '{0} '.format(combined_joins)
        return ''

    def build_where(self):
        """
        Generates the sql for the WHERE portion of the query

        :return: the WHERE portion of the query
        :rtype: str
        """
        return self._where.get_sql()

    def build_groups(self):
        """
        Generates the sql for the GROUP BY portion of the query

        :return: the GROUP BY portion of the query
        :rtype: str
        """
        # check if there are any groupings
        if len(self.groups):
            groups = []

            # get the group sql for each grouping
            for group in self.groups:
                groups.append(group.get_name())
            return 'GROUP BY {0} '.format(', '.join(groups))
        return ''

    def build_order_by(self, use_alias=True):
        """
        Generates the sql for the ORDER BY portion of the query

        :type use_alias: bool
        :param use_alias: If True, the alias for the field will be used in the order by.
            This is an option before query windows do not use the alias. Defaults to True.

        :return: the ORDER BY portion of the query
        :rtype: str
        """
        # check if there are any sorters
        if len(self.sorters):
            sorters = []

            # get the sql for each sorter
            for sorter in self.sorters:
                sorters.append(sorter.get_name(use_alias=use_alias))
            return 'ORDER BY {0} '.format(', '.join(sorters))
        return ''

    def build_limit(self):
        """
        Generates the sql for the LIMIT and OFFSET portions of the query

        :return: the LIMIT and/or OFFSET portions of the query
        :rtype: str
        """
        if self._limit:
            return self._limit.get_sql()
        return ''

    def find_table(self, table):
        """
        Finds a table by name or alias. The FROM tables and JOIN tables
        are included in the search.

        :type table: str or :class:`ModelBase <django:django.db.models.base.ModelBase>`
        :param table: string of the table name or alias or a ModelBase instance

        :return: The table if it is found, otherwise None
        :rtype: Table or None
        """
        table = TableFactory(table)
        identifier = table.get_identifier()
        join_tables = [join_item.right_table for join_item in self.joins]
        for table in (self.tables + join_tables):
            if table.get_identifier() == identifier:
                return table
        return None

    # TODO: add test for alias
    # TODO: add option to use explicit names or *
    # TODO: add test for optional explicit names
    def wrap(self, alias=None):
        """
        Wraps the query by selecting all fields from itself

        :rtype: :class:`Query <querybuilder.query.Query>`
        :return: The wrapped query
        """
        field_names = self.get_field_names()
        query = Query(self.connection).from_table(copy_instance(self), alias=alias)
        self.__dict__.update(query.__dict__)

        # set explicit field names
        self.tables[0].set_fields(field_names)
        field_names = self.get_field_names()

        return self

    def copy(self):
        """
        Deeply copies everything in the query object except the connection object is shared
        """
        connection = self.connection
        del self.connection
        copied_query = deepcopy(self)
        copied_query.connection = connection
        self.connection = connection
        return copied_query

    def get_args(self):
        """
        Gets the args for the query which will be escaped when being executed by the
        db. All inner queries are inspected and their args are combined with this
        query's args.

        :return: all args for this query as a dict
        :rtype: dict
        """
        for table in self.tables + self.with_tables:
            if type(table) is QueryTable:
                self._where.args.update(table.query.get_args())

        return self._where.args

    def explain(self, sql=None, sql_args=None):
        """
        Runs EXPLAIN on this query

        :type sql: str or None
        :param sql: The sql to run EXPLAIN on. If None is specified, the query will
            use ``self.get_sql()``

        :type sql_args: dict or None
        :param sql_args: A dictionary of the arguments to be escaped in the query. If None and
            sql is None, the query will use ``self.get_args()``

        :rtype: list of str
        :return: list of each line of output from the EXPLAIN statement
        """
        cursor = self.get_cursor()
        if sql is None:
            sql = self.get_sql()
            sql_args = self.get_args()
        elif sql_args is None:
            sql_args = {}

        cursor.execute('EXPLAIN {0}'.format(sql), sql_args)
        rows = self._fetch_all_as_dict(cursor)
        return rows

    def select(self, return_models=False, nest=False, bypass_safe_limit=False, sql=None, sql_args=None):
        """
        Executes the SELECT statement and returns the rows as a list of dictionaries or a list of
        model instances

        :type return_models: bool
        :param return_models: Set to True to return a list of models instead of a list of dictionaries.
            Defaults to False

        :type nest: bool
        :param nest: Set to True to treat all double underscores in keynames as nested data. This will
            convert all keys with double underscores to dictionaries keyed off of the left side of
            the underscores. Ex: {"id": 1", "account__id": 1, "account__name": "Name"} becomes
            {"id": 1, "account": {"id": 1, "name": "Name"}}

        :type bypass_safe_limit: bool
        :param bypass_safe_limit: Ignores the safe_limit option even if the safe_limit is enabled

        :type sql: str or None
        :param sql: The sql to execute in the SELECT statement. If one is not specified, then the
            query will use ``self.get_sql()``

        :type sql_args: str or None
        :param sql_args: The sql args to be used in the SELECT statement. If none are specified, then
            the query wil use ``self.get_args()``

        :rtype: list of dict
        :return: list of dictionaries of the rows
        """
        # Check if we need to set a safe limit
        if bypass_safe_limit is False:
            if Query.enable_safe_limit:
                if self.count() > Query.safe_limit:
                    self.limit(Query.safe_limit)

        # determine which sql to use
        if sql is None:
            sql = self.get_sql()

        # determine which sql args to use
        if sql_args is None:
            sql_args = self.get_args()

        # get the cursor to execute the query
        cursor = self.get_cursor()

        # execute the query
        cursor.execute(sql, sql_args)

        # get the results as a list of dictionaries
        rows = self._fetch_all_as_dict(cursor)

        # check if models should be returned instead of dictionaries
        if return_models:

            # set nesting to true, so the nested models can easily load the data
            nest = True

            # build model map of map name to model
            model_map = {}
            for join_item in self.joins:
                model_map[join_item.right_table.field_prefix] = join_item.right_table.model

        # check if results should be nested
        if nest:

            # convert keys with double underscores to dictionaries
            for row in rows:
                _row = row.copy()
                for key, value in _row.items():
                    set_value_for_keypath(row, key, value, True, '__')
                    if '__' in key:
                        row.pop(key)

            # create models if needed
            if return_models:
                model_class = self.tables[0].model
                new_rows = []
                for row in rows:
                    model = model_class()
                    # assign all non-model keys first because django 1.5 requires
                    # that the model has an id set before setting a property that is
                    # a foreign key
                    for key, value in row.items():
                        if key not in model_map:
                            setattr(model, key, value)
                    # assign all model instances
                    for key, value in row.items():
                        if key in model_map:
                            child_model = model_map[key]()
                            for child_key, child_value in value.items():
                                setattr(child_model, child_key, child_value)
                            value = child_model
                        setattr(model, key, value)
                    new_rows.append(model)
                rows = new_rows

        return rows

    def insert(self, rows):
        """
        Inserts records into the db
        # TODO: implement this
        """
        if len(rows) == 0:
            return

        sql, sql_args = self.get_insert_sql(rows)

        # get the cursor to execute the query
        cursor = self.get_cursor()

        # execute the query
        cursor.execute(sql, sql_args)

    def update(self, rows):
        """
        Updates records in the db
        """
        if len(rows) == 0:
            return

        sql, sql_args = self.get_update_sql(rows)

        # get the cursor to execute the query
        cursor = self.get_cursor()

        # execute the query
        cursor.execute(sql, sql_args)

    def get_auto_field_name(self, model_class):
        """
        If one of the unique_fields is the model's AutoField, return the field name, otherwise return None
        """
        # Get auto field name (a model can only have one AutoField)
        for field in model_class._meta.fields:
            if isinstance(field, AutoField):
                return field.column

        return None

    def upsert(self, rows, unique_fields, update_fields, return_rows=False, return_models=False):
        """
        Performs an upsert with the set of models defined in rows. If the unique field which is meant
        to cause a conflict is an auto increment field, then the field should be excluded when its value is null.
        In this case, an upsert will be performed followed by a bulk_create
        """
        if len(rows) == 0:
            return

        ModelClass = self.tables[0].model

        rows_with_null_auto_field_value = []

        # Get auto field name (a model can only have one AutoField)
        auto_field_name = self.get_auto_field_name(ModelClass)

        # Check if unique fields list contains an auto field
        if auto_field_name in unique_fields:
            # Separate the rows that need to be inserted vs the rows that need to be upserted
            rows_with_null_auto_field_value = [row for row in rows if getattr(row, auto_field_name) is None]
            rows = [row for row in rows if getattr(row, auto_field_name) is not None]

        return_value = []

        if rows:
            sql, sql_args = self.get_upsert_sql(
                rows,
                unique_fields,
                update_fields,
                auto_field_name=auto_field_name,
                return_rows=return_rows or return_models
            )

            # get the cursor to execute the query
            cursor = self.get_cursor()

            # execute the upsert query
            cursor.execute(sql, sql_args)

            if return_rows or return_models:
                return_value.extend(self._fetch_all_as_dict(cursor))

        if rows_with_null_auto_field_value:
            sql, sql_args = self.get_upsert_sql(
                rows_with_null_auto_field_value,
                unique_fields,
                update_fields,
                auto_field_name=auto_field_name,
                only_insert=True,
                return_rows=return_rows or return_models
            )

            # get the cursor to execute the query
            cursor = self.get_cursor()

            # execute the upsert query
            cursor.execute(sql, sql_args)

            if return_rows or return_models:
                return_value.extend(self._fetch_all_as_dict(cursor))

        if return_models:
            ModelClass = self.tables[0].model
            model_objects = [
                ModelClass(**row_dict)
                for row_dict in return_value
            ]

            # Set the state to indicate the object has been loaded from db
            for model_object in model_objects:
                model_object._state.adding = False
                model_object._state.db = 'default'

            return_value = model_objects

        return return_value

    def sql_delete(self):
        """
        Deletes records from the db
        # TODO: implement this
        """
        pass

    def get_count_query(self):
        """
        Copies the query object and alters the field list and order by to do a more efficient count
        """
        query_copy = self.copy()
        if not query_copy.tables:
            raise Exception('No tables specified to do a count')

        for table in query_copy.tables:
            del table.fields[:]

        query_copy.tables[0].add_field(CountField('*'))
        del query_copy.sorters[:]
        return query_copy

    def count(self, field='*'):
        """
        Returns a COUNT of the query by wrapping the query and performing a COUNT
        aggregate of the specified field

        :param field: the field to pass to the COUNT aggregate. Defaults to '*'
        :type field: str

        :return: The number of rows that the query will return
        :rtype: int
        """
        rows = self.get_count_query().select(bypass_safe_limit=True)
        return list(rows[0].values())[0]

    def max(self, field):
        """
        Returns the maximum value of a field in the result set of the query
        by wrapping the query and performing a MAX aggregate of the specified field
        :param field: the field to pass to the MAX aggregate
        :type field: str

        :return: The maximum value of the specified field
        :rtype: int
        """
        q = Query(self.connection).from_table(self, fields=[
            MaxField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return list(rows[0].values())[0]

    def min(self, field):
        """
        Returns the minimum value of a field in the result set of the query
        by wrapping the query and performing a MIN aggregate of the specified field
        :param field: the field to pass to the MIN aggregate
        :type field: str

        :return: The minimum value of the specified field
        :rtype: int
        """
        q = Query(self.connection).from_table(self, fields=[
            MinField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return list(rows[0].values())[0]

    def sum(self, field):
        """
        Returns the sum of the field in the result set of the query
        by wrapping the query and performing a SUM aggregate of the specified field
        :param field: the field to pass to the SUM aggregate
        :type field: str

        :return: The sum of the specified field
        :rtype: int
        """
        q = Query(self.connection).from_table(self, fields=[
            SumField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return list(rows[0].values())[0]

    def avg(self, field):
        """
        Returns the average of the field in the result set of the query
        by wrapping the query and performing an AVG aggregate of the specified field
        :param field: the field to pass to the AVG aggregate
        :type field: str

        :return: The average of the specified field
        :rtype: int
        """
        q = Query(self.connection).from_table(self, fields=[
            AvgField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return list(rows[0].values())[0]

    def _fetch_all_as_dict(self, cursor):
        """
        Iterates over the result set and converts each row to a dictionary

        :return: A list of dictionaries where each row is a dictionary
        :rtype: list of dict
        """
        return json_fetch_all_as_dict(cursor)


class QueryWindow(Query):
    """
    This is a query window that is meant to be used in the OVER clause of
    window functions. It extends ``Query``, but the only methods that will
    be used are ``order_by`` and ``partition_by`` (which just calls ``group_by``)
    """

    def partition_by(self, field=None, table=None):
        """
        Equivalent to ``order_by``, but named accordingly to the syntax of
        a window function

        :type field: str or dict or Field
        :param field: This can be a string of a field name, a dict of {'alias': field}, or
            a ``Field`` instance

        :type table: str or dict or Table
        :param table: Optional. This can be a string of a table name, a dict of {'alias': table}, or
            a ``Table`` instance. A table only needs to be supplied in more complex queries where
            the field name is ambiguous.

        :rtype: :class:`querybuilder.query.QueryWindow`
        :return: self
        """
        return self.group_by(field, table)

    def get_sql(self, debug=False, use_cache=True):
        """
        Generates the sql for this query window and returns the sql as a string.

        :type debug: bool
        :param debug: If True, the sql will be returned in a format that is easier to read and debug.
            Defaults to False

        :type use_cache: bool
        :param use_cache: If True, the query will returned the cached sql if it exists rather
            then generating the sql again. If False, the sql will be generated again. Defaults to True.

        :rtype: str
        :return: The generated sql for this query window
        """
        # TODO: implement caching and debug
        sql = ''
        sql += self.build_partition_by_fields()
        sql += self.build_order_by(use_alias=False)
        sql += self.build_limit()
        sql = sql.strip()
        sql = 'OVER ({0})'.format(sql)
        self.sql = sql

        return self.sql

    def build_partition_by_fields(self):
        """
        Equivalent to ``self.build_groups()`` except for the GROUP BY
        clause being named PARTITION BY

        :return: The sql to be used in the PARTITION BY clause
        :rtype: str
        """
        select_sql = self.build_groups()
        return select_sql.replace('GROUP BY', 'PARTITION BY', 1)


class QueryBuilderQuerySet(QuerySet):

    class Meta:
        model = None

    def __init__(self, model=None, query=None, using=None, **kwargs):
        if self.Meta is not None and model is None and hasattr(self.Meta, 'model'):
            model = self.Meta.model
            if isinstance(model, str):
                model = get_model(*model.split('.', 1))
        super(QueryBuilderQuerySet, self).__init__(model, query, using, **kwargs)
        self._queryset = self.model.objects.get_queryset()

    def __getitem__(self, k):
        if isinstance(k, int):
            return self.get_model_queryset(self._queryset, k, 1)[0]
        elif hasattr(k, 'start'):
            return self.get_model_queryset(
                self._queryset,
                k.start,
                k.stop
            )
        return None

    def get_model_queryset(self, queryset, offset, limit):
        raise NotImplementedError

    def get_field_name_from_filter(self, filter):
        filter_bits = filter.split(LOOKUP_SEP)
        field_name = filter_bits.pop(0)
        return field_name

    def call_field_filter_method(self, field, value, type='filter'):
        field_name = self.get_field_name_from_filter(field)
        filter_method_name = '{0}__{1}'.format(
            type,
            field_name
        )
        default_filter_method_name = '{0}__'.format(
            type
        )
        filter_method = getattr(self, default_filter_method_name)
        if hasattr(self, filter_method_name) and value is not None:
            filter_method = getattr(self, filter_method_name)
        filter_method({field: value}, field, value)

    def filter__(self, filter, field, value):
        pass

    def filter(self, *args, **kwargs):
        for field, value in six.iteritems(kwargs):
            self.call_field_filter_method(field, value, type='filter')
        return self

    def exclude__(self, filter, field, value):
        pass

    def exclude(self, *args, **kwargs):
        for field, value in six.iteritems(kwargs):
            self.call_field_filter_method(field, value, type='exclude')
        return self

    def count(self):
        raise NotImplementedError

    def order__(self, field, desc=False):
        pass

    def order_by(self, *field_names):
        for field in field_names:
            if field == 'pk':
                field = self.model._meta.pk.name
            desc = False
            if field[0] == '-':
                field = field[1:]
                desc = True
            method_name = '{0}__{1}'.format(
                'order',
                field
            )
            default_method_name = '{0}__'.format(
                'order'
            )
            method = getattr(self, default_method_name)
            if hasattr(self, method_name):
                method = getattr(self, method_name)
            method(field, desc)
        return self

    def distinct(self, *field_names):
        raise NotImplementedError


class JsonQueryset(QueryBuilderQuerySet):

    def __init__(self, *args, **kwargs):
        super(JsonQueryset, self).__init__(*args, **kwargs)
        self.json_query = Query().from_table(self.model)

    def get_model_queryset(self, queryset, offset, limit):
        return [self.model(**fields) for fields in self.json_query.limit(limit, offset).select()]

    def count(self):
        return self.json_query.count()

    def order_by(self, *field_names):
        for field_name in field_names:
            if field_name == 'pk':
                field_name = self.model._meta.pk.name
            reverse = '-' if field_name[0] == '-' else ''
            field_name = field_name.lstrip('-')
            parts = field_name.split('->')
            if len(parts) == 2:
                self.json_query.order_by('{0}{1}->>\'{2}\''.format(reverse, parts[0], parts[1]))
            else:
                self.json_query.order_by('{0}{1}'.format(reverse, field_name))
        return self

    def filter(self, *args, **kwargs):
        for key, value in kwargs.items():
            key = key.replace('__exact', '')
            parts = key.split('->')
            if len(parts) == 2:
                field_key_parts = parts[1].split('__')

                if len(field_key_parts) == 1:
                    key = '{0}->>\'{1}\''.format(parts[0], field_key_parts[0])
                else:
                    key = '{0}->>\'{1}\''.format(parts[0], '__'.join(field_key_parts[0:-1]))
                    key = '__'.join([key, field_key_parts[-1]])
                value = six.u('{0}'.format(value))
            if hasattr(value, 'id'):
                key = '{0}_id'.format(key)
                self.json_query.where(**{'{0}'.format(key): value.id})
            else:
                self.json_query.where(**{key: value})
        return self

    def limit(self, *args, **kwargs):
        self.json_query.limit(*args, **kwargs)
        return self
