# coding=utf-8
"""
Channel class
"""


class Channel(object):
    def __init__(self, data):
        self.path = data['path']
        self.object_id = data['object_id']
        self.data = data

    def __getattr__(self, name):
        return self.data['channel'].get(name)
