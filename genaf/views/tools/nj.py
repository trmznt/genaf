from genaf.views.tools import *

from rhombus.lib import fsoverlay as fso


@roles(PUBLIC)
def index(request):

    return process_request( request, 'Neighbor-Joining Tree (NJ)', 'Generate NJ',
            callback = func_callback, form_modifier = form_modifier )


def form_modifier(html, javacode):
    """ add tip labeling form """
    field_set = html.get('additional_fields')
    field_set.add(
        input_select(name='tip_label', label='Tip label', value='S',
            options = [ ('S', 'Sample Code'),
                        ('I', 'Sample ID'),
                        ('C', 'Country'),
                        ('1', 'Administrative Level 1'),
                        ('2', 'Administrative Level 2'),
                        ('3', 'Administrative Level 3'),
                        ('4', 'Administrative Level 4'),
                    ]
            )
    )

    return html, javacode



def func_callback( query, user ):

    from fatools.lib.analytics.dist import get_distance_matrix
    from fatools.lib.analytics.nj import plot_nj

    haplotype_sets = query.get_filtered_haplotype_sets()

    dm = get_distance_matrix(haplotype_sets)

    dbh = query.dbh
    fso_dir = get_fso_temp_dir(user.login)

    tip_label = query.options.get('tip_label', 'S')
    label_callback = {
        'S': lambda x: dbh.get_sample_by_id(x).code,
        'I': None,
        'C': lambda x: dbh.get_sample_by_id(x).location.country,
        '1': lambda x: dbh.get_sample_by_id(x).location.level1,
        '2': lambda x: dbh.get_sample_by_id(x).location.level2,
        '3': lambda x: dbh.get_sample_by_id(x).location.level3,
        '4': lambda x: dbh.get_sample_by_id(x).location.level4,
    }

    njplot_png = plot_nj(dm, fso_dir.abspath, 'png',
            label_callback = label_callback[tip_label])
    njplot_pdf = plot_nj(dm, fso_dir.abspath, 'pdf',
            label_callback = label_callback[tip_label])

    options = { 'png_plot': fso.get_urlpath(njplot_png),
                'pdf_plot': fso.get_urlpath(njplot_pdf) }

    html, code = format_output( options )

    return {    'custom': None,
                'options': None,
                'title': 'Neighbor-Joining (NJ) Tree Result',
                'html': html,
                'jscode': code,
                'refs': [
                    'Paradis E., Claude J. & Strimmer K. (2004) '
                    'APE: analyses of phylogenetics and evolution in R language. '
                    '<em>Bioinformatics</em>, <strong>20</strong>: 289-290',
                    '<a href="http://ape-package.ird.fr/">APE website</a>'
                ],
    }


def format_output( options ):

    html = div()

    if options:
        html.add(
                image(src=options['png_plot']),
                p(a('Click here to get the plot as a PDF file!', href=options['pdf_plot']))
                )

    return (html, '')