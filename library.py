import os
import re
import math
from datetime import timedelta
import pprint
import logging

from tinydb import TinyDB, Query
from tqdm import tqdm

from config import built_ins, MAX_BATCH
from util import chunks, file_time_str
from tablo.api import Api
from tablo.apiexception import APIError
from tablo.entities.show import Show
from recording import Recording

logger = logging.getLogger(__name__)


def view(args):
    print()
    path = built_ins['db']['recordings']
    rec_db = TinyDB(path)

    id_set = []
    cnt = 0
    for item in rec_db.all():
        cnt += 1
        if args.id_list:
            obj_id = item['data']['object_id']
            if obj_id not in id_set:
                id_set.append(obj_id)

        elif args.full:
            pprint.pprint(item)
        else:
            Recording(item['data']).print()

    if args.id_list:
        print(id_set)
    else:
        print(f'Total recordings found: {cnt}')


def print_stats():
    path = built_ins['db']['recordings']
    rec_db = TinyDB(path)
    shows = Query()
    shows_qry = shows.data

    field_title = '{:17}'
    print("Overview")
    print("-" * 50)
    print(f"Built: {file_time_str(path)}")

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

    print("By Show")
    print("-" * 50)
    shows = {}
    max_width = 0
    for item in rec_db.all():
        title = item['data']['airing_details']['show_title']
        max_width = max(max_width, len(title))
        key = _sortable_title(title)

        if key not in shows.keys():
            shows[key] = {'cnt': 1, 'title': title}
        else:
            shows[key]['cnt'] += 1

    for key in sorted(shows.keys()):
        # print(f"{shows[key]['title']} - {shows[key]['cnt']}")
        print(
            ('{:' + str(max_width) + '}').format(shows[key]['title']) +
            ' -  {:>2}'.format(shows[key]['cnt'])
        )


def _sortable_title(title):
    # toss a/an/the, force non-letters to end
    articles = ['a', 'an', 'the']
    word = title.split(' ', 1)[0].lower()
    sort_title = title
    if word in articles:
        try:
            sort_title = title.split(' ', 1)[1]
        except Exception:
            sort_title = title

    if ord(sort_title[0]) not in range(ord('A'), ord('z') + 1):
        sort_title = "ZZZZ" + sort_title

    return sort_title


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
                        'data': show.data,
                        'version': Api.device.version
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
                        'data': airing.data,
                        'version': Api.device.version
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
                            'data': data,
                            'version': Api.device.version
                        })

    print("Done!")


def print_dupes():
    dupes = _find_dupes()
    for key, data in dupes.items():
        if len(data) > 1:
            print(key + " = " + str(len(data)))
            for item in data:
                rec = Recording(item)
                print("\t" + str(rec.object_id) + " | " +
                      rec.get_description() + " - " + rec.get_dur())


def _find_dupes():
    path = built_ins['db']['recordings']
    rec_db = TinyDB(path)
    dupes = {}
    for item in rec_db.all():
        data = item['data']
        if 'episode' in data.keys():
            tmsid = data['episode']['tms_id']
            if tmsid.startswith('SH'):
                # TODO: this is easy, but wrong. SH* tms_id duplicates for
                #  every episode. Maybe replace with psuedo-title?
                continue
            if tmsid not in dupes:
                dupes[tmsid] = []
                dupes[tmsid].append(data)
            else:
                dupes[tmsid].append(data)
    return dupes


def print_incomplete(args):
    # weird way I made it work...
    percent = args.incomplete
    if percent == -1:
        percent = 100
    else:
        percent = min(percent, 100)
        percent = max(percent, 0)

    percent = percent / 100
    dupes = _find_dupes()
    proper_dur = 0
    matched = 0
    total_recs = 0
    id_set = []
    for key, data in dupes.items():
        if key.startswith('SH'):
            continue
        if len(data) > 0:
            sum_actual_dur = 0
            recs = []
            for item in data:
                rec = Recording(item)
                actual_dur = rec.video_details['duration']
                proper_dur = rec.airing_details['duration']
                sum_actual_dur += actual_dur
                if proper_dur > actual_dur:
                    recs.append(rec)

            if (proper_dur * percent) > sum_actual_dur:
                matched += 1
                total_recs += len(recs)
                header = None
                for x in recs:
                    if args.id_list:
                        if x.object_id not in id_set:
                            id_set.append(x.object_id)
                    else:
                        if not header:
                            header = x.get_description() + \
                                " - " + x.episode['tms_id']
                            print(header)
                        print("\t" + str(x.object_id) + " | " +
                              x.get_description() + " - " + x.get_dur())
                if not args.id_list:
                    sum_txt = str(timedelta(seconds=sum_actual_dur))
                    total_txt = str(timedelta(seconds=proper_dur))
                    pct = str(round(sum_actual_dur / proper_dur * 100, 2))
                    print(f"\n\t{sum_txt}  /  {total_txt}  ({pct}%)")
                    print()
    if args.id_list:
        print(id_set)
    else:
        print(f"Total incomplete shows less than {percent*100}% - {matched} "
              f"({total_recs} items)")


def delete(id_list, args):
    # TODO: add a confirmation (sans --yyyyassss)
    total = len(id_list)
    if total == 0:
        print(f"Nothing to delete, exiting...")
        return
    elif total == 1:
        print(f"Deleting {total} recording")
    else:
        print(f"Deleting {total} recordings")
    print("-" * 50)

    # Load all the recs
    path = built_ins['db']['recordings']
    rec_db = TinyDB(path)
    shows = Query()
    # shortcut for later
    shows_qry = shows.data

    recs = []
    total = 0
    for obj_id in id_list:
        obj = rec_db.get(
            (shows_qry.object_id == int(obj_id))
            &
            (shows_qry.video_details.state != 'recording')
        )
        if not obj:
            print(f'ERROR: Unable to find recording with '
                  f'object_id == "{obj_id}", skipping...')
            continue

        total += 1
        recs.append(
            {
                'doc_id': obj.doc_id,
                'obj_id': obj_id,
                'rec': Recording(obj['data'])
            })

    # TODO: don't "total" like this
    if total <= 0:
        print(f"No recordings found; {len(id_list)} requested.")
    elif total == 1:
        print(f"Deleting {total} recording...")
    else:
        print(f"Deleting {total} recordings...")

    if total > 0:
        for rec in recs:
            rec = rec['rec']
            print(f" - {rec.get_actual_dur()} | {rec.get_description()} ")

        print("-" * 50)
        if not args.yes:
            print()
            print('\tAdd the "--yes" flag to actually delete things...')
            print()
        else:
            for rec in recs:
                _delete(rec, rec_db)

    print("\nFINISHED")


def _delete(rec, rec_db):
    doc_id = rec['doc_id']
    item = rec['rec']

    print(f"Deleting: {item.get_description()} ({item.get_actual_dur()})")

    if built_ins['dry_run']:
        print("DRY RUN: would have deleted...")
    else:
        try:
            # try to delete the full recording
            item.delete()
            # delete the local db record instead of REBUILDing everything
            rec_db.remove(doc_ids=[doc_id])
            print("\tDeleted!")
        except APIError:
            print("Recording no longer exists")
            pass
