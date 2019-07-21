# import json

import pytz
import requests
import traceback
import logging

from . import discovery

from tablo.endpoint import Endpoint
from tablo.apiexception import APIError
from . import compat
# from .entities.airing import Airing
# from .watch import Watch

logger = logging.getLogger(__name__)

DISCOVERY_URL = 'https://api.tablotv.com/assocserver/getipinfo/'

ConnectionError = requests.exceptions.ConnectionError


class TabloAPI(Endpoint):
    def __init__(self, *args, **kwargs):
        super(TabloAPI, self).__init__(*args, **kwargs)
        self.device = None
        self.devices = None
        self.subscription = None
        self._hasUpdateStatus = False
        self._wasUpdating = False
        self.timezone = pytz.UTC
        self.serverInfo = {}

        # self.airing = Airing(self)
        # self.watch = Watch(self)

    def discover(self):
        self.devices = discovery.Devices()
        if not self.foundTablos():
            raise Exception("No Tablo devices found.")

    def add_device(self, device):
        if not self.devices:
            self.devices = discovery.Devices(False)
        if device not in self.devices:
            self.devices.tablos.append(device)

    def getServerInfo(self):
        if not self.deviceSelected():
            raise Exception('No device selected.')
        try:
            info = self.server.info.get()
        except ConnectionError:
            # logger.error('TabloApi.getServerInfo(): Failed to connect')
            return False
        except Exception:
            traceback.print_exc()
            return False

        self.serverInfo = info
        timezone = info.get('timezone')

        if timezone:
            self.timezone = pytz.timezone(timezone)

        return True

    def _getSubscription(self):
        try:
            self.subscription = self.server.subscription.get()
        except ConnectionError as e:
            logger.error(e)
            # would MUCH rather raise the exception here. Not just to make
            # fewer code changes
            return False
        except Exception:
            traceback.print_exc()

    def hasSubscription(self):
        return self.subscription and self.subscription.get('state') != "none"

    def getTablos(self):
        if not self.foundTablos():
            self.discover()
        return self.devices.tablos

    def foundTablos(self):
        return bool(self.devices and self.devices.tablos)

    def selectDevice(self, selection=None):
        self._hasUpdateStatus = False
        self._wasUpdating = False
        if isinstance(selection, int):
            self.device = self.devices.tablos[selection]
        elif not selection and len(self.devices.tablos):
            self.device = self.devices.tablos[0]
        elif not isinstance(selection, str):
            raise Exception('"selection" must be a string or integer')
        else:
            for d in self.devices.tablos:
                logger.debug(f"sel={selection} | devId={d.ID}")
                if selection == d.ID:
                    self.device = d
                    break
            else:
                devices_found = len(self.getTablos())
                msg = "Devices found, but requested Tablo ID doesn't exist."
                logger.exception(f"{devices_found} {msg}")

        self._getSubscription()

        return self.getServerInfo()

    def deviceSelected(self):
        return bool(self.device)

    def images(self, ID):
        return 'http://{0}/images/{1}'.format(self.device.address(), ID)

    def getUpdateDownloadProgress(self):
        try:
            prog = self.server.update.progress.get()
            return prog.get('download_progress')
        except Exception:
            traceback.print_exc()

        return None

    def getUpdateStatus(self):
        try:
            status = self.server.update.info.get()
            self._hasUpdateStatus = True
            state = status.get('state')
            if state in ('downloading', 'installing', 'rebooting', 'error'):
                self._wasUpdating = True
                if state == 'downloading':
                    return (state, self.getUpdateDownloadProgress())
                else:
                    return (state, None)
            return None
        except APIError as e:
            if self._hasUpdateStatus:
                traceback.print_exc()
                return ('error', None)

            if e.code == 404:
                try:
                    self.server.tuners.get()
                except APIError:
                    if e.code == 503:
                        self._wasUpdating = True
                        return ('updating', None)
                except ConnectionError:
                    if self._wasUpdating:
                        return ('rebooting', None)
                except Exception:
                    traceback.print_exc()
        except ConnectionError:
            if self._wasUpdating:
                return ('rebooting', None)

        return None

    #originally from tablo.utils
    def now():
        return compat.datetime.datetime.now(self.timezone)


# This is kind of gross. Doing this so 1 init'd object is used everywhere
# to be clear: it needs to be init'd so one can hold the devices...
Api = TabloAPI()
