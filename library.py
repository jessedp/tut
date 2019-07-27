import os
import pprint
import re
import math
import logging

from tinydb import TinyDB, Query
from tqdm import tqdm

from config import built_ins, MAX_BATCH
from util import chunks
from tablo.api import Api
from tablo.entities.show import Show
from recording import Recording

logger = logging.getLogger(__name__)


def view(full=False):
    print()
    path = built_ins['db']['recordings']
    rec_db = TinyDB(path)

    for item in rec_db.all():
        if full:
            pprint.pprint(item)
        else:
            Recording(item['data']).print()


def print_stats():
    path = built_ins['db']['recordings']
    rec_db = TinyDB(path)
    shows = Query()
    shows_qry = shows.data

    field_title = '{:17}'
    print("Overview")
    print("-" * 50)

    cnt = len(rec_db.all())
    print('{:10}'.format("Total Recordings") + ": " + f'{cnt}')
    cnt = rec_db.count(shows_qry.user_info.watched == True)  # noqa: E712
    print('{:10}'.format("Total Watched") + ": " + f'{cnt}')
    print()

    print("By Current Recording State")
    print("-"*50)
    cnt = rec_db.count(shows_qry.video_details.state == 'finished')
    print(field_title.format("Finished") + ": " + f'{cnt}')
    cnt = rec_db.count(shows_qry.video_details.state == 'failed')
    print(field_title.format("Failed") + ": " + f'{cnt}')
    cnt = rec_db.count(shows_qry.video_details.state == 'recording')
    print(field_title.format("Recording") + ": " + f'{cnt}')
    print()

    print("By Recording Type")
    print("-" * 50)
    cnt = rec_db.count(shows.path.matches(f'.*episode.*', flags=re.IGNORECASE))
    print(field_title.format("Episodes/Series") + ": " + f'{cnt}')
    cnt = rec_db.count(shows.path.matches(f'.*movie.*', flags=re.IGNORECASE))
    print(field_title.format("Movies") + ": " + f'{cnt}')
    cnt = rec_db.count(shows.path.matches(f'.*sports.*', flags=re.IGNORECASE))
    print(field_title.format("Sports/Events") + ": " + f'{cnt}')
    cnt = rec_db.count(
        shows.path.matches(f'.*programs.*', flags=re.IGNORECASE)
    )
    print(field_title.format("Programs") + ": " + f'{cnt}')

    print()


def build():
    print("Building library. NO videos are being fetched.")
    print("-"*50)

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
    print('Loading All Guide/Show data')
    sections = Api.views('guide').shows.get()

    total = sum(len(section.get('contents')) for section in sections)
    print(f"Total Shows: {total}")
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

    programs = Api.recordings.airings.get()
    show_paths = []
    print(f"Total Recordings: {len(programs)}")
    # cnt = 0
    with tqdm(total=len(programs)) as pbar:
        for piece in chunks(programs, MAX_BATCH):
            airings = Api.batch.post(piece)
            # cnt += len(airings)
            # print(f"\tchunk: {cnt}/{len(programs)}")
            for path, data in airings.items():
                airing = Recording(data)

                if airing.showPath not in show_paths:
                    show_paths.append(airing.showPath)

                if not built_ins['dry_run']:
                    recs_db.insert({
                        'id': airing.object_id,
                        'path': airing.path,
                        'show_path': airing.showPath,
                        'data': airing.data
                    })
                pbar.update(1)

    recshow_db = TinyDB(recshow_path)
    print(f"Total Recorded Shows: {len(show_paths)}")
    my_show = Query()
    with tqdm(total=len(show_paths)) as pbar:
        # this is silly and just to make the progress bar move :/
        for piece in chunks(show_paths, math.ceil(MAX_BATCH/5)):
            # not caring about progress, we'd use this:
            # for piece in chunks(show_paths, MAX_BATCH):
            airing_shows = Api.batch.post(piece)
            for path, data in airing_shows.items():
                stuff = recshow_db.search(my_show.show_path == path)
                pbar.update(1)
                if not stuff:
                    if not built_ins['dry_run']:
                        recshow_db.insert({
                            'id': data['object_id'],
                            'show_path': path,
                            'data': data
                        })

    print("Done!")
