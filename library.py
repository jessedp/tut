import os
import pprint
import re

from config import built_ins, MAX_BATCH
from tinydb import TinyDB, Query

from tablo.api import Api
from tablo.entities.show import Show
from tablo.entities.airing import Airing
from util import chunks
import logging

logger = logging.getLogger(__name__)


def view(full=False):
    path = built_ins['db']['recordings']
    rec_db = TinyDB(path)

    for item in rec_db.all():
        if full:
            pprint.pprint(item)
        else:
            data = item['data']
            # TODO: convert datetime (we already have pytz & other funcs)
            # TODO: put this *somewhere* so it's not duplciated
            if data['video_details']['error']:
                error = data['video_details']['error']
            print(
                data['airing_details']['datetime'] + " - " +
                data['airing_details']['show_title'] + "\n" +
                "Desc: " + data['episode']['description'] + "\n" +
                "Status: " + data['video_details']['state'] +
                "  Error: " + error + "\n"
            )


def search(term, full=False):
    """
    TODO: massage "term" - extra white space in between terms ... more?
    TODO: allow more granular/specifc field searching that almost
          nobody would use?
    TODO: maybe a search_advanced() method to just let folk play with the db
    """

    path = built_ins['db']['recordings']
    rec_db = TinyDB(path)
    my_show = Query()

    results = rec_db.search(
        my_show.data.airing_details.show_title.matches(
            f'.*{term}.*', flags=re.IGNORECASE
        )
    )
    if not results:
        print(f'No records found matching "{term}"')
    else:
        for item in results:
            if full:
                pprint.pprint(item)
            else:
                data = item['data']
                error = 'none'
                if data['video_details']['error']:
                    error = data['video_details']['error']
                print(
                    data['airing_details']['datetime'] + " - " +
                    data['airing_details']['show_title'] + "\n" +
                    "Desc: " + data['episode']['description']+"\n" +
                    "Status: " + data['video_details']['state'] +
                    "  Error: " + error + "\n"
                )


def build():
    logger.debug(f"building library!")

    Api.discover()
    connected = Api.selectDevice()
    if not connected:
        logger.exception("NOT CONNECTED")

    # don't think we'll need this
    # _build_guide()
    _build_recordings()


def _build_guide():
    guide_path = built_ins['db']['guide']
    if not built_ins['dry_run']:
        try:
            os.unlink(guide_path)
        except Exception:
            pass

    guide_db = {}
    if not built_ins['dry_run']:
        guide_db = TinyDB(guide_path)

    # Load all the shows
    logger.info('Loading All Guide/Show data')
    sections = Api.views('guide').shows.get()

    total = sum(len(section.get('contents')) for section in sections)
    logger.info(f"Total Shows: {total}")
    for section in sections:
        contents = section.get('contents')
        if not contents:
            logger.info(f"Section {section.get('key').upper()} (0)")
            continue

        logger.info(f"Section {section.get('key').upper()} ({len(contents)})")
        for piece in chunks(contents, MAX_BATCH):
            shows = Api.batch.post(piece)
            for path, data in shows.items():
                show = Show.newFromData(data)
                if not built_ins['dry_run']:
                    guide_db.insert({
                        'id': show.object_id,
                        'path': show.path,
                        'data': show.data
                    })


def _build_recordings():
    recs_path = built_ins['db']['recordings']
    recshow_path = built_ins['db']['recording_shows']
    if not built_ins['dry_run']:
        try:
            os.unlink(recs_path)
        except Exception:
            pass
        try:
            os.unlink(recshow_path)
        except Exception:
            pass

    recs_db = TinyDB(recs_path)

    logger.info('Loading All Recording Data')
    programs = Api.recordings.airings.get()
    show_paths = []
    logger.info(f"Total Recordings: {len(programs)}")
    cnt = 0
    for piece in chunks(programs, MAX_BATCH):
        airings = Api.batch.post(piece)
        cnt += len(airings)
        logger.info(f"\tchunk: {cnt}/{len(programs)}")
        for path, data in airings.items():
            airing = Airing(data)

            if airing.showPath not in show_paths:
                show_paths.append(airing.showPath)

            if not built_ins['dry_run']:
                recs_db.insert({
                    'id': airing.object_id,
                    'path': airing.path,
                    'show_path': airing.showPath,
                    'data': airing.data
                })

    recshow_db = TinyDB(recshow_path)
    logger.info(f"Total Recording Shows: {len(show_paths)}")
    my_show = Query()
    for piece in chunks(show_paths, MAX_BATCH):
        airing_shows = Api.batch.post(piece)
        for path, data in airing_shows.items():
            stuff = recshow_db.search(my_show.show_path == path)
            if not stuff:
                if not built_ins['dry_run']:
                    recshow_db.insert({
                        'id': data['object_id'],
                        'show_path': path,
                        'data': data
                    })
