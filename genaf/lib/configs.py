from rhombus.lib.utils import random_string
import os

TEMP_DIR = None
PROC_DIR = None
LIBEXEC_DIR = None

TEMP_ROOT_DIR = {}

SAMPLE_PARSER_MODULE = None

TEMP_GENERAL = '/general'
TEMP_UPLOADMGR = '/uploadmgr'
TEMP_TOOLS = '/tools'


def set_temp_path( fullpath ):
    global TEMP_DIR
    TEMP_DIR = fullpath
    if not os.path.exists( TEMP_DIR ):
        os.makedirs( TEMP_DIR )


def get_temp_path( path = '', root=TEMP_GENERAL ):
    root_dir = os.path.normpath("%s/%s" % (TEMP_DIR, root))
    if not root_dir in TEMP_ROOT_DIR:
        if not os.path.exists( root_dir ):
            os.makedirs( root_dir )
        TEMP_ROOT_DIR[root_dir] = True
    return os.path.normpath("%s/%s" % (root_dir, path))


def set_proc_path( fullpath ):
    global PROC_DIR
    PROC_DIR = fullpath


def get_proc_path( path = None ):
    if path is None:
        path = random_string(8)
    return "%s/%s" % (PROC_DIR, path)


def set_libexec_path( fullpath ):
    global LIBEXEC_PATH
    LIBEXEC_PATH = fullpath
    if not os.path.exists(LIBEXEC_PATH):
        raise RuntimeError('LIBEXEC_PATH: %s does not exist!' % LIBEXEC_PATH)


def get_libexec_path( path = '' ):
    return "%s/%s" % (LIBEXEC_PATH, path)


def set_sampleparser_module( module ):
    global SAMPLEPARSER_MODULE
    # check sanity
    for func_name in ['']:
        if hasattr(module, ''):
            raise RuntimeError('PROG/ERR - module does not have %s function' % s)
    SAMPLEPARSER_MODULE = module


def get_sampleparser_module():
    return SAMPLEPARSER_MODULE
