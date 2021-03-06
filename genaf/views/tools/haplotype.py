
from genaf.views.tools import *

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Haplotype Summary', 'Summarize haplotypes',
            callback = func_callback )


def func_callback( query, request ):

    from fatools.lib.analytics.haploset import get_haplotype_sets

    analytical_sets = query.get_filtered_analytical_sets()
    haplotype_sets = get_haplotype_sets(analytical_sets)

    haplo_res = summarize_haplotypes(haplotype_sets)

    html, code = format_output(haplo_res, options)

    return ('Genotype Summary', html, code)


def format_output( results, options ):

    return '', ''
