# coding=utf-8
"""
Show -> Series class
"""
from .show import Show
from tablo.util import logger
from tablo.api import Api
from tablo.apiexception import APIError


class Series(Show):
    type = 'SERIES'
    airingType = 'episode'

    def processData(self, data):
        self.data = data['series']

    def episodes(self):
        return Api(self.path).episodes.get()

    def seasons(self):
        try:
            return Api(self.path).seasons.get()
        except APIError as e:
            logger.error(f'Series.seasons() failed: {format(e.message)}')
            return []

    def _airings(self):
        return self.episodes()
