# coding=utf-8
"""
Airing class
"""
from pprint import pformat
from tablo import compat
from tablo.api import Api
from tablo.watch import Watch
from tablo.util import processDate
from tablo.util import logger
from .show import Show
from .channel import Channel


class Airing(object):
    def __init__(self, data, type=None):
        super(Airing, self).__init__()
        self.data = data

        self.object_id = data.get('id')
        self.path = data.get('path')
        self.scheduleData = data.get('schedule')
        self.qualifiers = data.get('qualifiers')

        self._show = None
        self._background = None
        self._thumb = None
        self._channel = None
        self._datetime = False
        self._datetimeEnd = None
        self._gridAiring = None
        self.deleted = False
        self.setType(type)

    def dump_info(self):
        # output = f'SHOW PATH: {self.showPath}\n'
        output = ''
        for k, v in self.data.items():
            output += f'{k}: ' + pformat(v) + "\n"
        logger.debug(output)

    def setType(self, type_=None):
        if type_:
            self.type = type_
        elif 'series' in self.path:
            self.type = 'episode'
        elif 'movies' in self.path:
            self.type = 'movie'
        elif 'sports' in self.path:
            self.type = 'event'
        elif 'programs' in self.path:
            self.type = 'program'

    @property
    def showPath(self):
        if self.type == 'episode':
            return self.data['series_path']
        elif self.type == 'movie':
            return self.data['movie_path']
        elif self.type == 'event':
            return self.data['sport_path']
        elif self.type == 'program':
            return self.data['program_path']

    def show(self):
        if not self._show:
            info = Api(self.showPath).get()
            self._show = Show.newFromData(info)
        return self._show

    def __getattr__(self, name):
        try:
            logger.debug(f"getattr name = {name}")
            return self.data[self.type].get(name)
        except KeyError:
            return None

    def watch(self):
        if 'recording' in self.path:
            return Watch(self.Api, self.path)
        else:
            return Watch(self.Api, self.data['airing_details']['channel_path'])

    @property
    def background(self):
        if not self._background:
            image = self.background_image and \
                Api.images(self.background_image['image_id'])
            self._background = image or ''
        return self._background

    @property
    def thumb(self):
        if not self._thumb:
            image = self.thumbnail_image and \
                Api.images(self.thumbnail_image['image_id'])
            self._thumb = image or ''
        return self._thumb

    @property
    def snapshot(self):
        if not self.data.get('snapshot_image'):
            return ''

        return self.Api.images(self.data['snapshot_image']['image_id'])

    @property
    def duration(self):
        return self.data['airing_details']['duration']

    @property
    def channel(self):
        channelPath = self.data['airing_details']['channel_path']
        if not self._channel:
            self._channel = Channel(Api(channelPath).getCached())
        return self._channel

    @property
    def scheduled(self):
        return self.scheduleData['state'] == 'scheduled'

    @property
    def conflicted(self):
        return self.scheduleData['state'] == 'conflict'

    def schedule(self, on=True):
        airing = self.Api(self.path).patch(scheduled=on)
        self.scheduleData = airing.get('schedule')
        return self.scheduleData

    @property
    def datetime(self):
        if self._datetime is False:
            self._datetime = processDate(
                self.data['airing_details'].get('datetime')
            )

        return self._datetime

    @property
    def datetimeEnd(self):
        if self._datetimeEnd is None:
            if self.datetime:
                self._datetimeEnd = self.datetime + \
                    compat.datetime.timedelta(seconds=self.duration)
            else:
                self._datetimeEnd = 0

        return self._datetimeEnd

    def displayTimeStart(self):
        if not self.datetime:
            return ''

        return self.datetime.strftime('%I:%M %p').lstrip('0')

    def displayTimeEnd(self):
        if not self.datetime:
            return ''

        return self.datetimeEnd.strftime('%I:%M %p').lstrip('0')

    def displayDay(self):
        if not self.datetime:
            return ''

        return self.datetime.strftime('%A, %B {0}').format(self.datetime.day)

    def displayChannel(self):
        channel = self.channel
        return '{0}-{1}'.format(
            channel.data['channel']['major'],
            channel.data['channel']['minor']
        )

    def secondsToEnd(self, start=None):
        start = start or now()
        return compat.timedelta_total_seconds(self.datetimeEnd - start)

    def secondsToStart(self):
        return compat.timedelta_total_seconds(self.datetime - now())

    def secondsSinceEnd(self):
        return compat.timedelta_total_seconds(now() - self.datetimeEnd)

    def airingNow(self, ref=None):
        ref = ref or now()
        return self.datetime <= ref < self.datetimeEnd

    def ended(self):
        return self.datetimeEnd < now()

    @property
    def network(self):
        return self.channel.data['channel'].get('network') or ''

    # For recordings
    def delete(self):
        self.deleted = True
        return Api(self.path).delete()

    def recording(self):
        return self.data['video_details']['state'] == 'recording'

    @property
    def watched(self):
        return bool(self.data['user_info'].get('watched'))

    def markWatched(self, watched=True):
        recording = self.Api(self.path).patch(watched=watched)
        self.data['user_info'] = recording.get('user_info')
        return self.data['user_info']

    @property
    def protected(self):
        return bool(self.data['user_info'].get('protected'))

    def markProtected(self, protected=True):
        recording = self.Api(self.path).patch(protected=protected)
        self.data['user_info'] = recording.get('user_info')
        return self.data['user_info']

    @property
    def position(self):
        return self.data['user_info'].get('position')

    def setPosition(self, position=0):
        recording = self.Api(self.path).patch(position=int(position))
        self.data['user_info'] = recording.get('user_info')
        self.data['video_details'] = recording.get('video_details')
        return self.data['user_info']


class GridAiring(Airing):
    def setType(self, type_):
        if 'series' in self.data:
            self.type = 'series'
        elif 'movie' in self.data:
            self.type = 'movie'
        elif 'sport' in self.data:
            self.type = 'sport'
        elif 'program' in self.data:
            self.type = 'program'

    @property
    def gridAiring(self):
        if not self._gridAiring:
            data = Api(self.path).get()
            if 'episode' in data:
                self._gridAiring = Airing(data, 'episode')
            elif 'movie_airing' in data:
                self._gridAiring = Airing(data, 'movie')
            elif 'event' in data:
                self._gridAiring = Airing(data, 'event')
            elif 'program' in data:
                self._gridAiring = Airing(data, 'program')

        return self._gridAiring

    def schedule(self, on=True):
        self.scheduleData = self.gridAiring.schedule(on)
        return self.scheduleData
