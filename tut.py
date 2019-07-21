#!/usr/bin/env python

import sys
import logging

import argparse

import config
import library

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
        sp_lib.add_argument('-s', '--search',
                            help='search library')
        sp_lib.add_argument('--full', action='store_true',
                            help='dump/display full record details')

        args = parser.parse_args()

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

        if args.command == 'library':
            if args.build:
                library.build()

            elif args.view:
                library.view(args.full)

            elif args.search:
                library.search(args.search, args.full)

            else:
                sp_lib.print_help(sys.stderr)
            return EXIT_CODE_OK

        if args.command == 'config':
            if args.view:
                config.view()

            elif args.discover:
                config.discover()

            else:
                sp_cfg.print_help(sys.stderr)
            return EXIT_CODE_OK

    except KeyboardInterrupt:
        return EXIT_CODE_ERROR  # pragma: no cover


if __name__ == '__main__':

    sys.exit(main())
