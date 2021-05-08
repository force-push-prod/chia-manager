from .date import *
from json import JSONEncoder
import subprocess

from dataclasses import dataclass

NL = '\n'
TAB = '\t'
SP = ' '
SPACER = '    '
ERROR_DIVIDER = '*' * 80

def shorten_plot_id(s):
    assert len(s) == 64
    return s[:6]

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

def run_shell_get_stdout(s):
    return subprocess.run(s, shell=True, stdout=subprocess.PIPE, universal_newlines=True).stdout


@dataclass(init=True, repr=True, frozen=True)
class StageUpdateSignal():
    before: int = 0
    after: int = 0
