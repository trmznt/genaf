# heterozygosity summary


from genaf.views.tools import *

from rhombus.lib import fsoverlay as fso


@roles(PUBLIC)
def index(request):

    return process_request( request, 'Heterozygosity (He)', 'Calculate He',
            callback = func_callback )


def func_callback( query, request ):

    from fatools.lib.analytics.he import summarize_he

    analytical_sets = query.get_filtered_analytical_sets()

    results = summarize_he(analytical_sets)
    options = {}

    html, code = format_output(results, options)

    return render_to_response("genaf:templates/tools/report.mako",
    		{	'header_text': 'Heterozygosity (He) Summary Result',
    			'html': html,
    			'code': code,
    		}, request = request )


def format_output(results, options=None):

    dbh = get_dbhandler()

    html = div()

    df = results['data']
    labels = list(df.columns)

    # construct table header
    table_header = tr( th('Markers'))
    for label in labels:
        table_header.add( th(label) )

    # construct table body
    table_body = tbody()
    for marker_id in df.index:
        table_row = tr( td(dbh.get_marker_by_id(marker_id).label ))
        table_row.add( * tuple( td('%4.3f' % x) for x in df.loc[marker_id]))
        table_body.add(table_row)

    # add average and stddev
    for label, row in zip( ['Mean', 'Std Dev'], [results['mean'], results['stddev']]):
        table_row = tr( td(label) )
        table_row.add( * tuple( td('%4.3f' % x) for x in row ) )
        table_body.add(table_row)

    # consruct table
    he_table = table(class_='table table-condense table-striped')[
        table_header, table_body
    ]
    html.add( he_table )
    html.add( p('Statistics: ' + results['test'] +
            ' (p-value = %5.4f)' % results['stats'].pvalue) )

    return (html, '')
