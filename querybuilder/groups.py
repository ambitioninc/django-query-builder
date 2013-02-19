

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

    def __init__(self, lookup, auto=False, desc=False, include_datetime=False):
        super(AllTime, self).__init__(lookup, auto, desc, include_datetime)
        self.auto = True


class NoneTime(DatePart):
    name = 'none'

    def __init__(self, lookup, auto=False, desc=False, include_datetime=False):
        super(NoneTime, self).__init__(lookup, auto, desc, include_datetime)
        self.auto = True


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


class Epoch(DatePart):
    name = 'epoch'

    def __init__(self, lookup, auto=False, desc=False, include_datetime=False, group_name=None):
        super(Epoch, self).__init__(lookup, auto, desc, include_datetime)

        self.group_name = group_name


    def get_select(self, name=None, lookup=None):
        return super(Epoch, self).get_select(name=name, lookup=lookup)

class GroupEpoch(Epoch):

    def __init__(self, lookup, auto=False, desc=False, include_datetime=False, group_name=None):
        super(GroupEpoch, self).__init__(lookup, auto, desc, include_datetime)
        self.group_name = group_name

    def get_select(self, name=None, lookup=None):
        return 'CAST(extract({0} from date_trunc(\'{1}\', {2})) as INT)'.format(
            name or self.name,
            self.group_name,
            lookup or self.lookup
        )


class AllEpoch(Epoch):

    def get_select(self, name=None, lookup=None):
        return 'CAST(extract({0} from MIN({1})) as INT)'.format(
            name or self.name,
            lookup or self.lookup
        )


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