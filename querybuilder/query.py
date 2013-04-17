from copy import deepcopy
from django.db import connection
from django.db.models import Q
from querybuilder.fields import FieldFactory, CountField, MaxField, MinField, SumField, AvgField
from querybuilder.helpers import set_value_for_keypath
from querybuilder.tables import TableFactory, ModelTable, QueryTable


class Join(object):
    """
    Represents the JOIN clauses of a Query. The join can be of any join type.
    """

    def __init__(self, right_table=None, fields=None, condition=None, join_type='JOIN',
                 schema=None, left_table=None, owner=None, extract_fields=True,
                 prefix_fields=True, field_prefix=None):
        """
        Initializes the default values and assigns any passed params
        @param right_table: The table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance
        @type right_table: str or dict or Table
        @param fields: The fields to select from ``table``. Defaults to None. This can be
            a single field, a tuple of fields, or a list of fields. Each field can be a string
            or ``Field`` instance
        @type fields: str or tuple or list or Field
        @param condition: The join condition specifying the fields being joined. If the two tables being
            joined are instances of ``ModelTable`` then the condition should be created automatically.
        @type condition: str
        @param join_type: The type of join (JOIN, LEFT JOIN, INNER JOIN, etc). Defaults to 'JOIN'
        @type join_type: str
        @param schema: This is not implemented, but it will be a string of the db schema name
        @type schema: str
        @param left_table: The left table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance. Defaults to the first table
            in the query.
        @type left_table: str or dict or Table or None
        @param owner: A reference to the query managing this Join object
        @type owner: Query
        @param extract_fields: If True and joining with a ``ModelTable``, then '*'
            fields will be converted to individual fields for each column in the table. Defaults
            to True.
        @type extract_fields: bool
        @param prefix_fields: If True, then the joined table will have each of its field names
            prefixed with the field_prefix. If no field_prefix is specified, a name will be
            generated based on the join field name. This is usually used with nesting results
            in order to create models in python or javascript. Defaults to True.
        @type prefix_fields: bool
        @param field_prefix: The field prefix to be used in front of each field name if prefix_fields
            is set to True. If no field_prefix is set, one will be automatically created based on
            the join field name.
        @type field_prefix: str
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
        @return: the JOIN sql for the join tables and join condition
        @rtype: str
        """
        return '{0} {1} ON {2}'.format(self.join_type, self.right_table.get_sql(), self.get_condition())

    def set_left_table(self, left_table=None):
        """
        Sets the left table for this join clause. If no table is specified, the first table
        in the query will be used
        @param left_table: The left table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance. Defaults to the first table
            in the query.
        @type left_table: str or dict or Table or None
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
        @return: the left table if one was specified, otherwise the first table in the query
        @rtype: Table
        """
        if self.left_table:
            return self.left_table
        if len(self.owner.tables):
            return self.owner.tables[0]

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
            for field in self.left_table.model._meta.get_all_related_objects():
                if field.model == self.right_table.model:
                    if self.right_table.field_prefix is None:
                        self.right_table.field_prefix = field.get_accessor_name()
                        if len(self.right_table.field_prefix) > 4 and self.right_table.field_prefix[-4:] == '_set':
                            self.right_table.field_prefix = self.right_table.field_prefix[:-4]
                    return

            # check if this join type is for a foreign key
            for field in self.left_table.model._meta.fields:
                if (
                    field.get_internal_type() == 'OneToOneField' or
                    field.get_internal_type() == 'ForeignKey'
                ):
                    if field.rel.to == self.right_table.model:
                        if self.right_table.field_prefix is None:
                            self.right_table.field_prefix = field.name
                        return

    def get_condition(self):
        """
        Determines the condition to be used in the condition part of the join sql.
        @return: The condition for the join clause
        @rtype: str or None
        """
        if self.condition:
            return self.condition

        if type(self.right_table) is ModelTable and type(self.right_table) is ModelTable:
            # loop through fields to find the field for this model

            # check if this join type is for a related field
            for field in self.right_table.model._meta.get_all_related_objects():
                if field.model == self.left_table.model:
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
                    field.get_internal_type() == 'OneToOneField' or
                    field.get_internal_type() == 'ForeignKey'
                ):
                    if field.rel.to == self.left_table.model:
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
        'eq': '=',
        'gt': '>',
        'gte': '>=',
        'lt': '<',
        'lte': '<=',
        'contains': 'LIKE',
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
        return: the WHERE portion of the sql
        @rtype: str
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
        @return: the comparison operator from the Where class's comparison_map
        @rtype: str
        """
        return Where.comparison_map.get(operator, None)

    def get_condition_value(self, operator, value):
        """
        Gets the condition value based on the operator and value
        @param operator: the condition operator name
        @type operator: str
        @param value: the value to be formatted based on the condition operator
        @type value: object
        @return: the comparison operator from the Where class's comparison_map
        @rtype: str
        """
        if operator == 'contains':
            value = '%{0}%'.format(value)
        elif operator == 'startswith':
            value = '{0}%'.format(value)
        return value

    def build_where_part(self, wheres):
        """
        Recursive method that builds the where parts. Any Q objects that have children will
        also be built with ``self.build_where_part()``
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
                # TODO: do not convert the first double underscore to a .
                field_parts = field_name.split('__')
                if len(field_parts) > 1:
                    # get the operator based on the last element split from the double underscores
                    operator_str = field_parts[-1]
                    operator = self.get_condition_operator(operator_str)
                    if operator is None:
                        operator = '='
                        field_name = '.'.join(field_parts)
                    else:
                        field_name = '.'.join(field_parts[:-1])

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
        @return: the string placeholder for the arg
        @rtype: str
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
        @param field: This can be a string of a field name, a dict of {'alias': field}, or
            a ``Field`` instance
        @type field: str or dict or Field
        @param table: Optional. This can be a string of a table name, a dict of {'alias': table}, or
            a ``Table`` instance. A table only needs to be supplied in more complex queries where
            the field name is ambiguous.
        @type table: str or dict or Table
        """
        self.field = FieldFactory(field)
        self.table = TableFactory(table)
        if self.table and self.field.table is None:
            self.field.set_table(self.table)

    def get_name(self):
        """
        Gets the name to reference the grouped field
        @return: the name to reference the grouped field
        @rtype: str
        """
        return self.field.get_identifier()


class Sorter(object):
    """
    Used internally by the Query class to set ORDER BY clauses on the query.
    """

    def __init__(self, field=None, table=None, desc=False):
        """
        Initializes the instance variables
        @param field: This can be a string of a field name, a dict of {'alias': field}, or
            a ``Field`` instance
        @type field: str or dict or Field
        @param table: Optional. This can be a string of a table name, a dict of {'alias': table}, or
            a ``Table`` instance. A table only needs to be supplied in more complex queries where
            the field name is ambiguous.
        @type table: str or dict or Table
        @param desc: Set to True to sort by this field in DESC order or False to sort by this field
            in ASC order. Defaults to False.
        @type desc: bool
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
        if type(self.field.field) is str and self.field.field[0] == '-':
            self.desc = True
            self.field.field = self.field.field[1:]
            self.field.name = self.field.name[1:]

    def get_name(self, use_alias=True):
        """
        Gets the name to reference the sorted field
        @return: the name to reference the sorted field
        @rtype: str
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
        @param limit: the number of rows to return
        @type limit: int
        @param offset: the number of rows to start returning rows from
        @type limit: int
        """
        self.limit = limit
        self.offset = offset

    def get_sql(self):
        """
        Generates the sql used for the limit clause of a Query
        @return: the sql for the limit clause of a Query
        @rtype: str
        """
        sql = ''
        if self.limit > 0:
            sql += 'LIMIT {0} '.format(self.limit)
        if self.offset > 0:
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

    def __init__(self):
        """
        Initializes this instance by calling ``self.init_defaults``
        @return: self
        @rtype: self
        """
        self.init_defaults()

    def from_table(self, table=None, fields='*', schema=None, **kwargs):
        """
        Adds a ``Table`` and any optional fields to the list of tables
        this query is selecting from.
        @param table: The table to select fields from. This can be a string of the table
            name, a dict of {'alias': table}, a ``Table`` instance, a Query instance, or a
            django Model instance
        @type table: str or dict or Table or Query or ModelBase
        @param fields: The fields to select from ``table``. Defaults to '*'. This can be
            a single field, a tuple of fields, or a list of fields. Each field can be a string
            or ``Field`` instance
        @type fields: str or tuple or list or Field
        @param schema: This is not implemented, but it will be a string of the db schema name
        @type schema: str
        @param kwargs: Any additional parameters to be passed into the constructor of ``TableFactory``
        @return: self
        @rtype: self
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

    def with_query(self, query=None, alias=None):
        """
        @return: self
        @rtype: self
        """
        self.with_tables.append(TableFactory(query, alias=alias))
        print self.with_tables
        return self

    def join(self, right_table=None, fields=None, condition=None, join_type='JOIN',
             schema=None, left_table=None, extract_fields=True, prefix_fields=False, field_prefix=None,
             allow_duplicates=False):
        """
        Joins a table to another table based on a condition and adds fields from the joined table
        to the returned fields.
        @param right_table: The table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance
        @type right_table: str or dict or Table
        @param fields: The fields to select from ``right_table``. Defaults to `None`. This can be
            a single field, a tuple of fields, or a list of fields. Each field can be a string
            or ``Field`` instance
        @type fields: str or tuple or list or Field
        @param condition: The join condition specifying the fields being joined. If the two tables being
            joined are instances of ``ModelTable`` then the condition should be created automatically.
        @type condition: str
        @param join_type: The type of join (JOIN, LEFT JOIN, INNER JOIN, etc). Defaults to 'JOIN'
        @type join_type: str
        @param schema: This is not implemented, but it will be a string of the db schema name
        @type schema: str
        @param left_table: The left table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance. Defaults to the first table
            in the query.
        @type left_table: str or dict or Table
        @param extract_fields: If True and joining with a ``ModelTable``, then '*'
            fields will be converted to individual fields for each column in the table. Defaults
            to True.
        @type extract_fields: bool
        @param prefix_fields: If True, then the joined table will have each of its field names
            prefixed with the field_prefix. If not field_prefix is specified, a name will be
            generated based on the join field name. This is usually used with nesting results
            in order to create models in python or javascript. Defaults to True.
        @type prefix_fields: bool
        @param field_prefix: The field prefix to be used in front of each field name if prefix_fields
            is set to True. If no field_prefix is set, one will be automatically created based on
            the join field name.
        @type field_prefix: str
        @return: self
        @rtype: self
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
                if join_item.right_table.get_identifier() == new_join_item.right_table.get_identifier() and join_item.left_table.get_identifier() == new_join_item.left_table.get_identifier():
                    return self

        self.joins.append(new_join_item)

        return self

    def join_left(self, right_table=None, fields=None, condition=None, join_type='LEFT JOIN',
                  schema=None, left_table=None, extract_fields=True, prefix_fields=False,
                  field_prefix=None, allow_duplicates=False):
        """
        Wrapper for ``self.join`` with a default join of 'LEFT JOIN'
        @param right_table: The table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance
        @type right_table: str or dict or Table
        @param fields: The fields to select from ``right_table``. Defaults to `None`. This can be
            a single field, a tuple of fields, or a list of fields. Each field can be a string
            or ``Field`` instance
        @type fields: str or tuple or list or Field
        @param condition: The join condition specifying the fields being joined. If the two tables being
            joined are instances of ``ModelTable`` then the condition should be created automatically.
        @type condition: str
        @param join_type: The type of join (JOIN, LEFT JOIN, INNER JOIN, etc). Defaults to 'JOIN'
        @type join_type: str
        @param schema: This is not implemented, but it will be a string of the db schema name
        @type schema: str
        @param left_table: The left table being joined with. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance. Defaults to the first table
            in the query.
        @type left_table: str or dict or Table
        @param extract_fields: If True and joining with a ``ModelTable``, then '*'
            fields will be converted to individual fields for each column in the table. Defaults
            to True.
        @type extract_fields: bool
        @param prefix_fields: If True, then the joined table will have each of its field names
            prefixed with the field_prefix. If not field_prefix is specified, a name will be
            generated based on the join field name. This is usually used with nesting results
            in order to create models in python or javascript. Defaults to True.
        @type prefix_fields: bool
        @param field_prefix: The field prefix to be used in front of each field name if prefix_fields
            is set to True. If no field_prefix is set, one will be automatically created based on
            the join field name.
        @type field_prefix: str
        @return: self
        @rtype: self
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
        @param q: A django ``Q`` instance. This will be added to the query's ``Where`` object. If no
            Q object is passed, the kwargs will be examined for params to be added to Q objects
        @type q: Q
        @param where_type: The connection type of the where condition ('AND', 'OR')
        @param where_type: str
        @return: self
        @rtype: self
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
        @param field: This can be a string of a field name, a dict of {'alias': field}, or
            a ``Field`` instance
        @type field: str or dict or Field
        @param table: Optional. This can be a string of a table name, a dict of {'alias': table}, or
            a ``Table`` instance. A table only needs to be supplied in more complex queries where
            the field name is ambiguous.
        @type table: str or dict or Table
        @return: self
        @rtype: self
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
        @param field: This can be a string of a field name, a dict of {'alias': field}, or
            a ``Field`` instance
        @type field: str or dict or Field
        @param table: Optional. This can be a string of a table name, a dict of {'alias': table}, or
            a ``Table`` instance. A table only needs to be supplied in more complex queries where
            the field name is ambiguous.
        @type table: str or dict or Table
        @param desc: Set to True to sort by this field in DESC order or False to sort by this field
            in ASC order. Defaults to False.
        @type desc: bool
        @return: self
        @rtype: self
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
        @param limit: The number of rows to return
        @type limit: int
        @param offset: The offset from the start of the record set where rows should start being returned
        @type offset: int
        @return: self
        @rtype: self
        """
        self._limit = Limit(
            limit=limit,
            offset=offset
        )
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
        @param debug: If True, the sql will be returned in a format that is easier to read and debug.
            Defaults to False
        @type debug: bool
        @param use_cache: If True, the query will returned the cached sql if it exists rather
            then generating the sql again. If False, the sql will be generated again. Defaults to True.
        @type use_cache: bool
        @return: The generated sql for this query
        @rtype: str
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

    def format_sql(self):
        """
        Builds the sql in a format that is easy for humans to read and debug
        @return: The formatted sql for this query
        @rtype: str
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
        @return: list of field names
        @rtype: list of str
        """
        field_names = []
        for table in self.tables:
            field_names += table.get_field_names()
        for join_item in self.joins:
            field_names += join_item.right_table.get_field_names()
        return field_names

    def get_field_identifiers(self):
        """
        Builds a list of the field identifiers for all tables and joined tables by calling
        ``get_field_identifiers()`` on each table
        @return: list of field identifiers
        @rtype: list of str
        """
        field_identifiers = []
        for table in self.tables:
            field_identifiers += table.get_field_identifiers()
        for join_item in self.joins:
            field_identifiers += join_item.right_table.get_field_identifiers()
        return field_identifiers

    def build_withs(self):
        if self.is_inner:
            return ''

        withs = []
        for inner_query in self.get_inner_queries() + self.with_tables:
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
        @return: the SELECT portion of the query
        @rtype: str
        """
        field_sql = []

        # get the field sql for each table
        for table in self.tables:
            field_sql += table.get_field_sql()

        # get the field sql for each join table
        for join_item in self.joins:
            field_sql += join_item.right_table.get_field_sql()

        # combine all field sql separated by a comma
        sql = 'SELECT {0} '.format(', '.join(field_sql))
        return sql

    def build_from_table(self):
        """
        Generates the sql for the FROM portion of the query
        @return: the FROM portion of the query
        @rtype: str
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
        @return: the JOIN portion of the query
        @rtype: str
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
        @return: the WHERE portion of the query
        @rtype: str
        """
        return self._where.get_sql()

    def build_groups(self):
        """
        Generates the sql for the GROUP BY portion of the query
        @return: the GROUP BY portion of the query
        @rtype: str
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
        @param use_alias: If True, the alias for the field will be used in the order by.
            This is an option before query windows do not use the alias. Defaults to True.
        @type use_alias: bool
        @return: the ORDER BY portion of the query
        @rtype: str
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
        @return: the LIMIT and/or OFFSET portions of the query
        @rtype: str
        """
        if self._limit:
            return self._limit.get_sql()
        return ''

    def find_table(self, table):
        """
        Finds a table by name or alias. The FROM tables and JOIN tables
        are included in the search.
        @param table: string of the table name or alias or a ModelBase instance
        @type table: str or ModelBase
        @return: The table if it is found, otherwise None
        @rtype: Table or None
        """
        table = TableFactory(table)
        identifier = table.get_identifier()
        join_tables = [join_item.right_table for join_item in self.joins]
        for table in (self.tables + join_tables):
            if table.get_identifier() == identifier:
                return table
        return None

    def wrap(self):
        """
        Wraps the query by selecting all fields from itself
        @return: The wrapped query
        @rtype: self
        """
        field_names = self.get_field_names()
        query = Query().from_table(deepcopy(self))
        self.__dict__.update(query.__dict__)

        # set explicit field names
        self.tables[0].set_fields(field_names)
        field_names = self.get_field_names()

        return self

    def get_args(self):
        """
        Gets the args for the query which will be escaped when being executed by the
        db. All inner queries are inspected and their args are combined with this
        query's args.
        @return: all args for this query as a dict
        @rtype: dict
        """
        for table in self.tables + self.with_tables:
            if type(table) is QueryTable:
                self._where.args.update(table.query.get_args())

        return self._where.args

    def explain(self, sql=None, sql_args=None):
        """
        Runs EXPLAIN on this query
        @param sql: The sql to run EXPLAIN on. If None is specified, the query will
            use ``self.get_sql()``
        @type sql: str or None
        @param sql_args: A dictionary of the arguments to be escaped in the query. If None and
            sql is None, the query will use ``self.get_args()``
        @type sql_args: dict or None
        @return: list of each line of output from the EXPLAIN statement
        @rtype: list of str
        """
        cursor = connection.cursor()
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
        @param return_models: Set to True to return a list of models instead of a list of dictionaries.
            Defaults to False
        @type return_models: bool
        @param nest: Set to True to treat all double underscores in keynames as nested data. This will
            convert all keys with double underscores to dictionaries keyed off of the left side of
            the underscores. Ex: {"id": 1", "account__id": 1, "account__name": "Name"} becomes
            {"id": 1, "account": {"id": 1, "name": "Name"}}
        @type nest: bool
        @param bypass_safe_limit: Ignores the safe_limit option even if the safe_limit is enabled
        @type bypass_safe_limit: bool
        @param sql: The sql to execute in the SELECT statement. If one is not specified, then the
            query will use ``self.get_sql()``
        @type sql: str or None
        @param sql_args: The sql args to be used in the SELECT statement. If none are specified, then
            the query wil use ``self.get_args()``
        @type sql_args: str or None
        @return: list of dictionaries of the rows
        @rtype: list of dict
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
        cursor = connection.cursor()

        #execute the query
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
                for key, value in row.items():
                    set_value_for_keypath(row, key, value, True, '__')
                    if '__' in key:
                        row.pop(key)

            # create models if needed
            if return_models:
                model_class = self.tables[0].model
                new_rows = []
                for row in rows:
                    model = model_class()
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

    def sql_insert(self):
        """
        Inserts records into the db
        # TODO: implement this
        """
        pass

    def sql_update(self):
        """
        Updates records in the db
        # TODO: implement this
        """
        pass

    def sql_delete(self):
        """
        Deletes records from the db
        # TODO: implement this
        """
        pass

    def count(self, field='*'):
        """
        Returns a COUNT of the query by wrapping the query and performing a COUNT
        aggregate of the specified field
        @param field: the field to pass to the COUNT aggregate. Defaults to '*'
        @type field: str
        @return: The number of rows that the query will return
        @rtype: int
        """
        q = Query().from_table(self, fields=[
            CountField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def max(self, field):
        """
        Returns the maximum value of a field in the result set of the query
        by wrapping the query and performing a MAX aggregate of the specified field
        @param field: the field to pass to the MAX aggregate
        @type field: str
        @return: The maximum value of the specified field
        @rtype: int
        """
        q = Query().from_table(self, fields=[
            MaxField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def min(self, field):
        """
        Returns the minimum value of a field in the result set of the query
        by wrapping the query and performing a MIN aggregate of the specified field
        @param field: the field to pass to the MIN aggregate
        @type field: str
        @return: The minimum value of the specified field
        @rtype: int
        """
        q = Query().from_table(self, fields=[
            MinField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def sum(self, field):
        """
        Returns the sum of the field in the result set of the query
        by wrapping the query and performing a SUM aggregate of the specified field
        @param field: the field to pass to the SUM aggregate
        @type field: str
        @return: The sum of the specified field
        @rtype: int
        """
        q = Query().from_table(self, fields=[
            SumField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def avg(self, field):
        """
        Returns the average of the field in the result set of the query
        by wrapping the query and performing an AVG aggregate of the specified field
        @param field: the field to pass to the AVG aggregate
        @type field: str
        @return: The average of the specified field
        @rtype: int
        """
        q = Query().from_table(self, fields=[
            AvgField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def _fetch_all_as_dict(self, cursor):
        """
        Iterates over the result set and converts each row to a dictionary
        @return: A list of dictionaries where each row is a dictionary
        @rtype: list of dict
        """
        desc = cursor.description
        return [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
        ]


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
        @param field: This can be a string of a field name, a dict of {'alias': field}, or
            a ``Field`` instance
        @type field: str or dict or Field
        @param table: Optional. This can be a string of a table name, a dict of {'alias': table}, or
            a ``Table`` instance. A table only needs to be supplied in more complex queries where
            the field name is ambiguous.
        @type table: str or dict or Table
        @return: self
        @rtype: self
        """
        return self.group_by(field, table)

    def get_sql(self, debug=False, use_cache=True):
        """
        Generates the sql for this query window and returns the sql as a string.
        @param debug: If True, the sql will be returned in a format that is easier to read and debug.
            Defaults to False
        @type debug: bool
        @param use_cache: If True, the query will returned the cached sql if it exists rather
            then generating the sql again. If False, the sql will be generated again. Defaults to True.
        @type use_cache: bool
        @return: The generated sql for this query window
        @rtype: str
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
        @return: The sql to be used in the PARTITION BY clause
        @rtype: str
        """
        select_sql = self.build_groups()
        return select_sql.replace('GROUP BY', 'PARTITION BY', 1)
