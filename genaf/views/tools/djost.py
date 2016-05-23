
from genaf.views.tools import *

## FST calculation, uses Arlequin

@roles(PUBLIC)
def index(request):

    return process_request( request, 'D.Jost Index (DEMEtics)', 'Calculate D.Jost Index',
            callback = func_callback )


def func_callback( query, request ):

    from fatools.lib.analytics.djost_demetics import run_demetics

    dbh = get_dbhandler()
    analytical_sets = query.get_filtered_analytical_sets()

    if len(analytical_sets) < 2:
        return ('FST Calculation Result',
            p(b('Error:'), 'FST can be calculated with 2 or more data set'),
            '')

    # prepare the directory

    fso_dir = get_fso_temp_dir(request.user.login)
    fst = run_demetics( analytical_sets, dbh,  tmp_dir = fso_dir.abspath)
    #fst_max = run_arlequin( analytical_sets, dbh, tmp_dir = fso_dir.abspath, recode=True)
    #fst_std = standardized_fst( fst, fst_max )

    #html, code = format_output( fst, fst_max, fst_std )

    return ('FST Calculation Result', html, code)


def format_output( fst, fst_max, fst_std ):

    body = div()

    body.add( h4('FST') )
    body.add( create_table( fst ) )

    body.add( h4('FST Maximum') )
    body.add( create_table( fst_max ) )

    body.add( h4('FST Standardized') )
    body.add( create_table( fst_std ) )

    return (body, '')


def create_table( fst_result ):

    header_row = tr()[ th('X') ]
    for label in fst_result.get_labels():
        header_row.add( th(label) )

    t = table(class_='table table-condensed')[
        thead()[ header_row ]
    ]

    body = tbody()
    for i in range(len(fst_result.fst_m)):
        row = tr()[ td( fst_result.labels[i+1] ) ]

        for val in fst_result.fst_m[i]:
            row.add( td('%s' % val) )

        body.add( row )

    t.add( body )

    return t


    raise RuntimeError
