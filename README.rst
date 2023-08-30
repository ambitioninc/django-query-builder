.. image:: https://travis-ci.org/ambitioninc/django-query-builder.png
   :target: https://travis-ci.org/ambitioninc/django-query-builder

.. image:: https://coveralls.io/repos/ambitioninc/django-query-builder/badge.png?branch=develop
    :target: https://coveralls.io/r/ambitioninc/django-query-builder?branch=develop

.. image:: https://pypip.in/v/django-query-builder/badge.png
    :target: https://crate.io/packages/django-query-builder/
    :alt: Latest PyPI version

.. image:: https://pypip.in/d/django-query-builder/badge.png
    :target: https://crate.io/packages/django-query-builder/

django-query-builder
====================
querybuilder is a django library for assisting with the construction and
execution of sql. This is not meant to replace django querysets; it is meant
for managing complex queries and helping perform database operations that
django doesn't handle.

Why use querybuilder?
---------------------
The django querybuilder allows you to control all parts of the query
construction. This is happens more clearly because the function calls more
closely represent the actual sql keywords.

Why not just use django's .raw() function?
------------------------------------------
While the raw function lets you execute custom sql, it doesn't provide any way
for the developer to build the query dynamically. Users lacking experience
writing "raw" sql should avoid using querybuilder and stick with django's
querysets. The querybuilder's query construction closely mirrors writing sql,
where django querysets simplify the sql generation process for simple queries.

Requirements
------------
* Python 3.8 - 3.9
* Django 2.2 - 4.1
* Postgres 9.3+

Installation
------------
To install the latest release, type::

    pip install django-query-builder

To install the latest code directly from source, type::

    pip install git+git://github.com/ambitioninc/django-query-builder.git

Documentation
-------------

Full documentation is available at http://django-query-builder.readthedocs.org

License
-------
MIT License (see LICENSE)
