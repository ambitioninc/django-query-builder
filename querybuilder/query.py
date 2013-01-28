from django.db import connection
from collections import OrderedDict
from django.db.models import Aggregate
from django.db.models.base import ModelBase


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

    def __init__(self, lookup, auto=False):
        self.lookup = lookup
        self.auto = auto

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

    query_index = 0
    field_index = 0
    arg_index = 0
    window_index = 0

    def init_defaults(self):
        self.table = {}
        self.wheres = []
        self.joins = OrderedDict()
        self.groups = []
        self.order = []
        self.limit_count = 0
        self.offset = 0
        self.args = {}
        self.query = False

    def __init__(self):
        self.init_defaults()

    def mark_dirty(self):
        self.query = False

    def create_table_dict(self, table, fields=['*'], schema=None, condition=None, join_type=None):
        table_alias = False
        table_name = False

        if type(table) is dict:
            table_alias = table.keys()[0]
            table = table.values()[0]

        if type(table) is ModelBase:
            table_alias = table_alias or table._meta.db_table
            table_name = table._meta.db_table
        elif type(table) is Query:
            table_alias = table_alias or 'Q{0}'.format(Query.query_index)
            table_name = table
            Query.query_index += 1
        elif type(table) is str:
            table_alias = table_alias or table
            table_name = table
        else:
            #TODO: throw error
            pass

        table_dict = {
            table_alias: {
                'name': table_name,
                'fields': fields,
                'schema': schema,
                'condition': condition,
                'join_type': join_type
            }
        }
        return table_dict

    def from_table(self, table, fields=['*'], schema=None):
        self.mark_dirty()
        self.table.update(self.create_table_dict(table, fields=fields, schema=schema))
        return self

    def where(self, condition, *args):
        self.mark_dirty()
        for arg in args:
            named_arg = 'A{0}'.format(Query.arg_index)
            self.args[named_arg] = arg
            Query.arg_index += 1
            condition = condition.replace('?', '%({0})s'.format(named_arg), 1)
        self.wheres.append(condition)

    def join(self, table, fields=['*'], condition=None, join_type='JOIN', schema=None, flatten=False):
        self.mark_dirty()
        self.joins.update(self.create_table_dict(table, fields=fields, schema=schema, condition=condition, join_type=join_type))
        return self

    def join_left(self, table, condition, fields=['*'], schema=None, join_type='LEFT JOIN', flatten=False):
        return self.join(table, fields=fields, condition=condition, join_type=join_type, schema=schema, flatten=flatten)

    def group_by(self, group):
        if type(group) is str:
            self.groups.append(group)
        elif type(group) is list:
            self.groups += group
        return self

    def order_by(self, order):
        if type(order) is str:
            self.order.append(order)
        elif type(order) is list:
            self.order += order
        return self

    def limit(self, limit_count, offset=0):
        self.limit_count = limit_count
        self.offset = offset
        return self

    def get_query(self):
        if self.query:
            return self.query

        query = self.build_select_fields()
        query += self.build_from_table()
        query += self.build_where()
        query += self.build_joins()
        query += self.build_groups()
        query += self.build_order()
        query += self.build_limit()
        self.query = query

        return self.query

    def build_select_fields(self):
        parts = []
        items = self.table.items() + self.joins.items()
        for table_alias, table_dict in items:
            for field in table_dict['fields']:
                field_alias = False
                field_name = False

                if type(field) is dict:
                    field_alias = field.keys()[0]
                    field = field.values()[0]

                if type(field) is str:
                    field_alias = field_alias or field
                    field_name = field
                    if field_name == field_alias:
                        parts.append('{0}.{1}'.format(table_alias, field_alias))
                    else:
                        parts.append('{0}.{1} AS {2}'.format(table_alias, field_name, field_alias))
                elif isinstance(field, Aggregate):
                    field_alias = field_alias or '{0}_{1}'.format(field.name, field.lookup)
                    field_name = '{0}({1}.{2})'.format(field.name, table_alias, field.lookup)
                    parts.append('{0} AS {1}'.format(field_name, field_alias))
                elif isinstance(field, DatePart):
                    if field.auto:
                        for group_name in default_group_names:
                            field_alias = '{0}__{1}'.format(field.lookup, group_name)
                            field_name = field.get_select(group_name)
                            parts.append('{0} AS {1}'.format(field_name, field_alias))
                            self.group_by(field_alias)
                            self.order_by(field_alias)
                            if group_name == field.name:
                                break
                    else:
                        field_alias = field_alias or '{0}__{1}'.format(field.lookup, field.name)
                        field_name = field.get_select()
                        parts.append('{0} AS {1}'.format(field_name, field_alias))
                elif isinstance(field, WindowFunction):
                    field_alias = field_alias or 'W{0}'.format(Query.window_index)
                    Query.window_index += 1
                    if field.lookup:
                        field_name = '{0}({1}.{2}) OVER({3})'.format(field.name, table_alias, field.lookup, field.over.get_query())
                    else:
                        field_name = '{0}() OVER({1})'.format(field.name, field.over.get_query())
                    parts.append('{0} AS {1}'.format(field_name, field_alias))
                elif type(field) is Query:
                    field_alias = field_alias or 'F{0}'.format(Query.field_index)
                    field_name = '({0})'.format(field.get_query())
                    Query.field_index += 1
                    parts.append('{0}.{1} AS {2}'.format(table_alias, field_name, field_alias))

        fields = ', '.join(parts)
        query = 'SELECT {0} '.format(fields)
        return query

    def build_from_table(self):
        parts = []
        for table_alias, table_dict in self.table.items():
            if type(table_dict['name']) is Query:
                parts.append('({0}) AS {1}'.format(table_dict['name'].get_query(), table_alias))
            else:
                if table_dict['name'] == table_alias:
                    parts.append('{0}'.format(table_dict['name'], table_alias))
                else:
                    parts.append('{0} AS {1}'.format(table_dict['name'], table_alias))
        table = ', '.join(parts)
        str = 'FROM {0} '.format(table)
        return str

    def build_where(self):
        if len(self.wheres):
            return 'WHERE {0} '.format(' AND '.join(self.wheres))
        return ''

    def build_joins(self):
        parts = []

        for table_alias, table_dict in self.joins.items():
            if type(table_dict['name']) is Query:
                parts.append('{0} ({1}) AS {2} ON {3} '.format(table_dict['join_type'], table_dict['name'].get_query(), table_alias, table_dict['condition']))
            else:
                if table_dict['name'] == table_alias:
                    parts.append('{0} {1} ON {2} '.format(table_dict['join_type'], table_alias, table_dict['condition']))
                else:
                    parts.append('{0} {1} AS {2} ON {3} '.format(table_dict['join_type'], table_dict['name'], table_alias, table_dict['condition']))

        return ' '.join(parts)

    def build_groups(self):
        if len(self.groups):
            return 'GROUP BY {0} '.format(', '.join(self.groups))
        return ''

    def build_order(self):
        if len(self.order):
            orders = []
            for order in self.order:
                if order[0] == '-':
                    order = '{0} DESC'.format(order[1:])
                orders.append(order)
            return 'ORDER BY {0} '.format(', '.join(orders))
        return ''

    def build_limit(self):
        limit_str = ''
        if self.limit_count > 0:
            limit_str += 'LIMIT {0} '.format(self.limit_count)
        if self.offset > 0:
            limit_str += 'OFFSET {0} '.format(self.offset)
        return limit_str

    def fetch_rows(self):
        cursor = connection.cursor()
        cursor.execute(self.get_query(), self.args)
        return self._fetch_all_as_dict(cursor)

    def _fetch_all_as_dict(self, cursor):
        desc = cursor.description
        return [
            dict(zip([col[0] for col in desc], row))
            for row in cursor.fetchall()
        ]


class QueryWindow(Query):

    def partition_by(self, group):
        return super(QueryWindow, self).group_by(group)

    def get_query(self):
        query = self.build_partition_by_fields()
        query += self.build_order()
        query += self.build_limit()
        return query

    def build_partition_by_fields(self):
        select_sql = super(QueryWindow, self).build_groups()
        return select_sql.replace('GROUP BY', 'PARTITION BY', 1)
