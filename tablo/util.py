import logging
import pytz
import traceback

from tablo import compat
# from tablo.api import Api

# TODO: remove this completely!
LOG_LEVEL = logging.DEBUG
logger = logging.getLogger(__name__)




def UTCNow():
    return compat.datetime.datetime.now(pytz.timezone('UTC'))


# TODO: move processDate elsewher (tablo.api?)
def processDate(date, format_='%Y-%m-%dT%H:%M'):
    if not date:
        return None

    try:
        from tablo.api import Api
        return Api.timezone.fromutc(
            compat.datetime.datetime.strptime(date.rsplit('Z', 1)[0], format_)
        )
    except Exception:
        traceback.print_exc()

    return None


def debug_log(msg):
    import inspect
    from os import path

    func = inspect.currentframe().f_back.f_code
    filename = path.basename(func.co_filename)
    message = f'{filename}:{func.co_name}:{func.co_firstlineno}\n{msg}'
    # Dump the message + the name of this function to the log.
    logger.debug(message)


def dump_info(obj):
    attrs = vars(obj)
    logger.info(f'OBJECT str: {obj}')
    logger.info(', '.join("%s: %s" % item for item in attrs.items()))


def print_dict(dictionary, prefix='\t', braces=1):
    """ Recursively prints nested dictionaries."""

    for key, value in dictionary.items():
        if isinstance(value, dict):
            print('%s%s%s%s' % (prefix, braces * '[', key, braces * ']'))
            print_dict(value, prefix + '  ', braces + 1)
        else:
            print(prefix + '%s = %s' % (key, value))
