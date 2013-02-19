import abc
from django.db.models import Aggregate


class FieldFactory(object):
    def __new__(cls, field, *args, **kwargs):
        field_type = type(field)
        if field_type is dict:
            kwargs.update(alias=field.keys()[0])
            field = field.values()[0]
            field_type = type(field)

        if field_type is str:
            return SimpleField(field, **kwargs)
        elif isinstance(field, Aggregate):
            return AggregateField(field, **kwargs)
        elif isinstance(field, DatePart):
            return field


class Field(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, field, table=None, alias=None):
        self.field = field
        self.name = None
        self.table = table
        self.alias = alias
        self.auto_alias = None
        self.ignore = False
        self.auto = False

    def get_alias(self):
        alias = None
        if self.alias:
            alias = self.alias
        elif self.auto_alias:
            alias = self.auto_alias

        if self.table.prefix_fields:
            field_prefix = self.table.get_field_prefix()
            if alias:
                alias = '{0}__{1}'.format(field_prefix, alias)
            else:
                alias = '{0}__{1}'.format(field_prefix, self.name)

        return alias

    @abc.abstractmethod
    def get_identifier(self):
        """
        Gets the name for the field of how it should
        be references within a query. It will be
        prefixed with the table name or table alias
        :return: :rtype: str
        """
        pass

    @abc.abstractmethod
    def get_sql(self):
        """
        Gets the FROM sql part for a field
        Ex: field_name AS alias
        :return: :rtype: str
        """
        pass


class SimpleField(Field):
    def __init__(self, field, table=None, alias=None):
        super(SimpleField, self).__init__(field, table, alias)
        self.name = field

    def get_identifier(self):
        return '{0}.{1}'.format(self.table.get_name(), self.name)

    def get_sql(self):
        alias = self.get_alias()
        if alias:
            return '{0} AS {1}'.format(self.get_identifier(), alias)

        return self.get_identifier()


class AggregateField(Field):
    def __init__(self, field, table=None, alias=None):
        super(AggregateField, self).__init__(field, table, alias)

        self.name = field.lookup

        if self.name == '*':
            self.name = 'all'
        self.auto_alias = '{0}_{1}'.format(field.name.lower(), self.name)

    def get_identifier(self):
        return '{0}({1}.{2})'.format(
            self.field.name.upper(),
            self.table.get_name(),
            self.field.lookup
        )

    def get_sql(self):
        alias = self.get_alias()
        if alias:
            return '{0} AS {1}'.format(self.get_identifier(), alias)

        return self.get_identifier()


class DatePart(Field):
    group_name=None

    def __init__(self, field, table=None, alias=None, auto=None, desc=None, include_datetime=False):
        super(DatePart, self).__init__(field, table, alias)

        self.name = self.group_name
        self.auto = auto
        self.desc = desc
        self.include_datetime = include_datetime

        self.auto_alias = '{0}__{1}'.format(self.field, self.name)

    def get_identifier(self):
        lookup_field = '{0}.{1}'.format(self.table.get_name(), self.field)
        return 'CAST(extract({0} from {1}) as INT)'.format(self.name, lookup_field)

    def get_sql(self):
        alias = self.get_alias()
        if alias:
            return '{0} AS {1}'.format(self.get_identifier(), alias)

        return self.get_identifier()

    def generate_auto_fields(self):
        self.ignore = True
        datetime_str = None

        epoch_alias = '{0}__{1}'.format(self.field, 'epoch')

        if self.name == 'all':
            datetime_str = self.field
            self.add_to_table(AllEpoch(datetime_str, table=self.table), epoch_alias)
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
                    self.add_to_table(GroupEpoch(datetime_str, date_group_name=group_name, table=self.table), epoch_alias, add_group=True)
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


class AllTime(DatePart):
    group_name = 'all'

    def __init__(self, lookup, auto=False, desc=False, include_datetime=False):
        super(AllTime, self).__init__(lookup, auto, desc, include_datetime)
        self.auto = True


class NoneTime(DatePart):
    group_name = 'none'

    def __init__(self, lookup, auto=False, desc=False, include_datetime=False):
        super(NoneTime, self).__init__(lookup, auto, desc, include_datetime)
        self.auto = True


class Year(DatePart):
    group_name = 'year'


class Month(DatePart):
    group_name = 'month'


class Day(DatePart):
    group_name = 'day'


class Hour(DatePart):
    group_name = 'hour'


class Minute(DatePart):
    group_name = 'minute'


class Second(DatePart):
    group_name = 'second'


class Week(DatePart):
    group_name = 'week'


class Epoch(DatePart):
    group_name = 'epoch'

    def __init__(self, field, table=None, alias=None, auto=None, desc=None, include_datetime=False, date_group_name=None):
        super(Epoch, self).__init__(field, table, alias, auto, desc, include_datetime)
        self.date_group_name = date_group_name


class GroupEpoch(Epoch):

    def get_identifier(self):
        lookup_field = '{0}.{1}'.format(self.table.get_name(), self.field)
        return 'CAST(extract({0} from date_trunc(\'{1}\', {2})) as INT)'.format(
            self.name,
            self.date_group_name,
            lookup_field
        )


class AllEpoch(Epoch):

    def get_identifier(self):
        lookup_field = '{0}.{1}'.format(self.table.get_name(), self.field)
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