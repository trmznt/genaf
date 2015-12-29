from genaf.views.tools import *

from rhombus.lib import fsoverlay as fso

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Neighbor-Joining Tree (NJ)', 'Generate NJ',
            callback = func_callback )


def func_callback( query, request ):

    from fatools.lib.analytics.dist import get_distance_matrix
    from fatools.lib.analytics.nj import plot_nj

    haplotype_sets = query.get_filtered_haplotype_sets()

    dm = get_distance_matrix(haplotype_sets)

    dbh = get_dbhandler()
    fso_dir = get_fso_temp_dir(request.user.login)

    njplot_png = plot_nj(dm, fso_dir.abspath, 'png',
            label_callback = lambda x: dbh.get_sample_by_id(x).code)
    njplot_pdf = plot_nj(dm, fso_dir.abspath, 'pdf',
            label_callback = lambda x: dbh.get_sample_by_id(x).code)

    options = { 'png_plot': fso.get_urlpath(njplot_png),
                'pdf_plot': fso.get_urlpath(njplot_pdf) }

    html, code = format_output( options )

    return ('Neighbor-Joining (NJ) Tree Result', html, code)


def format_output( options ):

    html = div()

    if options:
        html.add(
                image(src=options['png_plot'])
                )

    return (html, '')