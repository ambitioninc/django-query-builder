Release Notes
=============

v1.2.0
------
* Add Django 2.1
* Add Django 2.2
* Add python 3.7
* Drop python 2.7
* Drop python 3.4
* Drop python 3.5
* Drop Django 1.10

v1.1.0
------
* Use tox to support more versions

v1.0.0
------
* Drop Django 1.9
* Drop Django 1.10
* Add Django 2.0
* Drop python 2.7
* Drop python 3.4

v0.15.0
-------
* Handle custom db column names
* Drop Django 1.8
* Support Django 1.10
* Support Django 1.11
* Support Python 3.6

v0.14.3
-------
* Respect return_models in upsert method when building upsert sql

v0.14.2
-------
* Fix upsert to use the proper prepare method on django fields

v0.14.1
-------
* Fix upsert to handle case when the uniqueness constraint is the pk field

v0.14.0
-------
* Drop support for django 1.7, add official support for python 3.5

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
