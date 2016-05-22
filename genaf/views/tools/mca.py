# Multiple Correspondence Analysis

from genaf.views.tools import *

from rhombus.lib import fsoverlay as fso

from genaf.views.tools.pcoa import format_output

from itertools import combinations

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Multiple Correspondence Analysis (MCA) Result',
        'Generate MCA', callback = func_callback)


def func_callback( query, user ):

    from fatools.lib.analytics.dist import get_distance_matrix, null_distance
    from fatools.lib.analytics.ca import mca, plot_pca

    dimension = 2

    haplotype_sets = query.get_filtered_haplotype_sets()
    dm = get_distance_matrix(haplotype_sets, null_distance)
    mca_res = mca(dm)

    fso_dir = get_fso_temp_dir(user.login)
    plotfile_urls = []

    for (ax, ay) in combinations(range( dimension ), 2):
        plotfile = fso_dir.abspath + '/' + 'pcoa-%d-%d' % (ax, ay)
        plot_png = plot_pca(mca_res, dm, ax, ay, plotfile + '.png')
        plot_pdf = plot_pca(mca_res, dm, ax, ay, plotfile + '.pdf')
        plotfile_urls.append( (fso.get_urlpath(plot_png), fso.get_urlpath(plot_pdf)) )

    options = { 'plotfile_urls': plotfile_urls }

    html, code = format_output( (mca_res, dm), options )

    return {    'custom': None,
                'options': None,
                'title': 'Multiple Correspondence Analysis (MCA) Result',
                'html': html,
                'jscode': code,
    }

    return ('Multiple Correspondence Analysis (MCA) Result', html, code)
