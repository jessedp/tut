# coding=utf-8
"""
Base show class
"""
from tablo.api import Api
from tablo.util import logger

from tablo.apiexception import APIError


class Show(object):

    type = None

    def __init__(self, data):
        self.data = None
        self.object_id = data['object_id']
        self.path = data['path']
        self.show_counts = data['show_counts']

        self._thumb = ''
        self._thumbHasTitle = None
        self._background = ''

        self.scheduleRule = \
            data.get('schedule_rule') != 'none' and \
            data.get('schedule_rule') or None
        self.showCounts = data.get('show_counts')
        # see the "subclasses" for what each does
        self.processData(data)

    def __getattr__(self, name):
        return self.data.get(name)

    def dump_info(self):
        logger.debug('\t'.
                     join("%s: %s\n" % item for item in self.data.items()))

    def update(self):
        self.__init__(Api(self.path).get())

    @classmethod
    def newFromData(self, data):
        """ These imports are a dirty hack that I'm not sure how to do
            better without putting them all (back) in one file
        """
        if 'series' in data:
            from .series import Series
            return Series(data)
        elif 'movie' in data:
            from .movie import Movie
            return Movie(data)
        elif 'sport' in data:
            from .sport import Sport
            return Sport(data)
        elif 'program' in data:
            from .program import Program
            return Program(data)

    def processData(self, data):
        pass

    @property
    def thumb(self):
        if not self._thumb:
            try:
                if self.data.get('thumbnail_image'):
                    self._thumb = \
                        Api.images(self.data['thumbnail_image']['image_id'])
                    self._thumbHasTitle = \
                        self.data['thumbnail_image']['has_title']
            except Exception:
                logger.debug(f"thumb img: {self.data['thumbnail_image']}")
                self._thumbHasTitle = False
        return self._thumb

    @property
    def thumbHasTitle(self):
        if self._thumbHasTitle is None:
            self.thumb

        return self._thumbHasTitle

    @property
    def background(self):
        if not self._background:
            self._background = \
                self.data.get('background_image') and \
                Api.images(self.data['background_image']['image_id']) \
                or ''
        return self._background

    def schedule(self, rule='none'):
        data = Api(self.path).patch(schedule=rule)
        self.scheduleRule = \
            data.get('schedule_rule') != 'none' and \
            data.get('schedule_rule') \
            or None

    def _airings(self):
        return Api(self.path).airings.get()

    def airings(self):
        try:
            return self._airings()
        except APIError as e:
            logger.error('Show.airings() failed: {0}', format(e.message))
            return []

    def deleteAll(self, delete_protected=False):
        if delete_protected:
            return Api(self.path)('delete').post()
        else:
            return Api(self.path)('delete').post(filter='unprotected')
