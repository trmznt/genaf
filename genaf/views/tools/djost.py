
from genaf.views.tools import *
from rhombus.lib import fsoverlay as fso
from itertools import combinations_with_replacement

## D.jost index calculation, uses DEMETICS

@roles(PUBLIC)
def index(request):

    return process_request( request, 'D.Jost Index (DEMEtics)', 'Calculate D.Jost Index',
            callback = func_callback )


def func_callback( query, user, temp_dir = None ):

    from fatools.lib.analytics.djost_demetics import run_demetics

    dbh = get_dbhandler()
    analytical_sets = query.get_filtered_analytical_sets()

    if len(analytical_sets) < 2:
        return {    'title': 'D-Jost Calculation Result',
                    'html': p(b('Error:'), 'D-Jost can be calculated with 2 or more data set'),
                    'jscode': '',
                    'custom': None,
                    'options': None }

    # prepare the directory

    if not temp_dir: temp_dir = get_fso_temp_dir(user.login)
    djost = run_demetics( analytical_sets, dbh,  tmp_dir = temp_dir.abspath)
    #fst_max = run_arlequin( analytical_sets, dbh, tmp_dir = fso_dir.abspath, recode=True)
    #fst_std = standardized_fst( fst, fst_max )

    html, code = format_output( djost )

    return {    'custom': None,
                'options': None,
                'title': 'D-Jost Calculation Result',
                'html': html,
                'jscode': code,
    }


def format_output( djost ):

    body = div()

    body.add( h4('D-Jost') )
    body.add( create_table( djost['M'] ) )

    if djost['msg']:
        body.add(br(), b('Warning: '), djost['msg'])

    body.add(
        br(),
        a('Data download link', href=fso.get_urlpath( djost['data_file'] )),
    )

    return (body, '')


def create_table( djost ):

    labels = sorted(djost.keys())
    print(labels)

    header_row = tr()[ th('X') ]
    for label in labels:
        header_row.add( th(label) )

    t = table(class_='table table-condensed')[
        thead()[ header_row ]
    ]

    body = tbody()
    for l1 in labels:
        row = tr()[ td( l1 ) ]

        for l2 in labels:
            if l1 == l2:
                row.add( td('-') )
            else:
                row.add( td('%s' % djost[l2][l1]) )

        body.add( row )

    t.add( body )

    return t
