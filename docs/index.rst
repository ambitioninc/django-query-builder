django-query-builder Documentation
==================================
querybuilder is a django library for assisting with the construction and
execution of sql. This is not meant to replace django querysets; it is meant
for managing complex queries and helping perform database operations that
django doesn't handle. Current database support only includes postgres 9.3+.

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

Force Build
