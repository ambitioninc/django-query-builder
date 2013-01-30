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

    def init_defaults(self):
        self.table = {}
        self.table_alias = ''
        self.table_dict = {}
        self.wheres = []
        self.joins = OrderedDict()
        self.groups = []
        self.order = []
        self.limit_count = 0
        self.offset = 0
        self.window_index = 0
        self.field_index = 0
        self.query_index = 0
        self.query_prefix = False
        self.arg_index = 0
        self.args = {}
        self.query = False
        self.join_format = 'flatten'
        self.subqueries = []

    def __init__(self):
        self.init_defaults()

    def mark_dirty(self):
        self.query = False
        self.arg_index = 0

    def create_table_dict(self, table, fields=['*'], schema=None, condition=None, join_type=None, join_format=None):
        table_alias = False
        table_name = False
        model = None
        query = None
        if join_format:
            self.join_format = join_format

        if type(table) is dict:
            table_alias = table.keys()[0]
            table = table.values()[0]

        if type(table) is ModelBase:
            table_alias = table_alias or table._meta.db_table
            table_name = table._meta.db_table
            model = table
        elif type(table) is Query:
            table_alias = table_alias or 'Q{0}'.format(self.query_index)
            query = table
            self.query_index += 1
            self.subqueries.append(table)
        elif type(table) is str:
            table_alias = table_alias or table
            table_name = table
        else:
            #TODO: throw error
            pass



        if join_type:
            if condition is None:
                if model:
                    # Build join condition
                    # Loop through fields to find the field for this model
                    table_join_field = ''
                    table_join_name = ''

                    # check if this join type is for a related field
                    for field in self.table_dict['model']._meta.get_all_related_objects():
                        if field.model == model:
                            table_join_field = field.field.column
                            table_join_name = field.get_accessor_name()
                            condition = '{0}.{1} = {2}.{3}'.format(table_alias, table_join_field, self.table_dict['name'], model._meta.pk.name)
                            break

                    # check if this join type is for a foreign key
                    for field in self.table_dict['model']._meta.fields:
                        if field.get_internal_type() == 'OneToOneField' or field.get_internal_type() == 'ForeignKey':
                            if field.rel.to == model:
                                table_join_field = field.column
                                table_join_name = field.name
                                condition = '{0}.{1} = {2}.{3}'.format(table_alias, model._meta.pk.name, self.table_dict['name'], table_join_field)
                                break

                    if fields[0] == '*':
                        fields = [field.column for field in model._meta.fields]

                    new_fields = []
                    for field in fields:
                        if type(field) is dict:
                            new_fields.append(field)
                        else:
                            new_fields.append({'{0}__{1}'.format(table_join_name, field): field})
                    fields = new_fields

        table_dict = {
            table_alias: {
                'name': table_name,
                'fields': fields,
                'schema': schema,
                'condition': condition,
                'join_type': join_type,
                'model': model,
                'query': query
            }
        }

        return table_dict

    def from_table(self, table, fields=['*'], schema=None, join_format=None):
        self.mark_dirty()
        if type(fields) is not list:
            fields = [fields]
        self.table.update(self.create_table_dict(table, fields=fields, schema=schema, join_format=join_format))
        self.table_alias = self.table.keys()[0]
        self.table_dict = self.table.values()[0]
        return self

    def where(self, condition, *args):
        self.mark_dirty()
        self.wheres.append({
            'condition': condition,
            'args': args
        })

    def join(self, table, fields=['*'], condition=None, join_type='JOIN', schema=None):
        self.mark_dirty()
        self.joins.update(self.create_table_dict(table, fields=fields, schema=schema, condition=condition, join_type=join_type))
        return self

    def join_left(self, table, fields=['*'], condition=None, join_type='LEFT JOIN', schema=None):
        return self.join(table, fields=fields, condition=condition, join_type=join_type, schema=schema)

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

        # assign query prefix
        self.query_prefix = self.query_prefix or 'ID0'

        # assign subquery prefixes
        subquery_index = 0
        for subquery in self.subqueries:
            subquery.mark_dirty()
            subquery.query_prefix = '{0}_{1}'.format(self.query_prefix, subquery_index)
            subquery.get_query()
            self.args.update(subquery.args)
            subquery_index += 1

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
                    field_alias = field_alias or 'W{0}'.format(self.window_index)
                    self.window_index += 1
                    if field.lookup:
                        field_name = '{0}({1}.{2}) OVER({3})'.format(field.name, table_alias, field.lookup, field.over.get_query())
                    else:
                        field_name = '{0}() OVER({1})'.format(field.name, field.over.get_query())
                    parts.append('{0} AS {1}'.format(field_name, field_alias))
                elif type(field) is Query:
                    field_alias = field_alias or 'F{0}'.format(self.field_index)
                    field_name = '({0})'.format(field.get_query())
                    self.field_index += 1
                    parts.append('{0}.{1} AS {2}'.format(table_alias, field_name, field_alias))

        fields = ', '.join(parts)
        query = 'SELECT {0} '.format(fields)
        return query

    def build_from_table(self):
        parts = []
        for table_alias, table_dict in self.table.items():
            if table_dict['query']:
                parts.append('({0}) AS {1}'.format(table_dict['query'].get_query(), table_alias))
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
            wheres = []
            for where in self.wheres:
                condition = where['condition']
                for arg in where['args']:
                    named_arg = '{0}_A{1}'.format(self.query_prefix, self.arg_index)
                    self.args[named_arg] = arg
                    self.arg_index += 1
                    condition = condition.replace('?', '%({0})s'.format(named_arg), 1)
                wheres.append(condition)
            return 'WHERE {0} '.format(' AND '.join(wheres))
        return ''

    def build_joins(self):
        parts = []

        for table_alias, table_dict in self.joins.items():
            if table_dict['query']:
                parts.append('{0} ({1}) AS {2} ON {3} '.format(table_dict['join_type'], table_dict['query'].get_query(), table_alias, table_dict['condition']))
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
        rows = self._fetch_all_as_dict(cursor)
        if self.join_format == 'nest':
            for row in rows:
                for key, value in row.items():
                    set_value_for_keypath(row, key, value, True, '__')
                    row.pop(key)


        return rows

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
