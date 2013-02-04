from django.db import connection
from collections import OrderedDict
from django.db.models import Aggregate
from django.db.models.base import ModelBase
from querybuilder.helpers import set_value_for_keypath


class WindowFunction(object):

    name = ''

    def __init__(self, over, lookup=None):
        self.over = over
        self.lookup = lookup


class Rank(WindowFunction):

    name = 'rank'


default_group_names = (
    'year',
    'month',
    'day',
    'hour',
    'minute',
    'second',
)


class DatePart(object):

    name = ''

    def __init__(self, lookup, auto=False, desc=False):
        self.lookup = lookup
        self.auto = auto
        self.desc = desc

    def get_select(self, name=None):
        return 'CAST(extract({0} from {1}) as INT)'.format(name or self.name, self.lookup)


class Year(DatePart):
    name = 'year'


class Month(DatePart):
    name = 'month'


class Day(DatePart):
    name = 'day'


class Hour(DatePart):
    name = 'hour'


class Minute(DatePart):
    name = 'minute'


class Second(DatePart):
    name = 'second'


class Week(DatePart):
    name = 'week'


class Query(object):

    def init_defaults(self):
        self.table = {}
        self.fields = []
        self.table_alias = ''
        self.table_dict = {}
        self.wheres = []
        self.joins = []
        self.groups = []
        self.order = []
        self.limit_count = 0
        self.offset = 0

        self.table_index = 0
        self.field_index = 0
        self.arg_index = 0
        self.window_index = 0

        self.args = {}
        self.query = False
        self.inner_queries = []

    def __init__(self):
        self.init_defaults()

    def mark_dirty(self):
        self.query = False
        self.table_index = 0
        self.field_index = 0
        self.arg_index = 0
        self.window_index = 0

    def create_table_dict(self, table, fields=['*'], schema=None, condition=None, join_type=None):
        """
        @return: dict
        """

        if type(fields) is not list:
            fields = [fields]

        table_alias = None
        static_alias = False
        if type(table) is dict:
            table_alias = table.keys()[0]
            table = table.values()[0]
            static_alias = True

        table_dict = {
            'alias': table_alias,
            'static_alias': static_alias,
            'table': table,
            'name': None,
            'fields': fields,
            'schema': schema,
            'condition': condition,
            'join_type': join_type,
            'type': type(table),
        }

        if type(table) is Query:
            self.inner_queries.append(table_dict)

        return table_dict

    def select_fields(self, fields=None):
        """
        @return: self
        """
        if type(fields) is not list:
            fields = [fields]
        self.table['fields'] = fields
        return self

    def from_table(self, table=None, fields=['*'], schema=None):
        """
        @return: self
        """
        self.mark_dirty()

        self.table = self.create_table_dict(table, fields=fields, schema=schema)

        return self

    #TODO: parse named arg conditions and convert to string
    # ex: Account__id__gt=5
    def where(self, condition, *args):
        """
        @return: self
        """
        self.mark_dirty()
        self.wheres.append({
            'condition': condition,
            'args': args
        })
        return self

    def join(self, table, fields=['*'], condition=None, join_type='JOIN', schema=None):
        """
        @return: self
        """
        self.mark_dirty()
        self.joins.append(self.create_table_dict(table, fields=fields, schema=schema, condition=condition, join_type=join_type))
        return self

    def join_left(self, table, fields=['*'], condition=None, join_type='LEFT JOIN', schema=None):
        """
        @return: self
        """
        return self.join(table, fields=fields, condition=condition, join_type=join_type, schema=schema)

    def group_by(self, group, *args):
        """
        @return: self
        """
        if type(group) is str:
            self.groups.append(group)
        elif type(group) is list:
            self.groups += group
        if len(args):
            self.group += args
        return self

    def order_by(self, order):
        """
        @return: self
        """
        if type(order) is str:
            self.order.append(order)
        elif type(order) is list:
            self.order += order
        return self

    def limit(self, limit_count, offset=0):
        """
        @return: self
        """
        self.limit_count = limit_count
        self.offset = offset
        return self

    def get_query(self):
        """
        @return: self
        """
        if self.query:
            return self.query

        #TODO: add query prefix in front of field names
        #TODO: add query prefix in front of window names
        #TODO: use self.table_alias as the query prefix

        # assign query alias
        table_dicts = [self.table] + self.joins
        for table_dict in table_dicts:
            if table_dict['alias'] is None:
                table_dict['alias'] = 'T{0}'.format(self.table_index)
                self.table_index += 1

            self.get_table_identifier(table_dict)

        # assign inner_query prefixes
        inner_query_index = 0
        for inner_query in self.inner_queries:
            # mark dirty so the args can be namespaced
            inner_query['table'].mark_dirty()


            if inner_query['static_alias'] is False:
                inner_query['alias'] = '{0}_{1}'.format(self.table['alias'], inner_query_index)
            inner_query['table'].get_query()
            self.args.update(inner_query['table'].args)
            inner_query_index += 1
            inner_query['table'].mark_dirty()

        query = self.build_select_fields()
        query += self.build_from_table()
        query += self.build_joins()
        query += self.build_where()
        query += self.build_groups()
        query += self.build_order()
        query += self.build_limit()
        self.query = query

        return self.query

    def build_select_fields(self):
        """
        @return: str
        """
        fields = []
        tables = [self.table] + self.joins

        # loop through table list
        for table_dict in tables:

            # generate fields if this is a join table
            if table_dict['join_type']:
                table_join_field = ''
                table_join_name = ''

                if table_dict['condition'] is None:

                    if table_dict['type'] is ModelBase:
                        # Build join condition
                        # Loop through fields to find the field for this model

                        # check if this join type is for a related field
                        for field in self.table['table']._meta.get_all_related_objects():
                            if field.model == table_dict['table']:
                                table_join_field = field.field.column
                                table_join_name = field.get_accessor_name()
                                table_dict['condition'] = '{0}.{1} = {2}.{3}'.format(table_dict['alias'], table_join_field, self.table['alias'], table_dict['table']._meta.pk.name)
                                break

                        # check if this join type is for a foreign key
                        for field in self.table['table']._meta.fields:
                            if field.get_internal_type() == 'OneToOneField' or field.get_internal_type() == 'ForeignKey':
                                if field.rel.to == table_dict['table']:
                                    table_join_field = field.column
                                    table_join_name = field.name
                                    table_dict['condition'] = '{0}.{1} = {2}.{3}'.format(table_dict['alias'], table_dict['table']._meta.pk.name, self.table['alias'], table_join_field)
                                    break

                if table_dict['type'] is ModelBase:
                    if len(table_join_name) == 0:
                        table_join_name = table_dict['table']._meta.db_table

                if table_dict['fields'][0] == '*':
                    if table_dict['type'] is ModelBase:
                        table_dict['fields'] = [field.column for field in table_dict['table']._meta.fields]

                new_fields = []
                for field in table_dict['fields']:
                    if type(field) is dict:
                        new_fields.append(field)
                    elif field == '*':
                        new_fields.append(field)
                    else:
                        new_fields.append({
                            '{0}__{1}'.format(table_join_name, field): field
                        })
                table_dict['fields'] = new_fields

            # loop through each field for this table
            for field in table_dict['fields']:
                field_alias = None

                # check if this field has an alias
                if type(field) is dict:
                    field_alias = field.keys()[0]
                    field = field.values()[0]

                if type(field) is str:
                    field_name = field
                    if field_alias:
                        fields.append('{0}.{1} AS {2}'.format(table_dict['alias'], field_name, field_alias))
                    else:
                        fields.append('{0}.{1}'.format(table_dict['alias'], field_name))
                elif isinstance(field, Aggregate):
                    field_name = field.lookup
                    if field_name == '*':
                        field_name = 'all'
                    field_alias = field_alias or '{0}_{1}'.format(field.name.lower(), field_name)
                    field_name = '{0}({1}.{2})'.format(field.name, table_dict['alias'], field.lookup)
                    fields.append('{0} AS {1}'.format(field_name, field_alias))
                elif isinstance(field, DatePart):
                    if field.auto:
                        for group_name in default_group_names:
                            field_alias = '{0}__{1}'.format(field.lookup, group_name)
                            field_name = field.get_select(group_name)
                            fields.append('{0} AS {1}'.format(field_name, field_alias))
                            self.group_by(field_alias)
                            if field.desc:
                                self.order_by('-{0}'.format(field_alias))
                            else:
                                self.order_by(field_alias)
                            if group_name == field.name:
                                break
                    else:
                        field_alias = field_alias or '{0}__{1}'.format(field.lookup, field.name)
                        field_name = field.get_select()
                        fields.append('{0} AS {1}'.format(field_name, field_alias))
                elif isinstance(field, WindowFunction):
                    field_alias = field_alias or 'W{0}'.format(self.window_index)
                    self.window_index += 1
                    if field.lookup:
                        field_name = '{0}({1}.{2}) OVER({3})'.format(field.name, table_alias, field.lookup, field.over.get_query())
                    else:
                        field_name = '{0}() OVER({1})'.format(field.name, field.over.get_query())
                    fields.append('{0} AS {1}'.format(field_name, field_alias))
                elif type(field) is Query:
                    field_alias = field_alias or 'F{0}'.format(self.field_index)
                    field_name = '({0})'.format(field.get_query())
                    self.field_index += 1
                    fields.append('{0}.{1} AS {2}'.format(table_alias, field_name, field_alias))

        fields = ', '.join(fields)
        query = 'SELECT {0} '.format(fields)
        return query

    def get_table_identifier(self, table_dict):
        table_identifier = ''
        table_name = ''

        if table_dict['type'] is ModelBase:
            table_dict['name'] = table_dict['table']._meta.db_table
        elif table_dict['type'] is str:
            table_dict['name'] = table_dict['table']
        elif table_dict['type'] is Query:
            table_dict['name'] = '({0})'.format(table_dict['table'].get_query())
        if table_dict['alias']:
            table_identifier = '{0} AS {1}'.format(table_dict['name'], table_dict['alias'])
        else:
            table_identifier = '{0}'.format(table_dict['name'])

        return table_identifier

    def build_from_table(self):
        """
        @return: str
        """
        str = 'FROM {0} '.format(self.get_table_identifier(self.table))
        return str

    def build_where(self):
        """
        @return: str
        """
        if len(self.wheres):
            wheres = []
            for where in self.wheres:
                condition = where['condition']
                for arg in where['args']:
                    named_arg = '{0}_A{1}'.format(self.table['alias'], self.arg_index)
                    self.args[named_arg] = arg
                    self.arg_index += 1
                    condition = condition.replace('?', '%({0})s'.format(named_arg), 1)
                wheres.append(condition)
            return 'WHERE {0} '.format(' AND '.join(wheres))
        return ''

    def build_joins(self):
        """
        @return: str
        """
        join_parts = []

        for table_dict in self.joins:

            join_parts.append('{0} {1} ON {2} '.format(table_dict['join_type'], self.get_table_identifier(table_dict), table_dict['condition']))
#            if table_dict['type'] is Query:
#                join_parts.append('{0} ({1}) AS {2} ON {3} '.format(table_dict['join_type'], table_dict['query'].get_query(), table_alias, table_dict['condition']))
#            else:
#                if table_dict['alias']:
#                    join_parts.append('{0} {1} AS {2} ON {3} '.format(table_dict['join_type'], table_dict['name'], table_alias, table_dict['condition']))
#                else:
#                    join_parts.append('{0} {1} ON {2} '.format(table_dict['join_type'], table_alias, table_dict['condition']))

        return ' '.join(join_parts)

    def build_groups(self):
        """
        @return: str
        """
        if len(self.groups):
            return 'GROUP BY {0} '.format(', '.join(self.groups))
        return ''

    def build_order(self):
        """
        @return: str
        """
        if len(self.order):
            orders = []
            for order in self.order:
                if order[0] == '-':
                    order = '{0} DESC'.format(order[1:])
                orders.append(order)
            return 'ORDER BY {0} '.format(', '.join(orders))
        return ''

    def build_limit(self):
        """
        @return: str
        """
        limit_str = ''
        if self.limit_count > 0:
            limit_str += 'LIMIT {0} '.format(self.limit_count)
        if self.offset > 0:
            limit_str += 'OFFSET {0} '.format(self.offset)
        return limit_str

    def select(self, nest=False):
        """
        @return: list
        """
        cursor = connection.cursor()
        cursor.execute(self.get_query(), self.args)
        rows = self._fetch_all_as_dict(cursor)
        if nest:
            for row in rows:
                for key, value in row.items():
                    set_value_for_keypath(row, key, value, True, '__')
                    if '__' in key:
                        row.pop(key)
        return rows

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

    def partition_by(self, group):
        return super(QueryWindow, self).group_by(group)

    def get_query(self):
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
