# coding=utf-8
"""
something about how Endpoint makes connections happen
"""
import json
import requests
from .apiexception import APIError
from .util import logger

# TODO - not this ua!!
USER_AGENT = 'Tablo-Kodi/0.1'


def request_handler(f):
    def wrapper(*args, **kwargs):
        r = f(*args, **kwargs)
        if not r.ok:
            e = APIError('{0}: {1}'.format(
                r.status_code, '/' +
                r.url.split('://', 1)[-1].split('/', 1)[-1]),
                code=r.status_code
            )
            try:
                edata = r.json()
                if isinstance(edata, dict):
                    e.message = edata.get('error', edata)
                else:
                    e.message = edata
            except Exception:
                pass
            raise e

        try:
            return r.json()
        except (ValueError, TypeError):
            return r.text

    return wrapper


class Endpoint(object):
    cache = {}

    def __init__(self, segments=None):
        self.device = None
        self.segments = segments or []

    def __getattr__(self, name):
        e = Endpoint(self.segments + [name.strip('_')])
        e.device = self.device
        return e

    def __call__(self, method=None):
        """ method is NOT the http method """
        logger.debug(f'Endpoint "Method": {method}')
        return self.__getattr__(str(method).lstrip('/'))

    def __get_uri(self):
        if self.device is None:
            msg = "No device selected."
            logger.error(msg)
            raise APIError(msg)

        uri = 'http://{0}/{1}'.format(
            self.device.address(), '/'.join(self.segments)
        )
        logger.debug(f'URI: {uri}')
        return uri

    def dump_info(self):
        attrs = vars(self)
        print(f'ENDPOINT INFO for {self.device}')
        print(', '.join("%s: %s" % item for item in attrs.items()))

    @request_handler
    def get(self, **kwargs):
        return requests.get(
            self.__get_uri(),
            headers={'User-Agent': USER_AGENT},
            params=kwargs
        )

    @request_handler
    def getCached(self, **kwargs):
        path = '/'.join(self.segments)

        if path not in self.cache.keys():
            self.cache[path] = requests.get(
                'http://{0}/{1}'.format(self.device.address(), path),
                headers={'User-Agent': USER_AGENT},
                params=kwargs
            )

        return self.cache[path]

    @request_handler
    def post(self, *args, **kwargs):
        return requests.post(
            self.__get_uri(),
            headers={'User-Agent': USER_AGENT},
            data=json.dumps(args and args[0] or kwargs)
        )

    @request_handler
    def patch(self, **kwargs):
        return requests.patch(
            'http://{0}/{1}'.format(
                self.device.address(), '/'.join(self.segments)
            ),
            headers={'User-Agent': USER_AGENT},
            data=json.dumps(kwargs)
        )

    @request_handler
    def delete(self, **kwargs):
        return requests.delete(
            'http://{0}/{1}'.format(
                self.device.address(), '/'.join(self.segments)
            ),
            headers={'User-Agent': USER_AGENT}
        )
