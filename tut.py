#!/usr/bin/env python
# gross, but do this before anything (including other modules) are loaded
import gevent.monkey  # noqa
gevent.monkey.patch_all(thread=False)  # noqa

import sys
import re
from ast import literal_eval
from dateutil.parser import parse
import logging

import export
import search
import library
import config
import argparse

VERSION = "0.0.2"

EXIT_CODE_OK = 0
EXIT_CODE_ERROR = 1


def main():
    try:
        config.setup()
        parser = argparse.ArgumentParser()

        # This is gross and dirty and may break b/c it's gross and dirty
        parser._positionals.title = "Available commands"

        parser.add_argument('-v', '--verbose', action='count', default=0,
                            help="amount of detail to display add vs (-vvvv) "
                                 "for maximum amount")
        parser.add_argument('--dry-run', action='store_true',
                            help="show what would happen, "
                                 "but don't change anything")
        parser.add_argument('--version', action='version',
                            version='%(prog)s ' + VERSION)

        subparsers = parser.add_subparsers(dest='command')

        # "config" cmd parser
        sp_cfg = subparsers.add_parser('config',
                                       help='manage configuration options')
        # add mutually exclusive group?
        sp_cfg.add_argument('-v', '--view', action='store_true',
                            help='view the current config data')
        sp_cfg.add_argument('-d', '--discover', action='store_true',
                            help='discover Tablos')

        # "library" cmd parser
        sp_lib = subparsers.add_parser('library',
                                       help='manage the local library '
                                            'of recordings')
        # add mutually exclusive group?
        sp_lib.add_argument('-b', '--build', action='store_true',
                            help='build library')
        sp_lib.add_argument('-v', '--view', action='store_true',
                            help='view library')
        sp_lib.add_argument('--stats', action='store_true',
                            help='search library')
        sp_lib.add_argument('--full', action='store_true',
                            help='dump/display full record details')
        sp_lib.add_argument('--dupes', action='store_true',
                            help='show what may be duplicate recordings. '
                                 "There's a good chance these are pieces of a "
                                 "partial recording")
        sp_lib.add_argument('--incomplete', nargs="?", type=int, default=-2,
                            const=-1,
                            help='show what may be incomplete recordings. Add '
                                 'a number to limit to less than that percent'
                                 'of a full show. "Similar to --dupes, but '
                                 "tries to show the dupes that can't be"
                                 'combined into a possibly useful single '
                                 'recording.')

        # search cmd parser
        sp_search = subparsers.add_parser('search',
                                          help='ways to search your library')

        sp_search.add_argument('-t', '--term',
                               help='search title/description for this')
        sp_search.add_argument('-a', '--after',
                               type=valid_date,
                               help='only recordings after this date')
        sp_search.add_argument('-b', '--before',
                               type=valid_date,
                               help='only recordings before this date')
        sp_search.add_argument('--limit', type=int,
                               help='only recordings in this state')
        sp_search.add_argument('--season', type=int,
                               help='episodes with this season')
        sp_search.add_argument('--episode', type=int,
                               help='episodes with this episode number')
        sp_search.add_argument('--state', action="append",
                               choices=['finished', 'failed', 'recording'],
                               help='only recordings in this state')
        sp_search.add_argument('--type', action="append",
                               choices=['episode', 'movie',
                                        'sport', 'programs'],
                               help='only include these recording types')
        sp_search.add_argument('--duration',
                               type=valid_duration,
                               help="recordings less than this length "
                                    "(28m, 10s, 1h. etc) - useful for culling "
                                    "bad recordings")
        sp_search.add_argument('--watched', action='store_true',
                               help='only include watched recordings')
        sp_search.add_argument('--full', action='store_true',
                               help='dump/display full record details')
        sp_search.add_argument('--tms-id',
                               help='select by TMS Id (probably unique)')
        sp_search.add_argument('--id', type=int,
                               help='select by Tablo Object Id'
                                    '(definitely unique)')
        sp_search.add_argument('-L', '--id-list', action='store_true',
                               help='only output a list matching Object Ids - '
                                    'Pipe this into other commands. '
                                    '(overrides --full and any other output)')

        # "copy" cmd parser
        sp_copy = subparsers.add_parser('copy',
                                        help='copy recordings somewhere')
        sp_copy.add_argument('--infile', nargs='?',
                             type=argparse.FileType('r'),
                             help="file with list of ids to use",
                             default=sys.stdin)

        sp_copy.add_argument('--clobber', action='store_true',
                             default=False,
                             help='should we overwrite existing files?')

        # "delete" cmd parser
        sp_delete = subparsers.add_parser('delete',
                                          help='delete recordings from the '
                                          'Tablo device')
        sp_delete.add_argument('--infile', nargs='?',
                               type=argparse.FileType('r'),
                               help="file with list of ids to use",
                               default=sys.stdin)

        sp_delete.add_argument('--yes', '--yyaaassss', action='store_true',
                               default=False,
                               help='This must be set to actually delete '
                                    'stuff')

        # args = parser.parse_args()
        args, unknown = parser.parse_known_args()

        if len(sys.argv) == 1:
            parser.print_help(sys.stderr)
            sys.exit(EXIT_CODE_ERROR)

        if args.verbose >= 3:
            log_level = logging.DEBUG
        elif args.verbose >= 2:
            log_level = logging.INFO
        elif args.verbose >= 1:
            log_level = logging.WARNING
        else:
            log_level = logging.CRITICAL

        config.built_ins['log_level'] = log_level
        config.setup_logger(log_level)

        config.built_ins['dry_run'] = args.dry_run

        if args.command == 'config':
            if args.view:
                config.view()

            elif args.discover:
                config.discover()

            else:
                sp_cfg.print_help(sys.stderr)

            return EXIT_CODE_OK

        if args.command == 'library':
            if args.build:
                library.build()
            elif args.view:
                library.view(args.full)
            elif args.stats:
                library.print_stats()
            elif args.dupes:
                library.print_dupes()
            elif args.incomplete and args.incomplete != -2:
                # TODO: all of what I've done here can't be the right way.
                if args.incomplete == -1:
                    args.incomplete = 100
                library.print_incomplete(args.incomplete)
            else:
                sp_lib.print_help(sys.stderr)

            return EXIT_CODE_OK

        if args.command == 'search':
            if not (args.after or args.before or args.full
                    or args.state or args.term or args.type
                    or args.limit or args.watched
                    or args.episode or args.season
                    or args.tms_id or args.id or args.id_list
                    or args.duration
                    or search_unknown(unknown)
                    ):
                sp_search.print_help(sys.stderr)
                return EXIT_CODE_OK
            else:
                # nothing that looked like an arg and not blank. try it.
                if search_unknown(unknown):
                    args.term = " ".join(unknown)
                    search.search(args)
                else:
                    search.search(args)

            return EXIT_CODE_OK

        if args.command == 'copy':
            print("Gathering data, [ENTER] to quit")
            data = args.infile.readline()
            try:
                id_list = check_input(data)
            except ValueError:
                sp_copy.print_help(sys.stderr)
                return EXIT_CODE_ERROR
            export.copy(id_list, args)

            return EXIT_CODE_OK

        if args.command == 'delete':
            print("Gathering data, [ENTER] to quit")
            data = args.infile.readline().rstrip()
            try:
                id_list = check_input(data)
            except ValueError:
                sp_delete.print_help(sys.stderr)
                return EXIT_CODE_ERROR
            library.delete(id_list, args)

            return EXIT_CODE_OK

    except KeyboardInterrupt:
        return EXIT_CODE_ERROR  # pragma: no cover


def search_unknown(str):
    if "-" in " ".join(str):
        return False
    elif len(str) == 0:
        return False
    elif not str:
        return False
    else:
        return True


def check_input(data):
    try:
        id_list = literal_eval(data)
    except (ValueError, SyntaxError):
        if data.rstrip() == "":
            print("No data provided")
        else:
            print(f'"{data}" is not a valid List')
        raise ValueError

    if type(id_list) is not list:
        print(f'"{id_list}" is not a valid List')
        raise ValueError

    errs = []
    for i in id_list:
        if type(i) is not int:
            errs.append(f'"{i}" is not an integer')

    if len(errs) != 0:
        for e in errs:
            print(e)
            raise ValueError

    return id_list


def valid_date(s):
    try:
        return parse(s)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def valid_duration(s):
    # doesn't deal with something like 28m5s or 27:40m
    # eg. 1s => 1 , 1m => 60, 1h => 3600
    parts = re.match('(\\d+)([hms]?)', s)
    if parts[2] == "" or parts[2] == "s":
        return int(parts[1])
    elif parts[2] == "m":
        return int(parts[1]) * 60
    elif parts[2] == "h":
        return int(parts[1]) * 3600


if __name__ == '__main__':
    code = main()
    sys.stderr.close()

    sys.exit(code)
