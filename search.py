from pprint import pprint
import re
from tinydb import TinyDB, Query
from config import built_ins

from util import datetime_comp
from recording import Recording


def search(args):
    path = built_ins['db']['recordings']
    rec_db = TinyDB(path)
    shows = Query()
    # shortcut for later
    shows_qry = shows.data

    # to store all possible search options/segments
    params = []

    # Handle search "term"arg - this checks title and description
    if args.term:
        params.append(
            shows_qry.airing_details.show_title.matches(
                f'.*{args.term}.*', flags=re.IGNORECASE
            )
            |
            shows_qry.episode.description.matches(
                f'.*{args.term}.*', flags=re.IGNORECASE
            )
        )

    # Handle "after" date arg
    if args.after:
        params.append(
            shows_qry.airing_details.datetime.test(
                datetime_comp, '>', args.after)
        )

    # Handle "before" date arg
    if args.before:
        params.append(
            shows_qry.airing_details.datetime.test(
                datetime_comp, '<', args.before)
        )
    # Handle recording state args
    if args.state:
        state_params = []
        for state in args.state:
            state_params.append(
                shows_qry.video_details.state == state
            )
        state_query = None
        for param in state_params:
            if not state_query:
                state_query = param
            else:
                state_query = (state_query) | (param)

        params.append(state_query)

    # Handle recording type args
    if args.type:
        type_params = []
        for rec_type in args.type:
            type_params.append(
                shows.path.matches(
                    f'.*{rec_type}.*', flags=re.IGNORECASE
                )
            )
        type_query = None
        for param in type_params:
            if not type_query:
                type_query = param
            else:
                type_query = (type_query) | (param)

        params.append(type_query)

    # Handle watched arg
    if args.watched:
        params.append(
            shows_qry.user_info.watched == True  # noqa: E712
        )

    # Handle season arg
    if args.season:
        params.append(
            shows_qry.episode.season_number == args.season
        )

    # Handle season arg
    if args.episode:
        params.append(
            shows_qry.episode.number == args.episode
        )

    # Handle tms-id arg
    if args.tms_id:
        params.append(
            shows_qry.episode.tms_id == args.tms_id
        )

    # Handle tablo object id arg
    if args.id:
        params.append(
            shows_qry.object_id == int(args.id)
        )

    # Finally, put the all the query params together and do the search
    query = None
    for param in params:
        if not query:
            query = param
        else:
            query = query & param

    if not query:
        # TODO: probably shouldn't let this happen?
        results = rec_db.all()
    else:
        results = rec_db.search(query)

    if not results:
        if args.id_list:
            print([])
        else:
            # TODO: print the criteria we tried to match
            print(f'No matching records found.')
    else:
        id_set = []
        returned = 0
        for item in results:
            if args.id_list:
                id = item['data']['object_id']
                if id not in id_set:
                    id_set.append(id)
            elif args.full:
                pprint(item)
            else:
                Recording(item['data']).print()

            returned += 1
            if args.limit and returned == args.limit:
                break
        if args.id_list:
            print(id_set)
        else :
            if returned == len(results):
                print(f'Total recordings found: {len(results)}')
            else:
                print(f'{returned}/{len(results)} total recordings displayed')
