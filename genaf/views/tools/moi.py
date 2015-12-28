
from genaf.views.tools import *

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Multiplicity of Infection (MoI) Summary',
            'Calculate MoI', callback = func_callback, mode = 'allele' )


def func_callback( query, request ):

    from fatools.lib.analytics.moi import summarize_moi

    analytical_sets = query.get_filtered_analytical_sets()

    options = None
    results = summarize_moi(analytical_sets)

    html, code = format_output(results, request, options)

    return ('Multiplicity of Infection (MoI) Summary', html, code)


def format_output(results, request, options):

    dbh = get_dbhandler()

    html = div()

    # construct table header
    table_header = tr( th('') )
    labels = results.keys()
    for label in labels:
        table_header.add( th(label) )


    # construct table body
    table_body = tbody()

    for row_label, row_key in ( ('Mean', 'mean'), ('Std Dev', 'std')):
        cerr('formating table')
        table_row = tr( td(row_label) )
        table_row.add( * tuple( td('%4.3f' % getattr(results[l], row_key))
                        for l in labels ))
        table_body.add( table_row )

    # construct full table
    cerr('constructing table')
    moi_table = table(class_='table table-condensed table-striped')[
        table_header, table_body
    ]

    html.add( moi_table )

    return (html, '')



