# allele summary


from genaf.views.tools import *

from rhombus.lib import fsoverlay as fso


@roles(PUBLIC)
def index(request):

    return process_request( request, 'Sample Summary', 'Summarize Samples',
            callback = func_callback, mode = 'allele' )


def func_callback( query ):

    return ("Sample Summary Report", None, None)