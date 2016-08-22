Release Notes
=============

v0.13.0
-------
* Add paginator class for json queryset
* No longer change '__' to '.' in filters. Just use a '.' where needed and use django 1.9's json field support for querying json fields

v0.12.0
-------
* Run tests with django 1.10
* Fix bug when filtering json fields with any operator other than equals
* Fix deprecated method call for django 1.10

v0.11.3
-------
* Added issubclass check for ModelBase when checking table type

v0.11.2
-------
* Use correct column name on upsert when existing record updates

v0.11.1
-------
* Get db prep values for upserts and get column name by model property names

v0.11.0
-------
* Wrap alias in double quotes to preserve case
* Fix bulk upsert column names
* Add upsert support to return affected records as dicts or models
* Implement distinct_on
* Fix tests for Postgres9.3
* Implement icontains
* Implement DISTINCT for aggregate fields

v0.10.0
-------
* Added postgres bulk upsert support

v0.9.0
------
* Added support for django 1.9 and tests with postgres 9.4 using new django json field

v0.8.1
------
* More efficient count query
* Add limit support on JsonQueryset
* Added copy method to Query object

v0.7.2
------
* Fixed queryset init args

v0.7.1
------
* Added Django 1.7 app config

v0.7.0
------
* Added basic support for filtering and ordering json fields

v0.5.10
-------
* Updated the usage examples
* Fixed infinite loop bug when a MultiField did not implement an identifier method

v0.5.9
------
* Fixed issue with certain functions for alternate databases

v0.5.8
------

* Added connection parameter to query for multiple database support
* flake8 cleanup

v0.5.7
------

* Added Python 3 compatibility
* Added sphinx docs
