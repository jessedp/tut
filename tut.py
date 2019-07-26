#!/usr/bin/env python

import sys
import logging
from dateutil.parser import parse
import argparse

import config
import library
import search

VERSION = "0.0.1"

EXIT_CODE_OK = 0
EXIT_CODE_ERROR = 1


def main():
    try:
        config.setup()
        parser = argparse.ArgumentParser()

        # This is gross and dirty and may break b/c it's gross and dirty
        parser._positionals.title = "Available commands"

        parser.add_argument('-v', '--verbose', action='count', default=0,
                            help="amount of program detail to output")
        parser.add_argument('--dry-run', action='store_true',
                            help="show what would happen, "
                                 "but don't change anything")
        parser.add_argument('--version', action='version',
                            version='%(prog)s ' + VERSION)

        subparsers = parser.add_subparsers(dest='command',
                                           help='available commands')

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
                                            'of Tablo recordings')
        # add mutually exclusive group?
        sp_lib.add_argument('-b', '--build', action='store_true',
                            help='build library')
        sp_lib.add_argument('-v', '--view', action='store_true',
                            help='view library')
        # sp_lib.add_argument('-s', '--search',
        #                     help='search library')
        sp_lib.add_argument('--stats', action='store_true',
                            help='search library')
        sp_lib.add_argument('--full', action='store_true',
                            help='dump/display full record details')

        # search cmd parser
        sp_search = subparsers.add_parser('search',
                                          help='library search options')

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
        sp_search.add_argument('--watched', action='store_true',
                               help='only include watched recordings')
        sp_search.add_argument('--full', action='store_true',
                               help='dump/display full record details')

        sp_search.set_defaults(func=search_default)

        # args = parser.parse_args()
        args, unknown = parser.parse_known_args()

        if len(sys.argv) == 1:
            parser.print_help(sys.stderr)
            sys.exit(1)

        if args.verbose >= 3:
            log_level = logging.DEBUG
        elif args.verbose >= 2:
            log_level = logging.INFO
        elif args.verbose >= 1:
            log_level = logging.WARNING
        else:
            log_level = logging.CRITICAL

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

            else:
                sp_lib.print_help(sys.stderr)

            return EXIT_CODE_OK

        if args.command == 'search':
            if not (args.after or args.before or args.full
                    or args.state or args.term or args.type
                    or args.limit or args.watched
                    or args.episode or args.season
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


def valid_date(s):
    try:
        return parse(s)
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def search_default(x):
    print("default!!")
    print(x)


if __name__ == '__main__':

    sys.exit(main())
