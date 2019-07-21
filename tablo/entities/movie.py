# coding=utf-8
"""
Show -> Movie class
"""
from .show import Show


class Movie(Show):
    type = 'MOVIE'
    airingType = 'schedule'

    def processData(self, data):
        self.data = data['movie']
