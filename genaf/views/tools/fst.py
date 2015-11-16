
from genaf.views.tools import *

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Haplotype Summary', 'Summarize haplotypes',
            callback = func_callback )


def func_callback( query, request ):

    pass
