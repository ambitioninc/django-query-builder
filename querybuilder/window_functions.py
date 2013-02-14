from querybuilder.query import Query


class WindowFunction(object):
    name = ''

    def __init__(self, over, lookup=None):
        """
        :type lookup: str
        """
        self.over = over
        self.lookup = lookup


class Rank(WindowFunction):
    name = 'rank'


class QueryWindow(Query):
    def partition_by(self, group):
        return super(QueryWindow, self).group_by(group)

    def get_query(self):
        """
        @return: self
        """
        query = self.build_partition_by_fields()
        query += self.build_order()
        query += self.build_limit()
        return query

    def build_partition_by_fields(self):
        """
        @return: str
        """
        select_sql = super(QueryWindow, self).build_groups()
        return select_sql.replace('GROUP BY', 'PARTITION BY', 1)
