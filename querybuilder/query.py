from copy import deepcopy
from django.db import connection
from django.db.models import Q
from django.db.models.sql import AND
from querybuilder.fields import FieldFactory, CountField, MaxField, MinField, SumField, AvgField
from querybuilder.helpers import set_value_for_keypath
from querybuilder.tables import TableFactory, ModelTable, QueryTable


class Join(object):
    """

    """

    def __init__(self, right_table=None, fields=None, condition=None, join_type='JOIN', schema=None, left_table=None, owner=None, extract_fields=True, prefix_fields=True, field_prefix=None):
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
        return '{0} {1} ON {2}'.format(self.join_type, self.right_table.get_sql(), self.get_condition())

    def set_left_table(self, left_table=None):
        if left_table:
            self.left_table = TableFactory(
                table=left_table,
                owner=self.owner,
            )
        else:
            self.left_table = self.get_left_table()

    def get_left_table(self):
        if self.left_table:
            return self.left_table
        if len(self.owner.tables):
            return self.owner.tables[0]

    def set_right_table(self, table):
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
        if self.condition:
            return self.condition

        condition = ''

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

    map = {
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
        self.arg_index = 0
        self.arg_prefix = ''
        self.args = {}
        self.wheres = Q()

    def get_sql(self):
        self.arg_index = 0
        self.args = {}
        if len(self.wheres):
            where = self.build_where_part(self.wheres)
            return 'WHERE {0} '.format(where)
        return ''

    def get_condition_operator(self, operator):
        return Where.map.get(operator, None)

    def get_condition_value(self, operator, value):
        if operator == 'contains':
            value = '%{0}%'.format(value)
        elif operator == 'startswith':
            value = '{0}%'.format(value)
        return value

    def build_where_part(self, wheres):
        where_parts = []
        for where in wheres.children:
            if type(where) is Q:
                where_parts.append(self.build_where_part(where))
            elif type(where) is tuple:
                field_name = where[0]
                value = where[1]

                operator_str = 'eq'
                operator = '='

                field_parts = field_name.split('__')
                if len(field_parts) > 1:
                    operator_str = field_parts[-1]
                    operator = self.get_condition_operator(operator_str)
                    if operator is None:
                        operator = '='
                        field_name = '.'.join(field_parts)
                    else:
                        field_name = '.'.join(field_parts[:-1])

                # check if we are comparing to null
                if value is None:
                    operator = 'IS'

                condition = '{0} {1} ?'.format(field_name, operator)
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

                    named_args = []
                    for value_item in value:
                        named_arg = self.set_arg(value_item)
                        named_args.append('%({0})s'.format(named_arg))
                    condition = condition.replace('?', '({0})'.format(','.join(named_args)), 1)
                else:
                    value = self.get_condition_value(operator_str, value)
                    named_arg = self.set_arg(value)
                    condition = condition.replace('?', '%({0})s'.format(named_arg), 1)

                where_parts.append(condition)
        joined_parts = ' {0} '.format(wheres.connector).join(where_parts)
        return '({0})'.format(joined_parts)

    def set_arg(self, value):
        named_arg = '{0}A{1}'.format(self.arg_prefix, self.arg_index)
        self.args[named_arg] = value
        self.arg_index += 1
        return named_arg


class Group(object):
    """

    """

    def __init__(self, field=None, table=None):
        self.field = FieldFactory(field)
        self.table = TableFactory(table)
        if self.table and self.field.table is None:
            self.field.set_table(self.table)

    def get_name(self):
        """
        Gets the name to reference the grouped field
        :return: :rtype: str
        """
        return self.field.get_identifier()


class Sorter(object):
    """

    """

    def __init__(self, field=None, table=None, desc=False):
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
        :return: :rtype: str
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

    """

    def __init__(self, limit=None, offset=None):
        self.limit = limit
        self.offset = offset

    def get_sql(self):
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
    """
    enable_safe_limit = False
    safe_limit = 1000

    def init_defaults(self):
        """
        Sets the default values for this instance
        """

        self.sql = ''
        """
        The query generated by calling ``self.get_sql()`` This is used for
        caching purposes.
        """

        self.tables = []
        """
        A list of ``Table`` instances this query is selecting from
        """

        self.joins = []

        """
        A list of ``Join`` instances this query is joining on
        """

        self._where = Where()
        """
        A ``Where`` instance containing filtering data for this query
        """

        self.groups = []
        """
        A list of ``Group`` instances that determine the GROUP BY clause for this query
        """

        self.sorters = []
        """
        A list of ``Sorter`` instances that determine the ORDER BY clause for this query
        """

        self._limit = None
        """
        An instance of ``Limit`` This will only exist if a limit has been specified for the query
        """

        self.table_prefix = ''
        """
        A ``str`` that determines how to prefix inner queries of this query
        """

    def __init__(self):
        """
        Initializes this instance by calling ``self.init_defaults``
        @return: self
        """
        self.init_defaults()

    def from_table(self, table=None, fields='*', schema=None, **kwargs):
        """
        Adds a ``Table`` and any optional fields to the list of tables
        this query is selecting from.
        @param table: The table to select fields from. This can be a string of the table
            name, a dict of {'alias': table}, or a ``Table`` instance
        @type table: str or dict or Table
        @param fields: The fields to select from ``table``. Defaults to '*'. This can be
            a single field, a tuple of fields, or a list of fields. Each field can be a string
            or ``Field`` instance
        @type fields: str or tuple or list or Field
        @param schema: This is not implemented, but it will be a string of the db schema name
        @type schema: str
        @return: self
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

    def join(self, right_table=None, fields=None, condition=None, join_type='JOIN', schema=None, left_table=None, extract_fields=True, prefix_fields=True, field_prefix=None):
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
        """
        # self.mark_dirty()
        # TODO: fix bug when joining from simple table to model table with no condition
        # it assumes left_table.model
        self.joins.append(Join(
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
        ))

        return self

    def join_left(self, right_table=None, fields=None, condition=None, join_type='LEFT JOIN', schema=None, left_table=None, extract_fields=True, prefix_fields=True, field_prefix=None):
        """
        Wrapper for ``self.join`` with a default join of 'LEFT JOIN'
        @return: self
        """
        return self.join(right_table=right_table, fields=fields, condition=condition, join_type=join_type, schema=schema, left_table=left_table, extract_fields=extract_fields, prefix_fields=prefix_fields, field_prefix=field_prefix)

    def where(self, q=None, where_type='AND', **kwargs):
        """
        Adds a where condition as a Q object to the query's ``Where`` instance.
        @param q: A django ``Q`` instance. This will be added to the query's ``Where`` object. If no
            Q object is passed, the kwargs will be examined for params to be added to Q objects
        @type q: Q
        @param where_type: The connection type of the where condition ('AND', 'OR')
        @param where_type: str
        @return: self
        """
        # self.mark_dirty()
        if q is not None:
            self._where.wheres.add(q, where_type)
        if len(kwargs):
            for key, value in kwargs.items():
                q = Q(**{key:value})
                self._where.wheres.add(q, where_type)
        return self

    def group_by(self, field=None, table=None):
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
        """
        self.groups.append(Group(
            field=field,
            table=table,
        ))

        return self

    def order_by(self, field=None, table=None, desc=False):
        """
        @return: self
        """
        self.sorters.append(Sorter(
            field=field,
            table=table,
            desc=desc
        ))
        return self

    def limit(self, limit=None, offset=None):
        """
        @return: self
        """
        self._limit = Limit(
            limit=limit,
            offset=offset
        )
        return self

    def check_name_collisions(self):
        table_index = 0
        table_names = {}
        for table in self.tables:
            table_prefix = 'T{0}'.format(table_index)
            auto_alias = '{0}{1}'.format(self.table_prefix, table_prefix)

            identifier = table.get_identifier()
            if identifier is None or identifier in table_names:
                table.auto_alias = auto_alias
            table_names[identifier] = True

            # prefix inner query args and update self args
            if type(table) is QueryTable:
                table.query.prefix_args(auto_alias)
                table.query.table_prefix = table_prefix

            table_index += 1

    def prefix_args(self, prefix):
        self._where.arg_prefix = prefix

    def get_sql(self, debug=False, use_cache=True):
        """
        @return: self
        """
        # if self.sql and use_cache and not debug:
        #     return self.sql

        self.check_name_collisions()

        if debug:
            return self.format_sql()

        sql = ''
        # sql += self.build_withs()
        sql += self.build_select_fields()
        sql += self.build_from_table()
        sql += self.build_joins()
        sql += self.build_where()
        sql += self.build_groups()
        sql += self.build_order_by()
        sql += self.build_limit()

        self.sql = sql.strip()

        return self.sql

    def format_sql(self):
        sql = ''
        select_segment = self.build_select_fields()
        select_segment = select_segment.replace('SELECT ', '', 1)
        fields = [field.strip() for field in select_segment.split(',')]
        sql += 'SELECT\n\t{0}\n'.format(',\n\t'.join(fields))

        from_segment = self.build_from_table()
        from_segment = from_segment.replace('FROM ', '', 1)
        tables = [table.strip() for table in from_segment.split(',')]
        sql += 'FROM\n\t{0}\n'.format(',\n\t'.join(tables))

        order_by_segment = self.build_order_by()
        if len(order_by_segment):
            order_by_segment = order_by_segment.replace('ORDER BY ', '', 1)
            sorters = [sorter.strip() for sorter in order_by_segment.split(',')]
            sql += 'ORDER BY\n\t{0}\n'.format(',\n\t'.join(sorters))

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
        field_names = []
        for table in self.tables:
            field_names += table.get_field_names()
        for join_item in self.joins:
            field_names += join_item.right_table.get_field_names()
        return field_names

    def get_field_identifiers(self):
        field_identifiers = []
        for table in self.tables:
            field_identifiers += table.get_field_identifiers()
        for join_item in self.joins:
            field_identifiers += join_item.right_table.get_field_identifiers()
        return field_identifiers

    def build_select_fields(self):
        """
        @return: str
        """
        field_sql = []
        for table in self.tables:
            field_sql += table.get_field_sql()
        for join_item in self.joins:
            field_sql += join_item.right_table.get_field_sql()
        sql = 'SELECT {0} '.format(', '.join(field_sql))
        return sql

    def build_from_table(self):
        """
        @return: str
        """
        table_parts = []
        for table in self.tables:
            sql = table.get_sql()
            if len(sql):
                table_parts.append(table.get_sql())

        sql = 'FROM {0} '.format(', '.join(table_parts))

        return sql

    def build_joins(self):
        """
        @return: str
        """
        join_parts = []

        for join_item in self.joins:
            join_parts.append(join_item.get_sql())

        if len(join_parts):
            combined_joins = ' '.join(join_parts)
            return '{0} '.format(combined_joins)
        return ''

    def build_where(self):
        """
        @return: str
        """
        return self._where.get_sql()

    def build_groups(self):
        """
        @return: str
        """
        if len(self.groups):
            groups = []
            for group in self.groups:
                groups.append(group.get_name())
            return 'GROUP BY {0} '.format(', '.join(groups))
        return ''

    def build_order_by(self, use_alias=True):
        """
        @return: str
        """
        if len(self.sorters):
            sorters = []
            for sorter in self.sorters:
                sorters.append(sorter.get_name(use_alias=use_alias))
            return 'ORDER BY {0} '.format(', '.join(sorters))
        return ''

    def build_limit(self):
        """
        @return: str
        """
        if self._limit:
            return self._limit.get_sql()
        return ''

    def find_table(self, table):
        """
        Finds a table by name or alias. The FROM tables and JOIN tables
        are included in the search.
        :param table: str of a table name or alias or a ModelBase instance
        :return: :rtype: Table
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
        @return: self
        """
        query = Query().from_table(deepcopy(self))
        self.__dict__.update(query.__dict__)
        return self

    def get_args(self):
        for table in self.tables:
            if type(table) is QueryTable:
                self._where.args.update(table.query.get_args())

        return self._where.args

    def explain(self, sql=None, sql_args=None):
        """
        @return: list
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
        @return: list
        """
        # Check if we need to set a safe limit
        if bypass_safe_limit is False:
            if Query.enable_safe_limit:
                if self.count() > Query.safe_limit:
                    self.limit(Query.safe_limit)

        cursor = connection.cursor()
        if sql is None:
            sql = self.get_sql()
        if sql_args is None:
            sql_args = self.get_args()
        cursor.execute(sql, sql_args)
        rows = self._fetch_all_as_dict(cursor)

        if return_models:
            nest = True

            # build model map
            model_map = {}
            for join_item in self.joins:
                model_map[join_item.right_table.field_prefix] = join_item.right_table.model

        if nest:
            for row in rows:
                for key, value in row.items():
                    set_value_for_keypath(row, key, value, True, '__')
                    if '__' in key:
                        row.pop(key)

            # make models
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
        pass

    def sql_update(self):
        pass

    def sql_delete(self):
        pass

    def count(self, field='*'):
        q = Query().from_table(self, fields=[
            CountField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def max(self, field):
        q = Query().from_table(self, fields=[
            MaxField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def min(self, field):
        q = Query().from_table(self, fields=[
            MinField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def sum(self, field):
        q = Query().from_table(self, fields=[
            SumField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def avg(self, field):
        q = Query().from_table(self, fields=[
            AvgField(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def _fetch_all_as_dict(self, cursor):
        """
        @return: list
        """
        desc = cursor.description
        return [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
        ]


class QueryWindow(Query):

    def partition_by(self, field=None, table=None):
        return super(QueryWindow, self).group_by(field, table)

    def get_sql(self):
        """
        @return: self
        """
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
        @return: str
        """
        select_sql = super(QueryWindow, self).build_groups()
        return select_sql.replace('GROUP BY', 'PARTITION BY', 1)
