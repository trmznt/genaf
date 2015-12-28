# PCoA ~ Principal Coordinate Analysis

from genaf.views.tools import *

from rhombus.lib import fsoverlay as fso
from itertools import combinations

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Principal Coordinate Analysis (PCoA)', 'Generate PCoA',
            callback = func_callback )


def func_callback( query, request ):

    from fatools.lib.analytics.dist import get_distance_matrix
    from fatools.lib.analytics.ca import pcoa, plot_pca

    dimension = 2

    haplotype_sets = query.get_filtered_haplotype_sets()

    dm = get_distance_matrix(haplotype_sets)
    pca_res = pcoa(dm, dim = dimension)

    fso_dir = get_fso_temp_dir(request.user.login)
    plotfile_urls = []

    for (ax, ay) in combinations(range( dimension ), 2):
        plotfile = fso_dir.abspath + '/' + 'pcoa-%d-%d' % (ax, ay)
        plot_png = plot_pca(pca_res, dm, ax, ay, plotfile + '.png')
        plot_pdf = plot_pca(pca_res, dm, ax, ay, plotfile + '.pdf')
        plotfile_urls.append( (fso.get_urlpath(plot_png), fso.get_urlpath(plot_pdf)) )

    options = { 'plotfile_urls': plotfile_urls }

    html, code = format_output( (pca_res, dm), options )

    return ('Principal Coordinate Analysis (PCoA) Result', html, code)


def format_output( results, options ):

    html = div()

    if options and 'plotfile_urls' in options:
        for (png, pdf) in options['plotfile_urls']:
            html.add(
                image(src=png)
                )

    return (html, '')


