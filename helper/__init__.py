from .date import *

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
