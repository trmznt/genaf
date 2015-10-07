
# genaf dbmgr script will override both rhombus' and fatools' dbmgr

import sys, transaction

from rhombus.lib.utils import cout, cerr, cexit, get_dbhandler
from rhombus.scripts import setup_settings
from rhombus.scripts.rbmgr import db_argparser
from fatools.scripts.dbmgr import ( init_argparser as fatools_init_argparser,
                                    do_dbmgr as fatools_do_dbmgr )



def init_argparser( parser = None ):

    if parser is None:
        import argparse
        p = argparse.ArgumentParser('dbmgr [genaf]', conflict_handler='resolve')
    else:
        p = parser

    # update our argparser
    p = fatools_init_argparser( db_argparser(p) )

    # provide our entry here
    return p


def main(args):

    cerr('genaf dbmgr main()')

    settings = setup_settings( args )

    if not args.rollback and not args.test and args.commit:
        with transaction.manager:
            do_dbmgr( args, settings )
            cerr('** COMMIT database **')

    else:
        cerr('** WARNING -- running without database COMMIT **')
        if not args.rollback and not args.test:
            keys = input('Do you want to continue [y/n]: ')
            if keys.lower()[0] != 'y':
                sys.exit(1)
        do_dbmgr( args, settings )


def do_dbmgr(args, settings, dbh=None):

    if dbh is None:
        dbh = get_dbhandler(settings, initial = args.initdb)
    print(dbh)

    fatools_do_dbmgr(args, dbh, warning=False)


