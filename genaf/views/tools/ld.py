from genaf.views.tools import *

@roles(PUBLIC)
def index(request):

    return process_request( request, 'LD (lian - LInkage ANalysis)', 'Calculate LD',
            callback = func_callback )


def func_callback( query, user ):

    from fatools.lib.analytics.ld_lian import run_lian

    dbh = get_dbhandler()
    analytical_sets = query.get_filtered_analytical_sets()

    # using LIAN, we don't have to prepare temporary directory

    results = run_lian(analytical_sets, dbh)

    html, code = format_output(results)

    return {    'custom': None,
                'options': None,
                'title': 'LD Calculation Result',
                'html': html,
                'jscode': code,
    }


def format_output(results):

    body = div()

    for (label, lian_result) in results:

        t = table(class_='table table-condensed table-striped')[
                tr()[ td('LD'), td(lian_result.get_LD()) ],
                tr()[ td('p-value'), td(lian_result.get_pvalue())],
        ]

        body.add( h3(label), t )

    return div(class_='row')[ div(class_='col-md-12')[ body ] ], ''

