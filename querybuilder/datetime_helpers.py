"""
Provides helpers for transforming datetime objects.
"""
import datetime

import pytz
from pytz import utc as utc_tz


def utc_now():
    """
    Returns the time in UTC with the UTC timezone attached.
    """
    return utc_tz.localize(datetime.datetime.utcnow())


def est_now():
    """
    Return the current time in EST
    """
    est_tz = pytz.timezone('US/Eastern')

    return est_tz.normalize(utc_now())


def utc_2_est(utc):
    """
    Given a time in UTC, convert it to EST
    """
    return utc_2_tz(utc, 'US/Eastern')


def utc_2_tz(utc, tz):
    """
    Converts a time in UTC to a given timezone.
    """
    if utc.tzinfo is None:
        # Attach the UTC timezone
        utc = utc_tz.localize(utc)

    return pytz.timezone(tz).normalize(utc)


def est_2_utc(est):
    """
    Given a time in EST, convert it to UTC
    """
    if est.tzinfo is None:
        # Attach the EST timezone
        est = pytz.timezone('US/Eastern').localize(est)

    return utc_tz.normalize(est)


def tz_2_utc(time, tz):
    """
    Given a time in the tz timezone, convert it to UTC
    """
    if time.tzinfo is None:
        # Attach the timezone
        time = pytz.timezone(tz).localize(time)

    return utc_tz.normalize(time)


def get_today_time_range_in_utc(timezone_as_str, utc_now=utc_now):
    """
    Given a timezone, return the start of day and end of day times
    in UTC.

    Why do this?  Because if it is now 10:00 pm EST, January 1, 2013,
    it is 3:00 am UTC, January 2, 2013.  In this case, this function
    will return
    (datetime(2013, 1, 1, 0, 0, 0), datetime(2013, 1, 2, 0, 0, 0))
    """
    # Convert to target timezone
    target_tz = pytz.timezone(timezone_as_str)
    target_now = target_tz.normalize(utc_now())

    # Get the start and end times of the day
    day_start = datetime.datetime.combine(
        target_now,
        datetime.time(0))

    day_end = day_start + datetime.timedelta(days=1)

    # Attach some lovely timezones
    day_start = target_tz.localize(day_start)
    day_end = target_tz.localize(day_end)

    # Convert it back to utc
    return (utc_tz.normalize(day_start), utc_tz.normalize(day_end))


def datetime_to_seconds(datetime_string):
    return int(datetime.datetime.strptime(datetime_string, '%Y-%m-%d').strftime('%s'))


def datetime_floor(t, floor):
    """
    Perform a 'floor' on a datetime, where the floor variable can be:
    'year', 'month', 'day', 'hour', 'minute', 'second', or 'week'. This
    function will round the datetime down to the nearest floor.
    """
    if floor == 'year':
        return t.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    elif floor == 'month':
        return t.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    elif floor == 'day':
        return t.replace(hour=0, minute=0, second=0, microsecond=0)
    elif floor == 'hour':
        return t.replace(minute=0, second=0, microsecond=0)
    elif floor == 'minute':
        return t.replace(second=0, microsecond=0)
    elif floor == 'second':
        return t.replace(microsecond=0)
    elif floor == 'week':
        t = t.replace(hour=0, minute=0, second=0, microsecond=0)
        return t - datetime.timedelta(days=t.weekday())
    return t


def unix_time(dt):
    """
    Converts a datetime object to unix timestamp assuming utc
    :param dt: A datetime object
    :type dt: datetime.datetime
    :return: :int: unix timestamp in seconds
    """
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return int(delta.total_seconds())


def unix_time_millis(dt):
    """
    Converts a datetime object to unix timestamp assuming utc
    :param dt: A datetime object
    :type dt: datetime.datetime
    :return: :float: unix timestamp in ms
    """
    return unix_time(dt) * 1000.0
