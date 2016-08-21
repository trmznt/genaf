# genaf dbmgr script will override both rhombus' and fatools' dbmgr

import transaction, sys

from rhombus.lib.utils import cout, cerr, cexit, get_dbhandler
from rhombus.scripts import setup_settings, arg_parser

from fatools.scripts.facmd import ( init_argparser as fatools_init_argparser,
                                    do_facmd as fatools_do_facmd )


def init_argparser( parser=None ):

    if parser is None:
        p = arg_parser('facmd - genaf')
    else:
        p = parser

    p = fatools_init_argparser( p )

    return p


def main(args):

    cerr('genaf facmd main()')

    settings = setup_settings( args )

    if args.commit:
        with transaction.manager:
            do_facmd( args, settings )
            cerr('** COMMIT database **')

    else:
        cerr('** WARNING -- running without database COMMIT **')
        if not args.test:
            keys = input('Do you want to continue? ')
            if keys.lower()[0] != 'y':
                sys.exit(1)
        do_facmd( args, settings )


def do_facmd(args, settings, dbh=None):

    if dbh is None:
        dbh = get_dbhandler(settings)
    print(dbh)

    fatools_do_facmd(args, dbh)


