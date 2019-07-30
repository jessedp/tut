import os
import datetime
from dateutil.parser import parse
from pytz import timezone

from config import config


def chunks(l, n):
    """Yield successive n-sized chunks from l"""
    for i in range(0, len(l), n):
        yield l[i:i + n]

# I feel like there are exceptions to be handled here


def convert_datestr(str, fmt='%m/%d/%Y %H:%M'):
    x = parse(str)
    tz = config.get('General', 'Timezone')
    out = x.astimezone(timezone(tz)).strftime(fmt)
    return out


def file_time_str(path):
    t = os.path.getmtime(path)
    disp = datetime.datetime.fromtimestamp(t).strftime('%c')
    return disp


def datetime_comp(val, op, test_val):
    if op not in ['<', '>', '=']:
        raise Exception(f"Invalid datetime_comp operator {op}")

    if not val or not test_val:
        return True

    val = parse(val)
    v = val.astimezone(timezone('UTC'))

    if type(test_val) == 'str':
        test_val = parse(test_val)

    tz = config.get('General', 'Timezone')
    t = test_val.astimezone(timezone(tz))

    if op == ">":
        return v > t
    else:
        return v < t
