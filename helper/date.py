import datetime
from .timeago import relative_format


def now_tz():
    current_tzinfo = datetime.datetime.now().astimezone().tzinfo
    return datetime.datetime.now(tz=current_tzinfo)

def now_no_tz():
    return datetime.datetime.now()

def now_tz_str():
    return now_tz().isoformat()

def now_no_tz_str():
    return now_no_tz().isoformat()

# def now_epoch_seconds():
#     return round(datetime.datetime.now().timestamp())

def unique_file_name():
    s = hex(int(datetime.datetime.now().timestamp() * 10000)).replace('0x', '0')
    return s[:4] + '-' + s[4:8] + '-' + s[8:]


def parse_iso(s: str):
    try:
        # Might not work with seconds that has decimal places
        return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        return datetime.datetime.strptime(s, '%Y-%m-%dT%H:%M:%S%z')


def parse_rfc(s):
    from email.utils import parsedate

    # [parsing - How to parse a RFC 2822 date/time into a Python datetime? - Stack Overflow](https://stackoverflow.com/questions/885015)
    t = parsedate(s)
    return datetime.datetime(*t[:6])


##########


def format_time(d: datetime):
    return str(d).replace('2021-', '') + '  ' + relative_format(d)

def format_seconds(s: float | int):
    s = int(s)
    return f'({s // 3600}.{s % 3600 // 60}.{s % 60 // 1}) {s}s'



############

