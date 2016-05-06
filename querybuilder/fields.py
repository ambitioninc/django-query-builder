import abc

from six import string_types, with_metaclass


class FieldFactory(object):
    """
    Creates the correct field class based on the type of the passed field
    """

    def __new__(cls, field, *args, **kwargs):
        """
        Determines which type of field class to instantiate based on the field argument

        :param field: The field used in determining which type of Field object to return.
            This can be a string of the field name, a dict of {'alias': field},
            or a ``Field``
        :type table: str or dict or :class:`Field <querybuilder.fields.Field>`

        :return: The Field instance if a valid type was determined, otherwise None
        :rtype: :class:`Field <querybuilder.fields.Field>` or None
        """
        field_type = type(field)
        if field_type is dict:
            kwargs.update(alias=list(field.keys())[0])
            field = list(field.values())[0]
            field_type = type(field)

        if isinstance(field, string_types):
            return SimpleField(field, **kwargs)
        elif isinstance(field, Field):
            for key, value in kwargs.items():
                setattr(field, key, value)
            return field
        return None


class Field(with_metaclass(abc.ABCMeta, object)):
    """
    Abstract field class that all field types extend.

    Properties:

        name: str
            The name that identifies this table if there is no alias

        alias: str
            The optional alias used to identify this table

        auto_alias: str
            An alias that is set automatically by the Query if needed for inner query
            namespacing

        ignore: bool
            If set to True before the field is added to a table, this field will be
            ignored and not actually added to the table list. Typically used for fields
            that will create other fields like '*' or auto date fields.

        auto: bool
            This is a flag that is read when adding fields which could indicate some
            other fields need to be automatically created.
    """

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None):
        """
        :param field: A string of a field name
        :type field: str

        :param table: A Table instance used to disambiguate the field. This is optional in
            simple queries
        :type table: :class:`Table <querybuilder.tables.Table>`

        :param alias: An alias to be used for this field
        :type alias: str

        :param cast: A data type name this field should be cast to. Ex: 'float'
        :type cast: str

        :param distinct: Indicates if a DISTINCT flag should be added during sql generation
        :type cast: bool
        """
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

        :return: the sql for this field used in the SELECT portion of the query
        :rtype: str
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
        """
        Gets the name for the field and returns it. This identifies the field if there
        is not an alias set.

        :return: The name for the field
        :rtype: str
        """
        alias = self.get_alias()
        if alias:
            return alias
        return self.name

    def get_alias(self):
        """
        Gets the alias for the field or the auto_alias if one is set.
        If there isn't any kind of alias, None is returned.

        :return: The field alias, auto_alias, or None
        :rtype: str or None
        """
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
        Gets the name for the field of how it should be referenced within a query.
        It will be prefixed with the table name or table alias

        :return: the name to reference the field within a query
        :rtype: str
        """
        alias = self.get_alias()
        if alias:
            return alias
        return self.get_select_sql()

    def get_select_sql(self):
        """
        Gets the SELECT field portion for the field without the alias. If the field
        has a table, it will be included here like table.field

        :return: Gets the SELECT field portion for the field without the alias
        :rtype: str
        """
        if self.table:
            return '{0}.{1}'.format(self.table.get_identifier(), self.name)
        return '{0}'.format(self.name)

    def before_add(self):
        """
        Template method to be implemented by subclasses. This is called
        before the field is actually added to a table
        """
        pass

    def set_table(self, table):
        """
        Setter for the table. This is meant to be extended by any subclass that might need
        to do additional processing with the table it belongs to. Ex: aggregate functions
        which reference multiple fields can set their inner fields' table.
        """
        self.table = table


class SimpleField(Field):
    """
    A field that is created with just the string name of the field
    """

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None):
        """
        Sets the name of the field to the passed in field value

        :param field: A string of a field name
        :type field: str

        :param table: A Table instance used to disambiguate the field. This is optional in
            simple queries
        :type table: :class:`Table <querybuilder.tables.Table>`

        :param alias: An alias to be used for this field
        :type alias: str

        :param cast: A data type name this field should be cast to. Ex: 'float'
        :type cast: str

        :param distinct: Indicates if a DISTINCT flag should be added during sql generation
        :type cast: bool
        """
        super(SimpleField, self).__init__(field, table, alias, cast, distinct)
        self.name = field


class JsonField(SimpleField):
    """
    Used to access postgres native json fields
    """
    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, key=None):
        super(JsonField, self).__init__(field, table, alias, cast, distinct)
        self.key = key

    def get_select_sql(self):
        if self.table:
            return '{0}.{1}->\'{2}\''.format(self.table.get_identifier(), self.name, self.key)
        return '{0}->\'{1}\''.format(self.name, self.key)

    def get_where_key(self):
        if self.table:
            return '{0}.{1}->>\'{2}\''.format(self.table.get_identifier(), self.name, self.key)
        return '{0}->>\'{1}\''.format(self.name, self.key)


class MultiField(Field):
    """
    A field that contains one or more nested fields
    """

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None):
        # TODO: implement handling of more than one nested field
        super(MultiField, self).__init__(field, table, alias, cast, distinct)
        self.field = FieldFactory(field)
        if self.table:
            self.field.set_table(self.table)

    def set_table(self, table):
        """
        Setter for the table of this field. Also sets the inner field's table.
        """
        super(MultiField, self).set_table(table)
        if self.field and self.field.table is None:
            self.field.set_table(self.table)

    def get_field_identifier(self):
        """
        Gets the identifier of the nested field

        :return: the identifier of the nested field
        :rtype: str
        """
        return self.field.get_identifier()


class ExpressionField(Field):
    pass


class AggregateField(MultiField):
    """
    The base class for aggregate functions and window functions.

    Properties:

        function_name: str
            The aggregate function name. This is used to automatically generate the sql
            for simple aggregate functions.
    """
    function_name = None

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, over=None):
        """
        Sets the field to a field instance because aggregate functions are treated as fields
        that perform an operation on a db column

        :param field: A string of a field name
        :type field: str

        :param table: A Table instance used to disambiguate the field. This is optional in
            simple queries
        :type table: :class:`Table <querybuilder.tables.Table>`

        :param alias: An alias to be used for this field
        :type alias: str

        :param cast: A data type name this field should be cast to. Ex: 'float'
        :type cast: str

        :param distinct: Indicates if a DISTINCT flag should be added during sql generation
        :type cast: bool

        :param over: The QueryWindow to perform the aggregate function over
        :type over: :class:`QueryWindow <querybuilder.query.QueryWindow>`
        """
        super(AggregateField, self).__init__(field, table, alias, cast, distinct)
        self.name = self.function_name
        self.over = over

        field_name = None
        if self.field and isinstance(self.field.field, string_types):
            field_name = self.field.field
            if field_name == '*':
                field_name = 'all'

        if field_name:
            self.auto_alias = '{0}_{1}'.format(field_name, self.name.lower())
        else:
            self.auto_alias = self.name.lower()

    def get_select_sql(self):
        """
        Gets the SELECT field portion for the field without the alias. If the field
        has a table, it will be included here like AggregateFunction(table.field)

        :return: Gets the SELECT field portion for the field without the alias
        :rtype: str
        """
        return '{0}({1}{2}){3}'.format(
            self.name.upper(),
            self.get_distinct(),
            self.get_field_identifier(),
            self.get_over(),
        )

    def get_field_identifier(self):
        """
        Gets the identifier of the field used in the aggregate function

        :return: the identifier of the field used in the aggregate function
        :rtype: str
        """
        return self.field.get_identifier()

    def get_over(self):
        """
        Gets the over clause to be used in the window function sql

        :returns: the over clause to be used in the window function sql
        :rtype: str
        """
        if self.over:
            return ' {0}'.format(self.over.get_sql())
        return ''

    def get_distinct(self):
        if self.distinct:
            return 'DISTINCT '
        return ''


class CountField(AggregateField):
    """
    Count aggregation
    """
    function_name = 'Count'


class AvgField(AggregateField):
    """
    Average aggregation
    """
    function_name = 'Avg'


class MaxField(AggregateField):
    """
    Maximum aggregation
    """
    function_name = 'Max'


class MinField(AggregateField):
    """
    Minimum aggregation
    """
    function_name = 'Min'


class StdDevField(AggregateField):
    """
    Standard deviation aggregation
    """
    function_name = 'StdDev'


class NumStdDevField(AggregateField):
    """
    Number of standard deviations from the average aggregation
    """
    function_name = 'num_stddev'

    def get_select_sql(self):
        """
        To calculate the number of standard deviations calculate the difference
        of the field and the average and divide the difference by the standard
        deviation
        """
        return '(CASE WHEN (STDDEV({0}){1}) <> 0 THEN (({0} - (AVG({0}){1})) / (STDDEV({0}){1})) ELSE 0 END)'.format(
            self.get_field_identifier(),
            self.get_over(),
        )


class SumField(AggregateField):
    """
    Summation aggregation
    """
    function_name = 'Sum'


class VarianceField(AggregateField):
    """
    Variance window function
    """
    function_name = 'Variance'


class RowNumberField(AggregateField):
    """
    Row number window function
    """
    function_name = 'row_number'

    def get_field_identifier(self):
        return ''


class RankField(AggregateField):
    """
    Rank window function
    """
    function_name = 'rank'

    def get_field_identifier(self):
        return ''


class DenseRankField(AggregateField):
    """
    Dense rank window function
    """
    function_name = 'dense_rank'

    def get_field_identifier(self):
        return ''


class PercentRankField(AggregateField):
    """
    Percent rank window function
    """
    function_name = 'percent_rank'

    def get_field_identifier(self):
        return ''


class CumeDistField(AggregateField):
    """
    Cume dist window function
    """
    function_name = 'cume_dist'

    def get_field_identifier(self):
        return ''


class NTileField(AggregateField):
    """
    NTile window function
    """
    function_name = 'ntile'

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, over=None, num_buckets=1):
        """
        Sets the num_buckets for ntile

        :param field: A string of a field name
        :type field: str

        :param table: A Table instance used to disambiguate the field. This is optional in
            simple queries
        :type table: :class:`Table <querybuilder.tables.Table>`

        :param alias: An alias to be used for this field
        :type alias: str

        :param cast: A data type name this field should be cast to. Ex: 'float'
        :type cast: str

        :param distinct: Indicates if a DISTINCT flag should be added during sql generation
        :type cast: bool

        :param over: The QueryWindow to perform the aggregate function over
        :type over: :class:`QueryWindow <querybuilder.query.QueryWindow>`

        :param num_buckets: Number of buckets to use for ntile
        :type num_buckets: int
        """
        super(NTileField, self).__init__(field, table, alias, cast, distinct, over)
        self.num_buckets = num_buckets

    def get_field_identifier(self):
        """
        Returns the number of buckets

        :return: the number of buckets used for the ntile function
        :rtype: int
        """
        return self.num_buckets


class LeadLagField(AggregateField):
    """
    Base class for lag and lead window functions
    """

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, over=None, offset=1, default=None):
        """
        Sets the offset and default value for the lag/lead calculation

        :param field: A string of a field name
        :type field: str

        :param table: A Table instance used to disambiguate the field. This is optional in
            simple queries
        :type table: :class:`Table <querybuilder.tables.Table>`

        :param alias: An alias to be used for this field
        :type alias: str

        :param cast: A data type name this field should be cast to. Ex: 'float'
        :type cast: str

        :param distinct: Indicates if a DISTINCT flag should be added during sql generation
        :type cast: bool

        :param over: The QueryWindow to perform the aggregate function over
        :type over: :class:`QueryWindow <querybuilder.query.QueryWindow>`

        :param offset: The offset number of rows which to calculate the lag/lead
        :type offset: int

        :param default: The default value to use if the offset doesn't find a field
        :type default: number or str or object
        """
        super(LeadLagField, self).__init__(field, table, alias, cast, distinct, over)
        self.offset = offset
        self.default = default

    def get_field_identifier(self):
        """
        Return the lag/lead function with the offset and default value
        """
        if self.default is None:
            return '{0}, {1}'.format(self.field.get_select_sql(), self.offset)
        return "{0}, {1}, '{2}'".format(self.field.get_select_sql(), self.offset, self.default)


class LagField(LeadLagField):
    """
    Lag window function
    """
    function_name = 'lag'


class LeadField(LeadLagField):
    """
    Lead window function
    """
    function_name = 'lead'


class LeadLagDifferenceField(LeadLagField):
    """
    Base class for lag difference and lead difference window functions
    """
    def get_select_sql(self):
        """
        Calculate the difference between this record's value and the lag/lead record's value
        """
        return '(({0}) - ({1}({2}){3}))'.format(
            self.field.get_select_sql(),
            self.name.upper(),
            self.get_field_identifier(),
            self.get_over(),
        )


class LagDifferenceField(LeadLagDifferenceField):
    """
    Lag difference window function
    """
    function_name = 'lag'


class LeadDifferenceField(LeadLagDifferenceField):
    """
    Lead difference window function
    """
    function_name = 'lead'


class FirstValueField(AggregateField):
    """
    First value window function
    """
    function_name = 'first_value'


class LastValueField(AggregateField):
    """
    Last value window function
    """
    function_name = 'last_value'


class NthValueField(AggregateField):
    """
    Nth value window function
    """
    function_name = 'nth_value'

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, over=None, n=1):
        """
        Sets the Nth value

        :param field: A string of a field name
        :type field: str

        :param table: A Table instance used to disambiguate the field. This is optional in
            simple queries
        :type table: :class:`Table <querybuilder.tables.Table>`

        :param alias: An alias to be used for this field
        :type alias: str

        :param cast: A data type name this field should be cast to. Ex: 'float'
        :type cast: str

        :param distinct: Indicates if a DISTINCT flag should be added during sql generation
        :type cast: bool

        :param over: The QueryWindow to perform the aggregate function over
        :type over: :class:`QueryWindow <querybuilder.query.QueryWindow>`

        :param n: the n value to use for the Nth value function
        :type n: int
        """
        super(NthValueField, self).__init__(field, table, alias, cast, distinct, over)
        self.n = n

    def get_field_identifier(self):
        """
        Returns the field's sql and the n value

        :return: the field's sql and the n value
        :rtype: str
        """
        return '{0}, {1}'.format(self.field.get_select_sql(), self.n)


class DatePartField(MultiField):
    """
    Base class for all date part fields

    Properties:

        group_name: str
            The name of the date part
    """
    group_name = None

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, auto=False, desc=False,
                 include_datetime=False):
        """
        :param field: A string of a field name
        :type field: str

        :param table: A Table instance used to disambiguate the field. This is optional in
            simple queries
        :type table: :class:`Table <querybuilder.tables.Table>`

        :param alias: An alias to be used for this field
        :type alias: str

        :param cast: A data type name this field should be cast to. Ex: 'float'
        :type cast: str

        :param distinct: Indicates if a DISTINCT flag should be added during sql generation
        :type cast: bool

        :param auto: Set to True for this date field to auto generate the necessary other date parts and
            apply the appropriate groupings. Defaults to False
        :type auto: bool

        :param desc: If this is set to True, the results will be sorted by the datetime field in
            descending order. Defaults to False
        :type desc: bool

        :param include_datetime: If set to True, datetime objects will be returned in addition to the
            unix timestamp. Defaults to False.
        :type include_datetime: bool
        """
        super(DatePartField, self).__init__(field, table, alias, cast, distinct)
        self.name = self.group_name
        self.auto = auto
        self.desc = desc
        self.include_datetime = include_datetime

        if self.cast is None:
            self.cast = 'INT'

        self.auto_alias = '{0}__{1}'.format(self.field.get_name(), self.name)

    def get_select_sql(self):
        """
        Extract the date part from the date field

        :return: The EXTRACT sql portion for this field
        :rtype: str
        """
        return 'EXTRACT({0} FROM {1})'.format(self.name, self.field.get_select_sql())

    def before_add(self):
        """
        Generate auto fields for this date part if auto is True.
        """
        if self.auto:
            self.ignore = True
            self.generate_auto_fields()

    def generate_auto_fields(self):
        """
        Generates any auto fields needed to properly group this date part.
        Ex: a Day field will create Year, Month, Day fields and group by Year, Month, Day
        """
        # ignore the original date field
        self.ignore = True
        datetime_str = None

        # create an alias for the unix timestamp extraction
        epoch_alias = '{0}__{1}'.format(self.field.get_name(), 'epoch')

        if self.name == 'all':
            datetime_str = self.field
            self.add_to_table(AllEpoch(datetime_str, table=self.table, cast=self.cast), epoch_alias)
            # do not add the date order by for "all" grouping because we want to order by rank
            return
        elif self.name == 'none':
            datetime_str = self.field
            self.add_to_table(Epoch(datetime_str, table=self.table, cast=self.cast), epoch_alias, add_group=True)
        else:
            group_names = default_group_names
            if self.name == 'week':
                group_names = week_group_names

            group_name_index = group_names.index(self.name) + 1
            for group_name in group_names[0:group_name_index]:
                field_alias = '{0}__{1}'.format(self.field.get_name(), group_name)
                auto_field = group_map[group_name](self.field, table=self.table, cast=self.cast)
                self.add_to_table(auto_field, field_alias, add_group=True)

                # check if this is the last date grouping
                if group_name == self.name:
                    datetime_str = self.field
                    self.add_to_table(
                        GroupEpoch(
                            datetime_str,
                            date_group_name=group_name,
                            table=self.table,
                            cast=self.cast,
                        ),
                        epoch_alias,
                        add_group=True
                    )

        if self.desc:
            self.table.owner.order_by('-{0}'.format(epoch_alias))
        else:
            self.table.owner.order_by(epoch_alias)

    def add_to_table(self, field, alias, add_group=False):
        """
        Adds this field to the field's table and optionally group by it

        :param field: The field to add to the table
        :type field: str or :class:`Field <querybuilder.fields.Field>`

        :param alias: The alias for the field
        :type alias: str

        :param add_group: Whether or not the table should group by this field
        :type: bool
        """
        self.table.add_field({
            alias: field
        })
        if add_group:
            self.table.owner.group_by(alias)


class AllTime(DatePartField):
    """
    Date group will be over the whole time range
    """
    group_name = 'all'

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, auto=False, desc=False,
                 include_datetime=False):
        super(AllTime, self).__init__(field, table, alias, cast, distinct, auto, desc, include_datetime)
        self.auto = True


class NoneTime(DatePartField):
    """
    No date grouping is used
    """
    group_name = 'none'

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, auto=False, desc=False,
                 include_datetime=False):
        super(NoneTime, self).__init__(field, table, alias, cast, distinct, auto, desc, include_datetime)
        self.auto = True


class Year(DatePartField):
    """
    Extract the year from the datetime
    """
    group_name = 'year'


class Month(DatePartField):
    """
    Extract the month from the datetime
    """
    group_name = 'month'


class Day(DatePartField):
    """
    Extract the day from the datetime
    """
    group_name = 'day'


class Hour(DatePartField):
    """
    Extract the hour from the datetime
    """
    group_name = 'hour'


class Minute(DatePartField):
    """
    Extract the minute from the datetime
    """
    group_name = 'minute'


class Second(DatePartField):
    """
    Extract the second from the datetime
    """
    group_name = 'second'


class Week(DatePartField):
    """
    Extract the week from the datetime
    """
    group_name = 'week'


class Epoch(DatePartField):
    """
    Extract the epoch from the datetime
    """
    group_name = 'epoch'

    def __init__(self, field=None, table=None, alias=None, cast=None, distinct=None, auto=False, desc=False,
                 include_datetime=False, date_group_name=None):
        self.date_group_name = date_group_name
        super(Epoch, self).__init__(field, table, alias, cast, distinct, auto, desc, include_datetime)


class GroupEpoch(Epoch):
    """
    Epoch used for a date grouping
    """

    def get_select_sql(self):
        return 'EXTRACT({0} FROM date_trunc(\'{1}\', {2}))'.format(
            self.name,
            self.date_group_name,
            self.field.get_identifier()
        )


class AllEpoch(Epoch):
    """
    Epoch used for all grouping
    """
    def get_select_sql(self):
        return 0


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
