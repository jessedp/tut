# TODO: This is should be wholly necessary
import time
import datetime

try:
    datetime.datetime.strptime('0', '%H')
except TypeError:
    # Fix for datetime issues with XBMC/Kodi
    class new_datetime(datetime.datetime):
        @classmethod
        def strptime(cls, dstring, dformat):
            return datetime.datetime(*(time.strptime(dstring, dformat)[0:6]))

    datetime.datetime = new_datetime


# This is weird, probably should be done/described better if it
# touches code that currently matters.
def timedelta_total_seconds(td):
    try:
        return td.total_seconds()
    except Exception:
        HOUR = 24
        SEC_IN_HOUR = 3600
        # For converting milliseconds back to seconds. sigh.
        ONE_MILLION = 10 ** 6
        return (
            (float(td.seconds) + float(td.days) * HOUR * SEC_IN_HOUR)
            * ONE_MILLION) / ONE_MILLION
