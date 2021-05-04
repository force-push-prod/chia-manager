from .date import *
from json import JSONEncoder

NL = '\n'
TAB = '\t'
SP = ' '
SPACER = '    '

def shorten_plot_id(s):
    assert len(s) == 64
    return s[:7] + '..' + s[-6:]

def progress_bar(ratio, width=80):
    fill_count = round(width * ratio)
    space_count = width - fill_count
    return f"[{'=' * fill_count}{' ' * space_count}]"

def convert_object_to_str(o):
    class MyEncoder(JSONEncoder):
        def default(self, o):
            if isinstance(o, datetime.datetime):
                return o.isoformat()
            return o.__dict__
    return MyEncoder().encode(o)
