import abc
from django.db.models import Aggregate
from querybuilder.groups import DatePart, AllEpoch, Epoch, default_group_names, week_group_names, group_map, GroupEpoch


class FieldFactory(object):
    def __new__(self, field, *args, **kwargs):
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
            return DatePartField(field, **kwargs)


class Field(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, field, table=None, alias=None):
        self.field = field
        self.name = None
        self.table = table
        self.alias = alias
        self.auto_alias = None
        self.ignore = False

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


class DatePartField(Field):
    def __init__(self, field, table=None, alias=None):
        super(DatePartField, self).__init__(field, table, alias)

        if self.field.auto:
            self.generate_auto_fields()
        else:
            self.auto_alias = '{0}__{1}'.format(field.lookup, field.name)

    def get_identifier(self):
        lookup_field = '{0}.{1}'.format(self.table.get_name(), self.field.lookup)
        name = self.field.get_select(lookup=lookup_field)
        return name

    def get_sql(self):
        alias = self.get_alias()
        if alias:
            return '{0} AS {1}'.format(self.get_identifier(), alias)

        return self.get_identifier()

    def generate_auto_fields(self):
        self.ignore = True
        datetime_str = None

        epoch_alias = '{0}__{1}'.format(self.field.lookup, 'epoch')

        if self.field.name == 'all':
            datetime_str = self.field.lookup
            self.add_to_table(AllEpoch(datetime_str), epoch_alias)
        elif self.field.name == 'none':
            datetime_str = self.field.lookup
            self.add_to_table(Epoch(datetime_str), epoch_alias, add_group=True)
        else:
            group_names = default_group_names
            if self.field.name == 'week':
                group_names = week_group_names

            for group_name in group_names:
                field_alias = '{0}__{1}'.format(self.field.lookup, group_name)
                self.add_to_table(group_map[group_name](self.field.lookup), field_alias, add_group=True)

                # check if this is the last date grouping
                if group_name == self.field.name:
                    datetime_str = self.field.lookup
                    self.add_to_table(GroupEpoch(datetime_str, group_name=group_name), epoch_alias, add_group=True)
                    break

        if self.field.desc:
            self.table.owner.order_by('-{0}'.format(epoch_alias))
        else:
            self.table.owner.order_by(epoch_alias)

    def add_to_table(self, field, alias, add_group=False):
        self.table.add_field({
            alias: field
        })
        if add_group:
            self.table.owner.group_by(alias)
