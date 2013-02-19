from django.db import connection
from django.db.models import Count, Max, Min, Sum, Avg, Q
from django.db.models.base import ModelBase
from django.db.models.sql import AND
from querybuilder.fields import FieldFactory, Field
from querybuilder.helpers import set_value_for_keypath


class Table(object):

    def __init__(self, table=None, fields=None, schema=None, extract_fields=False, prefix_fields=False, owner=None):
        self.model = None
        self.owner = owner
        self.name = None
        self.alias = None
        self.auto_alias = None
        self.type = type(table)
        self.fields = []
        self.schema = schema
        self.extract_fields = extract_fields
        self.prefix_fields = prefix_fields

        if self.type is dict:
            self.alias = table.keys()[0]
            table = table.values()[0]
            self.type = type(table)

        if self.type is str:
            self.name = table
        elif self.type is ModelBase:
            self.model = table
            self.name = self.model._meta.db_table

        if fields:
            self.set_fields(fields)

    def add_field(self, field):
        if isinstance(field, Field):
            field.table = self
        else:
            field = FieldFactory(
                field,
                table=self,
            )

        if self.extract_fields and field.name == '*':
            field.ignore = True
            if self.type is ModelBase:
                fields = [model_field.column for model_field in self.model._meta.fields]
                self.add_fields(fields)

        if field.auto:
            field.ignore = True
            field.generate_auto_fields()

        if field.ignore is False:
            self.fields.append(field)

        # new_fields = []
        # for field in table_dict['fields']:
        #     if type(field) is dict:
        #         new_fields.append(field)
        #     elif field == '*':
        #         new_fields.append(field)
        #     else:
        #         new_fields.append({
        #             '{0}__{1}'.format(table_join_name, field): field
        #         })
        # table_dict['fields'] = new_fields
        # if fields and len(fields) and fields[0] == '*':
        #     table_dict['fields'] = [field.column for field in table_dict['table']._meta.fields]

    def set_fields(self, fields):
        self.fields = []
        self.add_fields(fields)

    def add_fields(self, fields):
        for field in fields:
            self.add_field(field)

    def get_fields_sql(self):
        """
        Loop through this tables fields and calls the get_sql
        method on each of them to build the field list for the FROM
        clause
        :return: :rtype: str
        """
        parts = []
        for field in self.fields:
            parts.append(field.get_sql())
        return ', '.join(parts)

    def get_name(self):
        """
        Gets the name to reference the table within a query. If
        a table is aliased, it will return the alias, otherwise
        it returns the table name
        :return: :rtype: str
        """
        if self.alias:
            return self.alias
        elif self.auto_alias:
            return self.auto_alias

        return self.name

    def get_sql(self):
        """
        Gets the FROM sql for a table
        Ex: table_name AS alias
        :return: :rtype: str
        """
        if self.alias:
            return '{0} AS {1}'.format(self.name, self.alias)
        elif self.auto_alias:
            return '{0} AS {1}'.format(self.name, self.auto_alias)
        return self.name

    def get_field_prefix(self):
        return self.name


class Join(object):

    def __init__(self, right_table=None, fields=None, condition=None, join_type='JOIN', schema=None, left_table=None, owner=None, extract_fields=True, prefix_fields=True):
        self.owner = owner
        self.left_table = None
        # self.table_join_name = None
        self.prefix_fields = prefix_fields
        self.condition = condition
        self.join_type = join_type
        self.schema = schema

        self.set_left_table(left_table=left_table)
        self.right_table = Table(
            table=right_table,
            fields=fields,
            extract_fields=extract_fields,
            prefix_fields=prefix_fields,
            owner=self.owner,
        )

    def get_sql(self):
        return '{0} {1} ON {2}'.format(self.join_type, self.right_table.get_sql(), self.get_condition())

    def set_left_table(self, left_table=None):
        if left_table:
            self.left_table = Table(
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

    def get_condition(self):
        if self.condition:
            return self.condition

        condition = ''
        left_table = self.get_left_table()
        if left_table.model is None and len(self.owner.tables):
            self.left_table = self.owner.tables[0]

        if self.right_table.type is ModelBase:
            # loop through fields to find the field for this model

            # check if this join type is for a related field
            for field in self.right_table.model._meta.get_all_related_objects():
                if field.model == self.left_table.model:
                    table_join_field = field.field.column
                    # self.table_join_name = field.get_accessor_name()
                    condition = '{0}.{1} = {2}.{3}'.format(
                        self.right_table.get_name(),
                        self.right_table.model._meta.pk.name,
                        self.left_table.get_name(),
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
                            self.right_table.get_name(),
                            table_join_field,
                            self.left_table.get_name(),
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
    }

    def __init__(self):
        self.arg_index = 0
        self.args = {}
        self.wheres = Q()

    def get_sql(self):
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

                condition = '{0} {1} ?'.format(field_name, operator)
                if wheres.negated:
                    condition = 'NOT({0})'.format(condition)

                value = self.get_condition_value(operator_str, value)
                # named_arg = '{0}_A{1}'.format(self.get_name(self.table), self.arg_index)
                named_arg = 'A{0}'.format(self.arg_index)
                self.args[named_arg] = value
                self.arg_index += 1
                condition = condition.replace('?', '%({0})s'.format(named_arg), 1)
                where_parts.append(condition)
        joined_parts = ' {0} '.format(wheres.connector).join(where_parts)
        return '({0})'.format(joined_parts)


class Group(object):

    def __init__(self, field=None, table=None):
        self.field = field
        self.table = table

    def get_name(self):
        """
        Gets the name to reference the grouped field
        :return: :rtype: str
        """
        if self.table:
            return '{0}.{1}'.format(self.table, self.field)
        return '{0}'.format(self.field)


class Sorter(object):

    def __init__(self, field=None, table=None, desc=False):
        self.desc = desc
        if field[0] == '-':
            self.desc = True
            field = field[1:]
        self.field = field
        self.table = table

    def get_name(self):
        """
        Gets the name to reference the sorted field
        :return: :rtype: str
        """
        if self.desc:
            direction = 'DESC'
        else:
            direction = 'ASC'
        if self.table:
            return '{0}.{1} {2}'.format(self.table, self.field, direction)
        return '{0} {1}'.format(self.field, direction)


class Limit(object):

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

    enable_safe_limit = False
    safe_limit = 1000

    def init_defaults(self):
        self.sql = None
        self.tables = []
        self.joins = []
        self._where = Where()
        self.groups = []
        self.sorters = []
        self._limit = None

        # self._distinct = False
        # self.table = {}
        # self.fields = []

        # self.table_index = 0
        # self.field_index = 0
        # self.arg_index = 0
        # self.window_index = 0
        #
        # self.args = {}
        # self.inner_queries = []
        #
        # self.table_alias_map = {}
        # self.managed_by = None

    def __init__(self):
        """
        @return: self
        """
        self.init_defaults()

    def from_table(self, table=None, fields=None, schema=None):
        """
        @return: self
        """
        # self.mark_dirty()

        if fields is None:
            fields = ['*']

        self.tables.append(Table(
            table=table,
            fields=fields,
            schema=schema,
            owner=self,
        ))

        return self

    def join(self, right_table=None, fields=None, condition=None, join_type='JOIN', schema=None, left_table=None, extract_fields=True, prefix_fields=True):
        """
        @return: self
        """
        # self.mark_dirty()
        self.joins.append(Join(
            left_table=left_table,
            right_table=right_table,
            fields=fields,
            condition=condition,
            join_type=join_type,
            schema=schema,
            owner=self,
            extract_fields=extract_fields,
            prefix_fields=prefix_fields
        ))
        return self

    def join_left(self, right_table=None, fields=None, condition=None, join_type='LEFT JOIN', schema=None, left_table=None, extract_fields=True, prefix_fields=True):
        """
        @return: self
        """
        return self.join(right_table=right_table, fields=fields, condition=condition, join_type=join_type, schema=schema, left_table=left_table, extract_fields=extract_fields, prefix_fields=prefix_fields)

    def where(self, q, where_type=AND):
        """
        Adds a Q object to the query's where condition
        :param where: django Q object with where condition
        :param where_type: django where type. AND, OR
        @return: self
        """
        # self.mark_dirty()
        self._where.wheres.add(q, where_type)
        return self

    def group_by(self, field=None, table=None):
        """
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
            if table.get_name() in table_names:
                table.auto_alias = 'T{0}'.format(table_index)
                table_index += 1
            table_names[table.get_name()] = True

    def get_sql(self, debug=False, use_cache=True):
        """
        @return: self
        """
        if self.sql and use_cache and not debug:
            return self.sql


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
        self.sql = sql

        return self.sql.strip()

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

    def build_select_fields(self):
        """
        @return: str
        """
        field_sql_parts = []
        for table in self.tables:
            field_sql_parts.append(table.get_fields_sql())
        for join_item in self.joins:
            if len(join_item.right_table.fields):
                field_sql_parts.append(join_item.right_table.get_fields_sql())
        sql = 'SELECT {0} '.format(', '.join(field_sql_parts))
        return sql

        # fields = []
        # tables = [self.table] + self.joins
        #
        # # loop through table list
        # for table_dict in tables:
        #
        #     # generate fields if this is a join table
        #     if table_dict['join_type']:
        #         table_join_name = ''
        #
                # if table_dict['condition'] is None:
                #
                #     if table_dict['type'] is ModelBase:
                #         # Build join condition
                #         # Loop through fields to find the field for this model
                #
                #         # check if this join type is for a related field
                #         for field in self.table['table']._meta.get_all_related_objects():
                #             if field.model == table_dict['table']:
                #                 table_join_field = field.field.column
                #                 table_join_name = field.get_accessor_name()
                #                 table_dict['condition'] = '{0}.{1} = {2}.{3}'.format(
                #                     self.get_name(table_dict),
                #                     table_join_field,
                #                     self.get_name(self.table),
                #                     table_dict['table']._meta.pk.name
                #                 )
                #                 break
                #
                #         # check if this join type is for a foreign key
                #         for field in self.table['table']._meta.fields:
                #             if (
                #                         field.get_internal_type() == 'OneToOneField' or
                #                         field.get_internal_type() == 'ForeignKey'
                #             ):
                #                 if field.rel.to == table_dict['table']:
                #                     table_join_field = field.column
                #                     table_join_name = field.name
                #                     table_dict['condition'] = '{0}.{1} = {2}.{3}'.format(
                #                         self.get_name(table_dict),
                #                         table_dict['table']._meta.pk.name,
                #                         self.get_name(self.table),
                #                         table_join_field
                #                     )
                #                     break
                #
                # if table_dict['type'] is ModelBase:
                #     if len(table_join_name) == 0:
                #         table_join_name = table_dict['table']._meta.db_table
                #
                # if table_dict['fields'][0] == '*':
                #     if table_dict['type'] is ModelBase:
                #         table_dict['fields'] = [field.column for field in table_dict['table']._meta.fields]
                #
                # new_fields = []
                # for field in table_dict['fields']:
                #     if type(field) is dict:
                #         new_fields.append(field)
                #     elif field == '*':
                #         new_fields.append(field)
                #     else:
                #         new_fields.append({
                #             '{0}__{1}'.format(table_join_name, field): field
                #         })
                # table_dict['fields'] = new_fields
        #
        #     # loop through each field for this table
        #     for field in table_dict['fields']:
        #         field_alias = None
        #
        #         # check if this field has an alias
        #         if type(field) is dict:
        #             field_alias = field.keys()[0]
        #             field = field.values()[0]
        #
        #         # determine how to reference the table for field selection
        #         table_prefix = ''
        #         if table_dict['alias']:
        #             table_prefix = '{0}.'.format(table_dict['alias'])
        #         elif table_dict['temp_alias']:
        #             table_prefix = '{0}.'.format(table_dict['temp_alias'])
        #         elif table_dict['name']:
        #             table_prefix = '{0}.'.format(table_dict['name'])
        #
        #         if type(field) is str:
        #             field_name = field
        #             if field_alias:
        #                 fields.append('{0}{1} AS {2}'.format(table_prefix, field_name, field_alias))
        #             else:
        #                 fields.append('{0}{1}'.format(table_prefix, field_name))
        #         elif isinstance(field, Aggregate):
        #             field_name = field.lookup
        #             if field_name == '*':
        #                 field_name = 'all'
        #             field_alias = field_alias or '{0}_{1}'.format(field.name.lower(), field_name)
        #             field_name = '{0}({1}.{2})'.format(field.name, self.get_name(table_dict), field.lookup)
        #             fields.append('{0} AS {1}'.format(field_name, field_alias))
        #         elif isinstance(field, DatePart):
        #             if field.auto:
        #                 if field.name == 'all':
        #                     # add the datetime object
        #                     datetime_alias = '{0}__{1}'.format(field.lookup, 'datetime')
        #                     datetime_str = field.lookup
        #                     if field.include_datetime:
        #                         fields.append('{0} AS {1}'.format(datetime_str, datetime_alias))
        #                         self.group_by(datetime_alias)
        #
        #                     # add the epoch time
        #                     epoch_alias = '{0}__{1}'.format(field.lookup, 'epoch')
        #                     fields.append('CAST(EXTRACT(EPOCH FROM MIN({0})) AS INT) AS {1}'.format(
        #                         datetime_str,
        #                         epoch_alias
        #                     ))
        #                 elif field.name == 'none':
        #                     # add the datetime object
        #                     datetime_alias = '{0}__{1}'.format(field.lookup, 'datetime')
        #                     datetime_str = field.lookup
        #                     if field.include_datetime:
        #                         fields.append('{0} AS {1}'.format(datetime_str, datetime_alias))
        #                         self.group_by(datetime_alias)
        #
        #                     # add the epoch time
        #                     epoch_alias = '{0}__{1}'.format(field.lookup, 'epoch')
        #                     fields.append('CAST(EXTRACT(EPOCH FROM {0}) AS INT) AS {1}'.format(
        #                         datetime_str,
        #                         epoch_alias
        #                     ))
        #                     self.group_by(epoch_alias)
        #                 else:
        #                     group_names = default_group_names
        #                     if field.name == 'week':
        #                         group_names = week_group_names
        #                     for group_name in group_names:
        #                         field_alias = '{0}__{1}'.format(field.lookup, group_name)
        #                         field_name = field.get_select(group_name)
        #                         fields.append('{0} AS {1}'.format(field_name, field_alias))
        #                         self.group_by(field_alias)
        #                         if field.desc:
        #                             self.order_by('-{0}'.format(field_alias))
        #                         else:
        #                             self.order_by(field_alias)
        #
        #                         # check if this is the last date grouping
        #                         if group_name == field.name:
        #                             # add the datetime object
        #                             datetime_alias = '{0}__{1}'.format(field.lookup, 'datetime')
        #                             datetime_str = 'date_trunc(\'{0}\', {1})'.format(group_name, field.lookup)
        #                             if field.include_datetime:
        #                                 fields.append('{0} AS {1}'.format(datetime_str, datetime_alias))
        #                                 self.group_by(datetime_alias)
        #
        #                             # add the epoch time
        #                             epoch_alias = '{0}__{1}'.format(field.lookup, 'epoch')
        #                             fields.append('CAST(EXTRACT(EPOCH FROM {0}) AS INT) AS {1}'.format(
        #                                 datetime_str,
        #                                 epoch_alias
        #                             ))
        #                             self.group_by(epoch_alias)
        #                             break
        #             else:
        #                 field_alias = field_alias or '{0}__{1}'.format(field.lookup, field.name)
        #                 field_name = field.get_select()
        #                 fields.append('{0} AS {1}'.format(field_name, field_alias))
        #         elif isinstance(field, WindowFunction):
        #             field_alias = field_alias or 'W{0}'.format(self.window_index)
        #             self.window_index += 1
        #             if field.lookup:
        #                 field_name = '{0}({1}.{2}) OVER({3})'.format(
        #                     field.name,
        #                     table_dict['alias'],
        #                     field.lookup,
        #                     field.over.get_sql()
        #                 )
        #             else:
        #                 field_name = '{0}() OVER({1})'.format(field.name, field.over.get_sql())
        #             fields.append('{0} AS {1}'.format(field_name, field_alias))
        #         elif type(field) is Query:
        #             field_alias = field_alias or '{0}_F{1}'.format(table_dict['alias'], self.field_index)
        #             field_name = '({0})'.format(field.get_sql())
        #             self.field_index += 1
        #             fields.append('{0}.{1} AS {2}'.format(table_dict['alias'], field_name, field_alias))
        #
        # fields = ', '.join(fields)
        # if self._distinct:
        #     query = 'SELECT DISTINCT {0} '.format(fields)
        # else:
        #     query = 'SELECT {0} '.format(fields)
        # return query

    def build_from_table(self):
        """
        @return: str
        """
        table_parts = []
        for table in self.tables:
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

        return ' '.join(join_parts)

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

    def build_order_by(self):
        """
        @return: str
        """
        if len(self.sorters):
            sorters = []
            for sorter in self.sorters:
                sorters.append(sorter.get_name())
            return 'ORDER BY {0} '.format(', '.join(sorters))
        return ''

    def build_limit(self):
        """
        @return: str
        """
        if self._limit:
            return self._limit.get_sql()
        return ''

    # def distinct(self, distinct=True):
    #     """
    #     @return: self
    #     """
    #     self._distinct = distinct
    #     return self
    #
    # def mark_dirty(self):
    #     self.sql = False
    #     self.table_index = 0
    #     self.field_index = 0
    #     self.arg_index = 0
    #     self.window_index = 0
    #     self.table_alias_map = {}

#     def create_table_dict(self, table=None, fields=['*'], schema=None, condition=None, join_type=None):
#         """
#         :type fields: list
#         @return: dict
#         """
#
#         if type(fields) is not list:
#             fields = [fields]
#
#         table_alias = None
#         if type(table) is dict:
#             table_alias = table.keys()[0]
#             table = table.values()[0]
#
#         table_type = type(table)
#         table_name = None
#         if table_type is ModelBase:
#             table_name = table._meta.db_table
#         elif table_type is str:
#             table_name = table
#         elif table_type is Query:
#             pass
# #            table_name = '({0})'.format(table.get_sql())
#
#         table_dict = {
#             'alias': table_alias,
#             'temp_alias': None,
#             'table': table,
#             'name': table_name,
#             'fields': fields,
#             'schema': schema,
#             'condition': condition,
#             'join_type': join_type,
#             'type': table_type,
#         }
#
#         if table_type is Query:
#             self.add_inner_query(table_dict)
#
#         return table_dict

    # def add_inner_query(self, table_dict):
    #     table_dict['table'].managed_by = self
    #     self.inner_queries.append(table_dict)
    #
    # def select_fields(self, fields=None):
    #     """
    #     @return: self
    #     """
    #     if type(fields) is not list:
    #         fields = [fields]
    #     self.table['fields'] = fields
    #     return self


    # def build_alias_maps(self):
    #     tables = [self.table] + self.joins
    #
    #     # loop through table list
    #     for table_dict in tables:
    #         self.table_alias_map[table_dict['name']] = table_dict['alias']
    #
    # def build_withs(self):
    #     withs = []
    #
    #     for inner_query in self.get_inner_queries():
    #         if inner_query['type'] is Query:
    #             inner_query['table'].mark_dirty()
    #             if inner_query['alias'] is None and self.managed_by is None:
    #                 inner_query['temp_alias'] = 'T{0}'.format(self.table_index)
    #                 self.table_index += 1
    #
    #     for inner_query in self.get_inner_queries():
    #         inner_query['table'].get_sql()
    #
    #     for inner_query in self.get_inner_queries():
    #         withs.append('{0} as ({1})'.format(
    #             inner_query['alias'] or inner_query['temp_alias'],
    #             inner_query['table'].get_sql()
    #         ))
    #         self.args.update(inner_query['table'].args)
    #
    #     withs.reverse()
    #     if len(withs) and self.managed_by is None:
    #         return 'WITH {0} '.format(', '.join(withs))
    #     return ''
    #
    # def build_args(self):
    #     pass



#     def get_name(self, table_dict):
#         if table_dict['type'] is Query:
#             table_dict['table'].mark_dirty()
#             return table_dict['alias'] or table_dict['temp_alias']
# #            return '({0})'.format(table_dict['table'].get_sql())
#         else:
#             return table_dict['name']

    # def get_table_identifier(self, table_dict):
    #     table_name = self.get_name(table_dict)
    #     table_alias = table_dict['alias'] or table_dict['temp_alias']
    #     if table_alias and table_alias != table_name:
    #         table_identifier = '{0} AS {1}'.format(table_name, table_alias)
    #     else:
    #         table_identifier = '{0}'.format(table_name)
    #
    #     return table_identifier

    def select(self, nest=False, bypass_safe_limit=False):
        """
        @return: list
        """
        # Check if we need to set a safe limit
        if bypass_safe_limit is False:
            if Query.enable_safe_limit:
                if self.count() > Query.safe_limit:
                    self.limit(Query.safe_limit)
        cursor = connection.cursor()
        cursor.execute(self.get_sql(), self._where.args)
        rows = self._fetch_all_as_dict(cursor)
        if nest:
            for row in rows:
                for key, value in row.items():
                    set_value_for_keypath(row, key, value, True, '__')
                    if '__' in key:
                        row.pop(key)
        return rows

    def sql_insert(self):
        pass

    def sql_update(self):
        pass

    def sql_delete(self):
        pass

    def count(self, field='*'):
        q = Query().from_table(self, fields=[
            Count(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def max(self, field):
        q = Query().from_table(self, fields=[
            Max(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def min(self, field):
        q = Query().from_table(self, fields=[
            Min(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def sum(self, field):
        q = Query().from_table(self, fields=[
            Sum(field)
        ])
        rows = q.select(bypass_safe_limit=True)
        return rows[0].values()[0]

    def avg(self, field):
        q = Query().from_table(self, fields=[
            Avg(field)
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

    def get_inner_queries(self):
        inner_queries = []
        for inner_query in self.inner_queries:
            if inner_query['type'] is Query:
                inner_queries.append(inner_query)
                inner_queries += inner_query['table'].get_inner_queries()
        return inner_queries


class QueryWindow(Query):
    def partition_by(self, group):
        return super(QueryWindow, self).group_by(group)

    def get_sql(self):
        """
        @return: self
        """
        query = self.build_partition_by_fields()
        query += self.build_order()
        query += self.build_limit()
        return query

    def build_partition_by_fields(self):
        """
        @return: str
        """
        select_sql = super(QueryWindow, self).build_groups()
        return select_sql.replace('GROUP BY', 'PARTITION BY', 1)

