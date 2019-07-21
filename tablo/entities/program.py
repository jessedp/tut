# coding=utf-8
"""
Show -> Program class
"""
from .show import Show


class Program(Show):
    type = 'PROGRAM'
    airingType = 'airing'

    def processData(self, data):
        self.data = data['program']
