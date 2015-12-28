# allele summary


from genaf.views.tools import *

from rhombus.lib import fsoverlay as fso


PLOTFILE = 'alleles.pdf'
TABFILE = 'alleles.tab'

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Sample Summary', 'Summarize Samples',
            callback = func_callback, mode = 'allele' )


def func_callback( query, request ):

    return ("Sample Summary Report", None, None)