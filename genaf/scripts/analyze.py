# genaf dbmgr script will override both rhombus' and fatools' dbmgr

import transaction

from rhombus.lib.utils import cout, cerr, cexit
from rhombus.scripts.dbmgr import get_dbhandler
from rhombus.scripts import setup_settings

from fatools.scripts.analyze import ( init_argparser as fatools_init_argparser,
                                    do_analyze as fatools_do_analyze )


def init_argparser( parser=None ):

    if parser is None:
        import argparse
        p = argparse.ArgumentParser('facmd - genaf')
    else:
        p = parser

    p.add_argument('--config', default=False)
    p = fatools_init_argparser( p )

    return p


def main(args):

    cerr('genaf analyze main()')

    settings = setup_settings( args )

    do_analyze( args, settings )


def do_analyze(args, settings, dbh=None):

    if dbh is None:
        dbhandler_func = lambda x=None: get_dbhandler(settings)
    #print(dbh)

    fatools_do_analyze(args, dbhandler_func)


