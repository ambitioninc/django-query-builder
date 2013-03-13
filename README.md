# django-query-builder
querybuilder is a django library for assisting with the construction and execution of sql. This is not meant to replace django querysets; it is meant for managing complex queries and helping perform database operations that django doesn't handle.


## Requirements
- Python 2.7+
- Django 1.4+

## Why use querybuilder?
The django querybuilder allows you to control all parts of the query construction. This is happens more clearly because the function calls more closely represent the actual sql keywords.

### Why not just use django's .raw() function?
While the raw function lets you execute custom sql, it doesn't provide any way for the developer to build the query dynamically. Users lacking experience writing "raw" sql should avoid using querybuilder and stick with django's querysets. The querybuilder's query construction closely mirrors writing sql, where django querysets simplify the sql generation process for simple queries.

## Examples

### Selecting records as dictionaries

Select all fields from a table:
```python
query = Query().from_table('account')
query.select()
# [{"id": 1, "name": "Person 1"}, {"id": 2, "name": "Person 2"}]
query.get_sql()
# "SELECT account.* FROM account"
```
<table>
  <tr>
    <th>id</th><th>name</th>
  </tr>
  <tr>
    <td>1</td><td>Person 1</td>
  </tr>
  <tr>
    <td>2</td><td>Person 2</td>
  </tr>
</table>

Alias a table and fields:
```python
query = Query().from_table(
    table={
        'my_table': Account
    },
    fields=[{
        'the_id': 'id'
    }, {
        'the_name': 'name'
    }]
)
query.select()
# [{"the_id": 1, "the_name": "Person 1"}, {"the_id": 2, "the_name": "Person 2"}]
query.get_sql()
# "SELECT my_table.id AS the_id, my_table.name AS the_name FROM account AS my_table"
```
<table>
  <tr>
    <th>the_id</th><th>the_name</th>
  </tr>
  <tr>
    <td>1</td><td>Person 1</td>
  </tr>
  <tr>
    <td>2</td><td>Person 2</td>
  </tr>
</table>

### Selecting records as models
Select all fields from a table:
```python
query = Query().from_table('account')
query.select(return_models=True)
# [<Account: Account object>, <Account: Account object>]
query.get_sql()
# "SELECT account.* FROM account"
```

### Sorting

Select all fields using a django model and order by id desc:
```python
query = Query().from_table(Account).order_by('-id')
query.select()
# [{"id": 2, "name": "Person 2"}, {"id": 1, "name": "Person 1"}]
query.get_sql()
# "SELECT account.* FROM account ORDER BY id DESC"
```
<table>
  <tr>
    <th>id</th><th>name</th>
  </tr>
  <tr>
    <td>2</td><td>Person 2</td>
  </tr>
  <tr>
    <td>1</td><td>Person 1</td>
  </tr>
</table>

### Limit and Offset

Select specific fields and sort with a limit:
```python
query = Query().from_table(
    table=Account,
    fields=['name']
).order_by(
    '-id'
).limit(
    1
)
query.select()
# [{"name": "Person 2"}]
query.get_sql()
# "SELECT account.* FROM account ORDER BY id DESC LIMIT 1"
```
<table>
  <tr>
    <th>name</th>
  </tr>
  <tr>
    <td>Person 2</td>
  </tr>
</table>

### Filtering:
eq
gt
gte
lt
lte
~
&
|
contains
startswith

### Joins:


### Date functions


### Window functions


### Inner queries
```python
inner_query = Query().from_table(Account)
outer_query = Query().from_table(inner_query)
```

## Reference Material
* http://www.postgresql.org/docs/9.1/static/functions-window.html

