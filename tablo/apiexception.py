# coding=utf-8
"""
our custom exception

"""


class APIError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args)
        self.code = kwargs.get('code')
