# heterozygosity summary


from genaf.views.tools import *

from rhombus.lib import fsoverlay as fso


@roles(PUBLIC)
def index(request):

    return process_request( request, 'Heterozygosity (He)', 'Calculate He',
            callback = func_callback )


def func_callback( query, user ):

    from fatools.lib.analytics.he import summarize_he

    analytical_sets = query.get_filtered_analytical_sets()

    results = summarize_he(analytical_sets)
    options = {}

    html, code = format_output(results, options)

    return {    'custom': None,
                'options': None,
                'title': "Heterozygosity (He) Summary Result",
                'html': html,
                'jscode': code,
    }


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
    he_table = table(class_='table table-condensed table-striped')[
        table_header, table_body
    ]

    html.add( he_table )

    if 'test' in results:
        html.add( p('Statistics: ' + results['test'] +
            ' (p-value = %5.4f)' % results['stats'].pvalue) )

    html = div( div(html, id="toselect") )
    html.add(
        div(
            button('Select table', id="select_button", class_='btn btn-info'),
            'and use Ctrl-C to copy the table content to clipboard.'
        )
    )

    return (html, jscode)

jscode = '''

$('#select_button').click(function() {
    if (window.getSelection) {
        var range = document.createRange();
        range.selectNode( $('#toselect')[0] );
        window.getSelection().removeAllRanges();
        window.getSelection().addRange(range);
    }
});


'''