import binascii
import socket
import traceback
import struct
import time
import datetime
import requests
import logging
from .util import print_dict

logger = logging.getLogger(__name__)

DEVICE_DISCOVERY_PORT = 8881
DEVICE_REPLY_PORT = 8882

ASSOCIATION_SERVER_DISCOVERY_URL = \
    'https://api.tablotv.com/assocserver/getipinfo/'


def truncZero(string):
    return string.decode('ISO-8859-1').split('\0')[0]


class TabloDevice:
    port = 8885

    def __init__(self, data):
        self.ID = data.get('serverid')
        self.name = data.get('name')
        self.IP = data.get('private_ip')
        self.publicIP = data.get('public_ip')
        self.SSL = data.get('ssl')
        self.host = data.get('host')
        self.version = data.get('server_version')
        self.boardType = data.get('board_type')
        self.seen = self.processDate(data.get('last_seen'))
        self.inserted = self.processDate(data.get('inserted'))
        self.modified = self.processDate(data.get('modified'))
        self.modelType = ''
        self.data = data

    def __repr__(self):
        return '<TabloDevice:{0}:{1}>'.format(self.ID, self.IP)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if not isinstance(other, TabloDevice):
            return False
        return self.ID == other.ID or self.IP == other.IP

    def processDate(self, date):
        if not date:
            return None

        try:
            format = '%Y-%m-%d %H:%M:%S.%f'
            return datetime.datetime.strptime(date[:-6], format)
        except Exception:
            traceback.print_exc()
        return None

    def address(self):
        return '{0}:{1}'.format(self.IP, self.port)

    def valid(self):
        return True

    def check(self):
        if not self.name:
            self.updateInfoFromDevice()

    def updateInfoFromDevice(self):
        try:
            url = 'http://{0}/server/info'.format(self.address())
            data = requests.get(url).json()
        except Exception:
            traceback.print_exc()
            return

        self.name = data['name']
        self.version = data['version']
        self.ID = self.ID or data.get('server_id')
        self.modelType = data.get('model.type')

    def dump_info(self):
        attrs = vars(self)
        print(f'DEVICE INFO for {self.ID}')
        print_dict(attrs)

    @property
    def displayName(self):
        return self.name or self.host


class Devices(object):
    MAX_AGE = 3600

    def __init__(self, discover=True):
        if discover:
            self.reDiscover()
        else:
            self._discoveryTimestamp = time.time()
            self.tablos = []

    def __contains__(self, device):
        for d in self.tablos:
            if d == device:
                return True
        return False

    def reDiscover(self):
        self._discoveryTimestamp = time.time()
        self.tablos = []
        self.discover()
        if self.tablos:
            logger.debug('Device(s) found via local discovery')
        else:
            msg = 'No devices found via local discovery ' \
                  '- trying association server'
            logger.debug(msg)
            self.associationServerDiscover()

    def discover(self, device=None):
        from . import netif
        logger.debug("Looking for Networks interfaces")
        ifaces = netif.getInterfaces()
        sockets = []

        logger.debug("Checking interfaces")
        # try to create a bunch of sockets
        for i in ifaces:
            if not i.broadcast:
                logger.debug(f"Unusable, NO BROADCAST - if: {i.name}  "
                             f"ip: {i.ip} mask: {i.mask}  "
                             f"bcast: {i.broadcast}")
                continue
            if i.mask is None:
                logger.debug(f"Unusable, NO MASK - if: {i.name}  ip: {i.ip} "
                             f"mask: {i.mask}  bcast: {i.broadcast}")
                continue
            if i.ip.startswith('127.'):
                logger.debug('Unusable, localhost')
                continue
            logger.debug(f"Usable - if: {i.name}  ip: {i.ip} mask: {i.mask}  bcast: {i.broadcast}")
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(0.01)  # 10ms
            s.bind((i.ip, 0))
            s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sockets.append((s, i))

        packet = struct.pack('>4s', 'BnGr'.encode())

        logger.debug(
            '  o-> Broadcast Packet({0})'.format(binascii.hexlify(packet))
        )
        for attempt in (0, 1):
            for s, i in sockets:
                logger.debug(
                    '  o-> Broadcasting to {0}: {1}'.
                    format(i.name, i.broadcast))
                try:
                    s.sendto(packet, (i.broadcast, DEVICE_DISCOVERY_PORT))
                except Exception:
                    logger.exception("Unable to send packets.")

            end = time.time() + 0.25  # 250ms

            # Create reply socket
            rs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            rs.settimeout(0.01)  # 10ms
            try:
                rs.bind(('', DEVICE_REPLY_PORT))
                rs.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

                while time.time() < end:
                    try:
                        message, address = rs.recvfrom(8096)

                        added = self.add(message, address)

                        if added:
                            logger.debug(
                                '<-o   Response Packet({0})'.
                                format(binascii.hexlify(message))
                            )
                        elif added is False:
                            logger.debug(
                                '<-o   Response Packet(Duplicate)'
                            )
                        elif added is None:
                            logger.debug(
                                '<-o   INVALID RESPONSE({0})'.
                                format(binascii.hexlify(message))
                            )
                    except socket.timeout:
                        pass
                    except Exception:
                        traceback.print_exc()

                for d in self.tablos:
                    d.check()
            except OSError as e:
                logger.error(f"OSError {e}")
                pass

    def createDevice(self, packet, address):
        data = {}

        v = struct.unpack('>4s64s32s20s10s10s', packet)

        # key = v[0]
        data['host'] = truncZero(v[1])
        data['private_ip'] = truncZero(v[2])
        data['serverid'] = truncZero(v[3])
        typ = truncZero(v[4])
        data['board_type'] = truncZero(v[5])

        if not typ == 'tablo':
            return None

        return TabloDevice(data)

    def add(self, packet, address):
        device = self.createDevice(packet, address)

        if not device or not device.valid:
            return None
        elif device in self:
            return False
        self.tablos.append(device)

        return True

    def associationServerDiscover(self):
        r = requests.get(ASSOCIATION_SERVER_DISCOVERY_URL)
        try:
            data = r.json()
            if not data.get('success'):
                return False
            deviceData = data.get('cpes')
        except Exception:
            traceback.print_exc()
            return False

        self.tablos = [TabloDevice(d) for d in deviceData]
