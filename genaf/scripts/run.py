
import sys, os
import argparse

from rhombus.scripts.run import main as rhombus_main, set_config
from rhombus.lib.utils import cout, cerr, cexit

from genaf.models.handler import DBHandler

def greet():
    cerr('genaf-run')

def usage():
    cerr('genaf-run usage')


print("genaf run.py")
set_config( environ='GENAF_CONFIG',
            paths = [ 'fatools.scripts.', 'genaf.scripts.' ],
            greet = greet,
            usage = usage,
            dbhandler_class = DBHandler
)

main = rhombus_main
