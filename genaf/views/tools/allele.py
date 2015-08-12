# allele summary 


from genaf.views.tools import *


@roles(PUBLIC)
def index(request):
    
    return process_request( request, 'Allele Summary', 'Summarize Alleles',
            callback = func_callback )


def func_callback( query ):

    analytical_sets = query.get_filtered_analytical_sets()
