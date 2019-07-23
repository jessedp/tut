import sys
import os
from glob import glob
import pickle
import configparser
import logging
import logging.config
from tzlocal import get_localzone
from pytz import timezone
from pytz.exceptions import UnknownTimeZoneError

from util import print_dict
from tablo.api import Api

logger = logging.getLogger(__name__)
# For batch Api call
MAX_BATCH = 50

config = configparser.ConfigParser()
# TODO: see about using this for cleaner variable interpolation
# config = configparser.ConfigParser(
#           interpolation=configparser.ExtendedInterpolation
#           )
# prevent lowercasing options
config.optionxform = lambda option: option
orig_config = configparser.ConfigParser()

# built in shared options that we aren't allowing to be user-configurable
built_ins = {}


def view():
    print(f"Settings from: {built_ins['config_file']}")
    print("-" * 50)

    # for display purposes...
    orig_config['DEFAULT']['base_path'] = built_ins['base_path']

    for sect in config.sections():
        print(f'[{sect}]')
        for item, val in config.items(sect):
            ipol_disp = None
            if item == 'base_path':
                continue
            else:
                try:
                    test = orig_config.get(sect, item)
                except configparser.NoOptionError:
                    test = None

                def_val = f'{val} (default)'

                if not test and not val:
                    val_disp = def_val
                elif test and not val:
                    val_disp = f'{test} (default)  '
                elif val == test:
                    # The cheeky way I'm setting defaults means this can show
                    # up when it should just be "(default)"
                    val = config.get(sect, item)
                    raw_val = config.get(sect, item, raw=True)
                    if raw_val != val:
                        val_disp = f'{val} (set to default)  '
                        ipol_disp = raw_val
                    else:
                        val_disp = f'{val} (set to default)  '

                else:
                    # print(f'{item} = {val}')
                    val_disp = val
                    pass

                print('{:10}'.format(item) + " = " + val_disp)
                if ipol_disp:
                    print('{:>10}'.format('real') + " = " + ipol_disp)

        print()

    print()
    print("Built-in settings")
    print("-" * 50)
    print_dict(built_ins, '')
    print()
    print("Cached Devices")
    print("-" * 50)

    for name in glob(built_ins['db']['path']+"device_*"):
        with open(name, 'rb') as file:
            device = pickle.load(file)
            device.dump_info()
    print()
    print("Devices pre-loaded in Api")
    print("-" * 50)
    for device in Api.getTablos():
        print(f"{device.ID} - {device.IP} - {device.modified}")
        if Api.selectDevice(device.ID):
            print("\tSuccessfully connected to Tablo!")
        else:
            print("\tUnable to connect to Tablo!")
    print()


def discover(display=True):
    Api.discover()
    devices = Api.getTablos()
    if not devices:
        if display:
            print("Unable to locate any Tablo devices!")
    else:
        for device in devices:
            device.dump_info()
            Api.selectDevice(device.ID)
            if display:
                print(f'timezone: {Api.timezone}')
                print('srvInfo: ')
                print_dict(Api.serverInfo)
                print('subscription:')
                print_dict(Api.subscription)

            # cache the devices for later
            # TODO: maybe save serverinfo and subscription if find a need
            name = "device_" + device.ID
            with open(built_ins['db']['path'] + name, 'wb') as file:
                pickle.dump(device, file)


def setup():
    # create/find what should our config file
    if sys.platform == 'win32':  # pragma: no cover
        path = os.path.expanduser(r'~\Tablo')
    else:
        path = os.path.expanduser('~/Tablo')

    built_ins['base_path'] = path

    built_ins['config_file'] = built_ins['base_path'] + "/tablo.ini"
    # this is here primarily for display order... :/
    built_ins['dry_run'] = False

    db_path = built_ins['base_path'] + "/db/"
    built_ins['db'] = {
        'path': db_path,
        'guide': db_path + "guide.json",
        'recordings': db_path + "recordings.json",
        'recording_shows': db_path + "recording_shows.json"
    }

    os.makedirs(db_path, exist_ok=True)

    if os.path.exists(built_ins['config_file']):
        config.read(built_ins['config_file'])
    else:
        # write out a default config file
        config.read_string(DEFAULT_CONFIG_FILE)

        with open(built_ins['config_file'], 'w') as configfile:
            configfile.write(DEFAULT_CONFIG_FILE)

    orig_config.read_string(DEFAULT_CONFIG_FILE)
    # Setup config defaults we're not configuring yet, but need
    config['DEFAULT']['base_path'] = built_ins['base_path']
    # config['DEFAULT']['Timezone'] = 'America/New_York'

    tz = ''
    try:
        tz = config.get('General', 'Timezone')
    except configparser.NoSectionError:
        config['General'] = {}

    try:
        timezone(tz)
    except UnknownTimeZoneError:
        if tz:
            print("INVALID Timezone: '"+tz+"' - using defaults")

        tz = get_localzone()
        if tz:
            config.set('General', 'Timezone', str(tz))
            orig_config.set('General', 'Timezone', str(tz))
        else:
            config.set('General', 'Timezone', 'UTC')
            orig_config.set('General', 'Timezone', 'UTC')

    # Load cached devices so we don't *have* to discover
    for name in glob(built_ins['db']['path'] + "device_*"):
        with open(name, 'rb') as file:
            device = pickle.load(file)
            Api.add_device(device)
    # if we cn, go ahead and select a default device
    # TODO: try to use the config ip/id here too
    if Api.devices and len(Api.devices.tablos) == 1:
        Api.device = Api.devices.tablos[0]


def setup_logger(level=logging.CRITICAL):
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format':
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': level,
                'formatter': 'default',
                'stream': 'ext://sys.stdout'
            },

        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['console']
        },
        'loggers': {
            'default': {
                'level': 'DEBUG',
                'handlers': ['console']
            }
        },

    })
    """
    'file': {
        'level': 'DEBUG',
        'class': 'logging.handlers.RotatingFileHandler',
        'formatter': 'default',
        'filename': log_path,
        'maxBytes': 1024,
        'backupCount': 3
    }
    """


DEFAULT_CONFIG_FILE = \
"""[General]
Timezone =
# Timezone: defaults to your system, then UTC


[Tablo]
# Define settings for the Tablo device you want to use. Usually only one Tablo
# exists and will be found/used by default, so there's usually no need to set
# these.
#
# The values can be found by running './tablo.py config --discover'
#
# IMPORTANT: If these are set and wrong, you'll need to remove or manually
# change them before things work.

ID =
# ID: the device ID (see above) selects a specific Tablo regardless of IP
# (great for non-reserved DHCP addresses)

IP =
# IP: the device IP address.


[Output Locations]
# The locations/paths recordings will be output to
# These will default to HOME_DIR-Tablo
TV = %(base_path)s/TV
Movies = %(base_path)s/Movies

"""
