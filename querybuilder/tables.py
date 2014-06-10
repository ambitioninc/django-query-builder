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
        # Determine the type of the table
        table_type = type(table)
        if table_type is dict:
            kwargs.update(alias=table.keys()[0])
            table = table.values()[0]
            table_type = type(table)

        if table_type in [str, unicode]:
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
    """
    Abstract table class that all table types extend.

    Properties:

        name: str
            The name that identifies this table if there is no alias

        alias: str
            The optional alias used to identify this table

        auto_alias: str
            An alias that is set automatically by the Query if needed for inner query
            namespacing
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, table=None, fields=None, schema=None, extract_fields=False, prefix_fields=False,
                 field_prefix=None, owner=None, alias=None):
        """
        Initializes the table and sets default values
        @param table: The table name or model. This can be a string of the table
            name, a dict of {'alias': table}, a Query instance, or a django Model instance
        @type table: str or dict or Query or ModelBase
        @param fields: The fields to select from ``table``. Defaults to '*'. This can be
            a single field, a tuple of fields, or a list of fields. Each field can be a string
            or ``Field`` instance
        @type fields: str or tuple or list or Field
        @param schema: This is not implemented, but it will be a string of the db schema name
        @type schema: str
        @param extract_fields: If True, then '*' fields will be converted to individual
            fields for each column in the table. Defaults to False.
        @type extract_fields: bool
        @param prefix_fields: If True, then the table will have each of its field names
            prefixed with the field_prefix. Defaults to False.
        @type prefix_fields: bool
        @param field_prefix: The field prefix to be used in front of each field name if prefix_fields
            is set to True.
        @type field_prefix: str
        @param owner: A reference to the query managing this Table object
        @type owner: Query
        @param alias: An alias to be used for this table
        @type alias: str
        """
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
        """
        Template method meant to be overridden by subclasses. This is called
        in the __init__ before calling set_fields
        """
        pass

    def get_sql(self):
        """
        Gets the FROM sql portion for this table
        Ex: table_name AS alias
        @return: Returns the table identifier to be used in the FROM sql portion of the query
        @rtype: str
        """
        alias = self.get_alias()
        if alias:
            return '{0} AS {1}'.format(self.get_from_name(), alias)

        return self.get_identifier()

    def get_alias(self):
        """
        Gets the alias for the table or the auto_alias if one is set.
        If there isn't any kind of alias, None is returned.
        @return: The table alias, auto_alias, or None
        @rtype: str or None
        """
        alias = None
        if self.alias:
            alias = self.alias
        elif self.auto_alias:
            alias = self.auto_alias

        return alias

    def get_name(self):
        """
        Gets the name for the table and returns it. This identifies the table if there
        is not an alias set.
        @return: The name for the table
        @rtype: str
        """
        return self.name

    def get_from_name(self):
        """
        Gets the name to be used in the FROM clause for the table. This is separate
        from the get_name() method so subclasses don't always have to reference
        the table name by the FROM name. Otherwise Table subclasses like a QueryTable
        would be using the full Query sql for the get_name when getting the identifier in
        other parts of the query.
        """
        return self.name

    def get_identifier(self):
        """
        Gets the name to reference the table within a query. If
        a table is aliased, it will return the alias, otherwise
        it returns the table name
        @return: the name to reference the table within a query
        @rtype: str
        """
        alias = self.get_alias()
        if alias:
            return alias
        return self.get_name()

    def add_field(self, field):
        """
        Adds a field to this table
        @param field: This can be a string of a field name, a dict of {'alias': field}, or
            a ``Field`` instance
        @type field: str or dict or Field
        """
        field = FieldFactory(
            field,
        )
        field.set_table(self)

        # make sure field is not already added
        field_name = field.get_name()
        for existing_field in self.fields:
            if existing_field.get_name() == field_name:
                # print 'field already existed', field_name
                return

        self.before_add_field(field)
        field.before_add()

        if field.ignore is False:
            self.fields.append(field)

    def remove_field(self, field):
        """
        Removes a field from this table
        @param field: This can be a string of a field name, a dict of {'alias': field}, or
            a ``Field`` instance
        @type field: str or dict or Field
        """
        new_field = FieldFactory(
            field,
        )
        new_field.set_table(self)
        new_field_identifier = new_field.get_identifier()
        for field in self.fields:
            if field.get_identifier() == new_field_identifier:
                self.fields.remove(field)
                return

    def before_add_field(self, field):
        """
        This is a template method meant to be extended by subclasses. It is called
        during the add_field method after the field is returned from the factory,
        and before calling the field's before_add method, which is before actually
        appending the field to the list of fields.
        """
        pass

    def set_fields(self, fields):
        """
        This will clear the table's current fields and add all new fields
        @param fields: The fields to select from ``table``. This can be
            a single field, a tuple of fields, or a list of fields. Each field can be a string
            or ``Field`` instance
        @type fields: str or tuple or list of str or list of Field or Field
        """
        self.fields = []
        self.add_fields(fields)

    def add_fields(self, fields):
        """
        Adds all of the passed fields to the table's current field list
        @param fields: The fields to select from ``table``. This can be
            a single field, a tuple of fields, or a list of fields. Each field can be a string
            or ``Field`` instance
        @type fields: str or tuple or list of str or list of Field or Field
        """
        if type(fields) in [str, unicode]:
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
        @return: A list of sql for each field in this table
        @rtype: list of str
        """
        return [field.get_sql() for field in self.fields]

    def get_field_names(self):
        """
        Loop through this tables fields and calls the get_name
        method on each of them to build a list of field names
        @return: A list of field names found in this table
        @rtype: list of str
        """
        return [field.get_name() for field in self.fields]

    def get_field_identifiers(self):
        """
        Loop through this tables fields and calls the get_identifier
        method on each of them to build a list of field identifiers
        @return: A list of field identifiers found in this table
        @rtype: list of str
        """
        return [field.get_identifier() for field in self.fields]

    def get_field_prefix(self):
        """
        Gets the prefix to be used in front of each field. If no prefix is
        set, then the identifier for this table is returned
        @return: The field prefix for this table
        @rtype: str
        """
        return self.field_prefix or self.get_identifier()

    def find_field(self, field=None, alias=None):
        """
        Finds a field by name or alias.
        @param field: string of the field name or alias, dict of {'alias': field}, or a Field instance
        @type field: str or dict or Field
        @return: The field if it is found, otherwise None
        @rtype: Field or None
        """
        if alias:
            field = alias
        field = FieldFactory(field, table=self, alias=alias)
        identifier = field.get_identifier()
        for field in self.fields:
            if field.get_identifier() == identifier:
                return field
        return None


class SimpleTable(Table):
    """
    A table that is created with just the string name of the table
    """

    def init_defaults(self):
        """
        Sets the name of the table to the passed in table value
        """
        super(SimpleTable, self).init_defaults()
        self.name = self.table


class ModelTable(Table):
    """
    A table that is created by passing a django model for the table field. This allows
    fields to be extract and for joins to be made without specifying a condition.
    """

    def init_defaults(self):
        """
        Sets a model instance variable to the table value and sets the name to the
        table name as determined from the model class
        """
        super(ModelTable, self).init_defaults()
        self.model = self.table
        self.name = self.model._meta.db_table

    def before_add_field(self, field):
        """
        If extract_fields is set to True, then '*' fields will be removed and each
        individual field will read from the model meta data and added.
        """
        if self.extract_fields and field.name == '*':
            field.ignore = True
            fields = [model_field.column for model_field in self.model._meta.fields]
            self.add_fields(fields)


class QueryTable(Table):
    """
    A table that contains a Query object. This is used for inner queries in more complex
    queries, usually involving window functions or some sort of aggregation.
    """

    def init_defaults(self):
        """
        Sets a query instance variable to the table value
        """
        super(QueryTable, self).init_defaults()
        self.query = self.table
        self.query.is_inner = True


    def get_sql(self):
        return self.get_identifier()

    def get_from_name(self):
        """
        Return the query sql in the FROM clause of the query when building the table sql
        """
        return '({0})'.format(self.query.get_sql())

    def get_with_sql(self):
        return '{0} AS ({1})'.format(self.get_identifier(), self.query.get_sql())

