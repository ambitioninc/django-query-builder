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


class DatePart(object):
    name = ''

    def __init__(self, lookup, auto=False, desc=False, include_datetime=False):
        self.lookup = lookup
        self.auto = auto
        self.desc = desc
        self.include_datetime = include_datetime

    def get_select(self, name=None, lookup=None):
        return 'CAST(extract({0} from {1}) as INT)'.format(name or self.name, lookup or self.lookup)


class AllTime(DatePart):
    name = 'all'


class NoneTime(DatePart):
    name = 'none'


class Year(DatePart):
    name = 'year'


class Month(DatePart):
    name = 'month'


class Day(DatePart):
    name = 'day'


class Hour(DatePart):
    name = 'hour'


class Minute(DatePart):
    name = 'minute'


class Second(DatePart):
    name = 'second'


class Week(DatePart):
    name = 'week'
