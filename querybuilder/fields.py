import abc


class FieldFactory(object):

    def __new__(cls, field, *args, **kwargs):
        field_type = type(field)
        if field_type is dict:
            kwargs.update(alias=field.keys()[0])
            field = field.values()[0]
            field_type = type(field)

        if field_type is str:
            return SimpleField(field, **kwargs)
        elif isinstance(field, Field):
            for key, value in kwargs.items():
                setattr(field, key, value)
            return field
        return None


class Field(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None):
        self.field = field
        self.name = None
        self.table = table
        self.alias = alias
        self.auto_alias = None
        self.ignore = False
        self.auto = False
        self.cast = cast
        self.distinct = distinct

    def get_sql(self):
        """
        Gets the SELECT sql part for a field
        Ex: field_name AS alias
        :return: :rtype: str
        """
        alias = self.get_alias()
        if alias:
            if self.cast:
                return 'CAST({0} AS {1}) AS {2}'.format(self.get_select_sql(), self.cast.upper(), alias)
            return '{0} AS {1}'.format(self.get_select_sql(), alias)

        if self.cast:
            return 'CAST({0} AS {1})'.format(self.get_identifier(), self.cast.upper())
        return self.get_identifier()

    def get_name(self):
        alias = self.get_alias()
        if alias:
            return alias
        return self.name

    def get_alias(self):
        alias = None
        if self.alias:
            alias = self.alias
        elif self.auto_alias:
            alias = self.auto_alias

        if self.table and self.table.prefix_fields:
            field_prefix = self.table.get_field_prefix()
            if alias:
                alias = '{0}__{1}'.format(field_prefix, alias)
            else:
                alias = '{0}__{1}'.format(field_prefix, self.name)

        return alias

    def get_identifier(self):
        """
        Gets the name for the field of how it should
        be referenced within a query. It will be
        prefixed with the table name or table alias
        :return: :rtype: str
        """
        alias = self.get_alias()
        if alias:
            return alias
        return self.get_select_sql()

    def get_select_sql(self):
        if self.table:
            return '{0}.{1}'.format(self.table.get_identifier(), self.name)
        return '{0}'.format(self.name)

    def before_add(self):
        pass

    def set_table(self, table):
        self.table = table


class SimpleField(Field):

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None):
        super(SimpleField, self).__init__(field, table, alias, cast, distinct)
        self.name = field


class AggregateField(Field):
    function_name = None

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, over=None):
        super(AggregateField, self).__init__(field, table, alias, cast, distinct)
        self.field = FieldFactory(field)

        self.name = self.function_name
        self.over = over

        field_name = None
        if self.field and type(self.field.field) is str:
            field_name = self.field.field
            if field_name == '*':
                field_name = 'all'

        if field_name:
            self.auto_alias = '{0}_{1}'.format(field_name, self.name.lower())
        else:
            self.auto_alias = self.name.lower()

    def get_select_sql(self):
        return '{0}({1}){2}'.format(
            self.name.upper(),
            self.get_field_identifier(),
            self.get_over(),
        )

    def get_field_identifier(self):
        return self.field.get_identifier()

    def get_over(self):
        if self.over:
            return ' {0}'.format(self.over.get_sql())
        return ''

    def set_table(self, table):
        super(AggregateField, self).set_table(table)
        if self.field and self.field.table is None:
            self.field.table = self.table


class CountField(AggregateField):
    function_name = 'Count'

    # def get_select_sql(self):
    #     sql = super(CountField, self).get_select_sql()
    #     return 'CAST({0} AS FLOAT)'.format(sql)

class AvgField(AggregateField):
    function_name = 'Avg'


class MaxField(AggregateField):
    function_name = 'Max'


class MinField(AggregateField):
    function_name = 'Min'


class StdDevField(AggregateField):
    function_name = 'StdDev'


class NumStdDevField(AggregateField):
    function_name = 'num_stddev'

    def get_select_sql(self):
        return '(({0} - (AVG({0}){1})) / (STDDEV({0}){1}))'.format(
            self.get_field_identifier(),
            self.get_over(),
        )


class SumField(AggregateField):
    function_name = 'Sum'


class VarianceField(AggregateField):
    function_name = 'Variance'


class RowNumberField(AggregateField):
    function_name = 'row_number'

    def get_field_identifier(self):
        return ''


class RankField(AggregateField):
    function_name = 'rank'

    def get_field_identifier(self):
        return ''


class DenseRankField(AggregateField):
    function_name = 'dense_rank'

    def get_field_identifier(self):
        return ''


class PercentRankField(AggregateField):
    function_name = 'percent_rank'

    def get_field_identifier(self):
        return ''


class CumeDistField(AggregateField):
    function_name = 'cume_dist'

    def get_field_identifier(self):
        return ''


class NTileField(AggregateField):
    function_name = 'ntile'

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, over=None, num_buckets=1):
        super(NTileField, self).__init__(field, table, alias, cast, distinct, over)
        self.num_buckets = num_buckets

    def get_field_identifier(self):
        return self.num_buckets


class LeadLagField(AggregateField):

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, over=None, offset=1, default=None):
        super(LeadLagField, self).__init__(field, table, alias, cast, distinct, over)
        self.offset = offset
        self.default = default

    def get_field_identifier(self):
        if self.default is None:
            return '{0}, {1}'.format(self.field.get_select_sql(), self.offset)
        return "{0}, {1}, '{2}'".format(self.field.get_select_sql(), self.offset, self.default)


class LagField(LeadLagField):
    function_name = 'lag'


class LeadField(LeadLagField):
    function_name = 'lead'


class LeadLagDifferenceField(LeadLagField):

    def get_select_sql(self):
        return '(({0}) - ({1}({2}){3}))'.format(
            self.field.get_select_sql(),
            self.name.upper(),
            self.get_field_identifier(),
            self.get_over(),
        )

    def get_field_identifier(self):
        if self.default is None:
            return '{0}, {1}'.format(self.field.get_select_sql(), self.offset)
        return "{0}, {1}, '{2}'".format(self.field.get_select_sql(), self.offset, self.default)


class LagDifferenceField(LeadLagDifferenceField):
    function_name = 'lag'


class LeadDifferenceField(LeadLagDifferenceField):
    function_name = 'lead'


class FirstValueField(AggregateField):
    function_name = 'first_value'


class LastValueField(AggregateField):
    function_name = 'last_value'


class NthValueField(AggregateField):
    function_name = 'nth_value'

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, over=None, n=1):
        super(NthValueField, self).__init__(field, table, alias, cast, distinct, over)
        self.n = n

    def get_field_identifier(self):
        return '{0}, {1}'.format(self.field.get_select_sql(), self.n)


class DatePartField(Field):
    group_name = None

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, auto=None, desc=None, include_datetime=False):
        super(DatePartField, self).__init__(field, table, alias, cast, distinct)

        self.name = self.group_name
        self.auto = auto
        self.desc = desc
        self.include_datetime = include_datetime

        self.auto_alias = '{0}__{1}'.format(self.field, self.name)

    def get_select_sql(self):
        lookup_field = '{0}.{1}'.format(self.table.get_identifier(), self.field)
        return 'CAST(extract({0} from {1}) as INT)'.format(self.name, lookup_field)

    def before_add(self):
        if self.auto:
            self.ignore = True
            self.generate_auto_fields()

    def generate_auto_fields(self):
        self.ignore = True
        datetime_str = None

        epoch_alias = '{0}__{1}'.format(self.field, 'epoch')

        if self.name == 'all':
            datetime_str = self.field
            self.add_to_table(AllEpoch(datetime_str, table=self.table), epoch_alias)
            # do not add the date order by for "all" grouping because we want to order by rank
            return
        elif self.name == 'none':
            datetime_str = self.field
            self.add_to_table(Epoch(datetime_str, table=self.table), epoch_alias, add_group=True)
        else:
            group_names = default_group_names
            if self.name == 'week':
                group_names = week_group_names

            for group_name in group_names:
                field_alias = '{0}__{1}'.format(self.field, group_name)
                auto_field = group_map[group_name](self.field, table=self.table)
                self.add_to_table(auto_field, field_alias, add_group=True)

                # check if this is the last date grouping
                if group_name == self.name:
                    datetime_str = self.field
                    self.add_to_table(
                        GroupEpoch(
                            datetime_str,
                            date_group_name=group_name,
                            table=self.table
                        ),
                        epoch_alias,
                        add_group=True
                    )
                    break

        if self.desc:
            self.table.owner.order_by('-{0}'.format(epoch_alias))
        else:
            self.table.owner.order_by(epoch_alias)

    def add_to_table(self, field, alias, add_group=False):
        self.table.add_field({
            alias: field
        })
        if add_group:
            self.table.owner.group_by(alias)


class AllTime(DatePartField):
    group_name = 'all'

    def __init__(self, lookup, auto=False, desc=False, include_datetime=False):
        super(AllTime, self).__init__(lookup, auto, desc, include_datetime)
        self.auto = True


class NoneTime(DatePartField):
    group_name = 'none'

    def __init__(self, lookup, auto=False, desc=False, include_datetime=False):
        super(NoneTime, self).__init__(lookup, auto, desc, include_datetime)
        self.auto = True


class Year(DatePartField):
    group_name = 'year'


class Month(DatePartField):
    group_name = 'month'


class Day(DatePartField):
    group_name = 'day'


class Hour(DatePartField):
    group_name = 'hour'


class Minute(DatePartField):
    group_name = 'minute'


class Second(DatePartField):
    group_name = 'second'


class Week(DatePartField):
    group_name = 'week'


class Epoch(DatePartField):
    group_name = 'epoch'

    def __init__(self, field, table=None, alias=None, auto=None, desc=None,
                 include_datetime=False, date_group_name=None):
        super(Epoch, self).__init__(field, table, alias, auto, desc, include_datetime)
        self.date_group_name = date_group_name


class GroupEpoch(Epoch):

    def get_select_sql(self):
        lookup_field = '{0}.{1}'.format(self.table.get_identifier(), self.field)
        return 'CAST(extract({0} from date_trunc(\'{1}\', {2})) as INT)'.format(
            self.name,
            self.date_group_name,
            lookup_field
        )


class AllEpoch(Epoch):

    def get_select_sql(self):
        lookup_field = '{0}.{1}'.format(self.table.get_identifier(), self.field)
        return 'CAST(extract({0} from MIN({1})) as INT)'.format(
            self.name,
            lookup_field
        )


group_map = {
    'year': Year,
    'month': Month,
    'day': Day,
    'hour': Hour,
    'minute': Minute,
    'second': Second,
    'week': Week,
    'all': AllTime,
    'none': NoneTime,
}

all_group_names = (
    'year',
    'month',
    'day',
    'hour',
    'minute',
    'second',
    'week',
    'all',
    'none',
)

allowed_group_names = (
    'year',
    'month',
    'day',
    'hour',
    'minute',
    'second',
    'week',
)

default_group_names = (
    'year',
    'month',
    'day',
    'hour',
    'minute',
    'second',
)

week_group_names = (
    'year',
    'week',
)
