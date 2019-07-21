# coding=utf-8
"""
Show -> Sport class
"""
from .show import Show
from tablo.util import logger
from tablo.api import Api
from tablo.apiexception import APIError


class Sport(Show):
    type = 'SPORT'
    airingType = 'event'

    def processData(self, data):
        self.data = data['sport']

    def events(self):
        try:
            return Api(self.path).events.get()
        except APIError as e:
            logger.error(f'Sport.events() failed: {format(e.message)}')
            return []

    def _airings(self):
        return self.events()
