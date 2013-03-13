import abc
from django.db.models.base import ModelBase
import querybuilder
from querybuilder.fields import FieldFactory


class TableFactory(object):
    """
    Creates the correct table class based on the type of the passed table
    """

    def __new__(cls, table, *args, **kwargs):
        """
        Determines which type of table class to instantiate based on the table argument
        @param table: The table used in determining which type of Table object to return.
            This can be a string of the table name, a dict of {'alias': table},
            a ``Table`` instance, a django model class, or a Query instance
        @type table: str or dict or Table or ModelBase or Query
        @return: The Table instance if a valid type was determined, otherwise None
        @rtype: Table or None
        """
        table_type = type(table)
        if table_type is dict:
            kwargs.update(alias=table.keys()[0])
            table = table.values()[0]
            table_type = type(table)

        if table_type is str:
            return SimpleTable(table, **kwargs)
        elif table_type is ModelBase:
            return ModelTable(table, **kwargs)
        elif table_type is querybuilder.query.Query:
            return QueryTable(table, **kwargs)
        elif isinstance(table, Table):
            for key, value in kwargs.items():
                setattr(table, key, value)
            return table
        return None


class Table(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, table=None, fields=None, schema=None, extract_fields=False, prefix_fields=False,
                 field_prefix=None, owner=None, alias=None):
        self.table = table
        self.owner = owner
        self.name = None
        self.alias = alias
        self.auto_alias = None
        self.fields = []
        self.schema = schema
        self.extract_fields = extract_fields
        self.prefix_fields = prefix_fields
        self.field_prefix = field_prefix

        self.init_defaults()
        if fields:
            self.set_fields(fields)

    def init_defaults(self):
        pass

    def get_sql(self):
        """
        Gets the FROM sql for a table
        Ex: table_name AS alias
        :return: :rtype: str
        """
        alias = self.get_alias()
        if alias:
            return '{0} AS {1}'.format(self.get_from_name(), alias)

        return self.get_identifier()

    def get_alias(self):
        alias = None
        if self.alias:
            alias = self.alias
        elif self.auto_alias:
            alias = self.auto_alias

        return alias

    def get_name(self):
        return self.name

    def get_from_name(self):
        return self.name

    def get_identifier(self):
        """
        Gets the name to reference the table within a query. If
        a table is aliased, it will return the alias, otherwise
        it returns the table name
        :return: :rtype: str
        """
        alias = self.get_alias()
        if alias:
            return alias
        return self.get_name()

    def add_field(self, field):
        field = FieldFactory(
            field,
        )
        field.set_table(self)
        self.before_add_field(field)
        field.before_add()

        if field.ignore is False:
            self.fields.append(field)

    def before_add_field(self, field):
        pass

    def set_fields(self, fields):
        self.fields = []
        self.add_fields(fields)

    def add_fields(self, fields):
        if type(fields) is str:
            fields = [fields]
        elif type(fields) is tuple:
            fields = list(fields)
        for field in fields:
            self.add_field(field)

    def get_field_sql(self):
        """
        Loop through this tables fields and calls the get_sql
        method on each of them to build the field list for the FROM
        clause
        :return: :rtype: str
        """
        return [field.get_sql() for field in self.fields]

    def get_field_names(self):
        return [field.get_name() for field in self.fields]

    def get_field_identifiers(self):
        return [field.get_identifier() for field in self.fields]

    def get_field_prefix(self):
        return self.field_prefix or self.get_identifier()

    def find_field(self, field=None, alias=None):
        if alias:
            field = alias
        field = FieldFactory(field, table=self, alias=alias)
        identifier = field.get_identifier()
        for field in self.fields:
            if field.get_identifier() == identifier:
                return field
        return None


class SimpleTable(Table):

    def init_defaults(self):
        super(SimpleTable, self).init_defaults()
        self.name = self.table


class ModelTable(Table):

    def init_defaults(self):
        super(ModelTable, self).init_defaults()
        self.model = self.table
        self.name = self.model._meta.db_table

    def before_add_field(self, field):
        if self.extract_fields and field.name == '*':
            field.ignore = True
            fields = [model_field.column for model_field in self.model._meta.fields]
            self.add_fields(fields)


class QueryTable(Table):

    def init_defaults(self):
        super(QueryTable, self).init_defaults()
        self.query = self.table

    def get_from_name(self):
        return '({0})'.format(self.query.get_sql())
