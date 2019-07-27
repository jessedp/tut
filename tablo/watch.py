from urllib.parse import urlparse
import pickle
import ffmpeg
import m3u8
import requests

from .apiexception import APIError
from .api import Api
from .util import logger

WATCH_ERROR_MESSAGES = {
    'disk_unavailable': 'No Hard Drive Connected',
    'no_video': 'Video Cannot be Found',
    'no_tuner_available': 'No Tuner Available',
    'no_signal_lock': 'Weak Signal',
    None: 'A Playback Error Occurred'
}


class Watch(object):
    """
    This is not easily usable, but the code can stay for now
    """

    def __init__(self, api, path=None):
        self.error = None
        self.data = []
        if path is None:
            self.error = "No path"
        else:
            try:
                self.data = Api(path).watch.post()
                self.error = None
                self.errorDisplay = ''
            except APIError as e:
                self.error = e.message.get('details', 'Unknown')
                self.errorDisplay = WATCH_ERROR_MESSAGES.get(
                    self.error,
                    WATCH_ERROR_MESSAGES.get(None)
                )

        self.base = ''
        self.url = ''
        self.width = 0
        self.height = 0

        if self.error:
            return
        self.m3u8 = None
        self.originalPlaylistUrl = None
        self.bifSD = self.data.get('bif_url_sd')
        self.bifHD = self.data.get('bif_url_hd')
        self.playlist_url = self.data.get('playlist_url')
        self.expires = self.data.get('exires')
        self.token = self.data.get('token')
        if 'video_details' in self.data:
            self.width = self.data['video_details']['width']
            self.height = self.data['video_details']['height']

        self.getPlaylistURL(self.data.get('playlist_url'))

        self._playlist = None

    def dump_info(self):
        print("Watch [DATA]")
        print('\n\t'.
                     join("%s: %s" % item for item in self.data.items()))
        print('Watch [M3U8]')
        print(self.m3u8.dumps())

    def dl_video(self):
        (
            ffmpeg
            # .input(self.getSegmentedPlaylist().dumps())
            .input(self.data['playlist_url'])
            # .output('/tmp/test.mp4', absf='aac_adtstoasc', codec='copy')
            .output('/tmp/test.mp4', codec='copy')
            .run()
        )

    def getPlaylistURL(self, url):
        self.originalPlaylistUrl = url
        p = urlparse(url)

        self.base = '{0}://{1}{2}'.format(
            p.scheme,
            p.netloc,
            p.path.rsplit('/', 1)[0]
        )
        text = requests.get(url).text
        self.m3u8 = m3u8.loads(text)
        logger.debug(pickle.dumps(self.m3u8.playlists))
        self.url = '{0}://{1}{2}'.format(
            p.scheme,
            p.netloc,
            self.m3u8.playlists[0].uri
        )

    def getSegmentedPlaylist(self):
        if not self._playlist:
            self._playlist = requests.get(self.url).text

        m = m3u8.loads(self._playlist)
        m.base_path = self.base
        return m

    def makeSeekPlaylist(self, position):
        m = self.getSegmentedPlaylist()
        duration = m.segments[0].duration
        while duration < position:
            del m.segments[0]
            if not m.segments:
                break
            duration += m.segments[0].duration

        return m.dumps()
