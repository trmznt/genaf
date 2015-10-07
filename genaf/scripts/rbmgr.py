
## rbmgr [genaf]
##
## genaf rbmgr script will override both rhombus' rbmgr
## this script will be called by run.py
## all parameters has been set by run.py

import sys, transaction

from rhombus.lib.utils import cout, cerr, cexit
from rhombus.scripts.rbmgr import ( init_argparser as rhombus_init_argparser,
                                    do_rbmgr as rhombus_do_rbmgr,
                                    main as rhombus_main,
                                    get_dbhandler)
from rhombus.scripts import setup_settings
#from fatools.scripts.dbmgr import ( init_argparser as fatools_init_argparser,
#                                    do_dbmgr as fatools_do_dbmgr )



def init_argparser( parser = None ):

    if parser is None:
        import argparse
        p = argparse.ArgumentParser('[genaf] - rbmgr', conflict_handler='resolve')
    else:
        p = parser

    # update our argparser
    p = rhombus_init_argparser( p )

    # provide our entry here
    return p


def main(args):

    cerr('[genaf] rbmgr main()')

    rhombus_main( args )

    return

    settings = setup_settings( args )

    if any( (args.exportuserclass, args.exportgroup, args.exportenumkey) ):
        do_dbmgr( args, settings )

    elif not args.rollback and not args.test and (args.commit or args.initdb):
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

    if not rhombus_do_dbmgr(args, settings, dbh):
        cerr('ERR - command unrecognized!')


