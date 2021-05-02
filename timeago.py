from datetime import datetime, timedelta
# from timeago.locales import timeago_template
# from timeago.excepts import ParameterUnvalid
# from timeago import parser
# from timeago.setting import DEFAULT_LOCALE

# https://github.com/hustcc/timeago/blob/master/src/timeago/__init__.py

def total_seconds(dt):
    return dt.total_seconds()

# second, minute, hour, day, week, month, year(365 days)
SEC_ARRAY = [60.0, 60.0, 24.0, 7.0, 365.0 / 7.0 / 12.0, 12.0]
SEC_ARRAY_LEN = 6

class ParameterUnvalid(Exception):
    pass

LOCALE = [
    ["just now", "a while"],
    ["%s seconds ago", "in %s seconds"],
    ["1 minute ago", "in 1 minute"],
    ["%s minutes ago", "in %s minutes"],
    ["1 hour ago", "in 1 hour"],
    ["%s hours ago", "in %s hours"],
    ["1 day ago", "in 1 day"],
    ["%s days ago", "in %s days"],
    ["1 week ago", "in 1 week"],
    ["%s weeks ago", "in %s weeks"],
    ["1 month ago", "in 1 month"],
    ["%s months ago", "in %s months"],
    ["1 year ago", "in 1 year"],
    ["%s years ago", "in %s years"],
]


def timeago_template(index, ago_in):
    return LOCALE[index][ago_in]

def relative_format(date, now=None):
    if not isinstance(date, timedelta):
        if now is None:
            now = datetime.now()

        assert isinstance(date, datetime)
        assert isinstance(now, datetime)

        if date is None:
            raise ParameterUnvalid('the parameter `date` should be datetime '
                                   '/ timedelta, or datetime formatted string.')
        if now is None:
            raise ParameterUnvalid('the parameter `now` should be datetime, '
                                   'or datetime formatted string.')
        date = now - date
    # the gap sec
    diff_seconds = int(total_seconds(date))

    # is ago or in
    ago_in = 0
    if diff_seconds < 0:
        ago_in = 1  # date is later then now, is the time in future
        diff_seconds *= -1  # change to positive

    tmp = 0
    i = 0
    while i < SEC_ARRAY_LEN:
        tmp = SEC_ARRAY[i]
        # if diff_seconds >= tmp:
        if diff_seconds >= tmp * 2:
            i += 1
            diff_seconds /= tmp
        else:
            break
    diff_seconds = int(diff_seconds)
    i *= 2

    if diff_seconds > (i == 0 and 9 or 1):
        i += 1


    tmp = timeago_template(i, ago_in)

    if hasattr(tmp, '__call__'):
        tmp = tmp(diff_seconds)
    return '%s' in tmp and tmp % diff_seconds or tmp
