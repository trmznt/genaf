# PCoA ~ Principal Coordinate Analysis

from genaf.views.tools import *

from rhombus.lib import fsoverlay as fso
from itertools import combinations

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Principal Coordinate Analysis (PCoA)', 'Generate PCoA',
            callback = func_callback )


def func_callback( query, user ):

    from fatools.lib.analytics.dist import get_distance_matrix
    from fatools.lib.analytics.ca import pcoa, plot_pca, format_data

    dimension = 2

    haplotype_sets = query.get_filtered_haplotype_sets()

    dm = get_distance_matrix(haplotype_sets)
    pca_res = pcoa(dm, dim = dimension)

    fso_dir = get_fso_temp_dir(user.login)
    plotfile_urls = []

    for (ax, ay) in combinations(range( dimension ), 2):
        plotfile = fso_dir.abspath + '/' + 'pcoa-%d-%d' % (ax, ay)
        plot_png = plot_pca(pca_res, dm, ax, ay, plotfile + '.png')
        plot_pdf = plot_pca(pca_res, dm, ax, ay, plotfile + '.pdf')
        plotfile_urls.append( (fso.get_urlpath(plot_png), fso.get_urlpath(plot_pdf)) )

    pca_data = format_data(pca_res, dm)
    data_file = fso_dir.abspath + '/' + 'pcoa-data.txt'
    with open(data_file, 'w') as outfile:
        for r in pca_data:
            outfile.write( '\t'.join( r ) )
            outfile.write( '\n' )

    options = { 'plotfile_urls': plotfile_urls, 'data_file': fso.get_urlpath(data_file) }

    html, code = format_output( (pca_res, dm), options )

    return {    'custom': None,
                'options': None,
                'title': 'Principal Coordinate Analysis (PCoA) Result',
                'html': html,
                'jscode': code,
    }

    return ('Principal Coordinate Analysis (PCoA) Result', html, code)


def format_output( results, options ):

    html = div()

    if options and 'plotfile_urls' in options:
        for (png, pdf) in options['plotfile_urls']:
            html.add(
                image(src=png),
                br(),
                p(a('Click here to get the plot as a PDF file', href=pdf)),
                )

    html.add(
        br(),
        'Download data file here: ',
        a('data.txt', href=options['data_file']),
    )

    return (html, '')


