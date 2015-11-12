# PCoA ~ Principal Coordinate Analysis

from genaf.views.tools import *

from rhombus.lib import fsoverlay as fso


@roles(PUBLIC)
def index(request):

    return process_request( request, 'Principal Coordinate Analysis (PCoA)', 'Generate PCoA',
            callback = func_callback )


def func_callback( query, request ):

    from fatools.lib.analytics.haploset import get_haplotype_sets
    from fatools.lib.analytics.dist import get_distance_matrix

    analytical_sets = query.get_filtered_analytical_sets()
    haplotype_sets = get_haplotype_sets(analytical_sets)

    dm = get_distance_matrix(haplotype_sets)

    raise RuntimeError

def format_output(results, options=None):
    pass