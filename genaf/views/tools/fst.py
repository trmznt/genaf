
from genaf.views.tools import *

## FST calculation, uses Arlequin

@roles(PUBLIC)
def index(request):

    return process_request( request, 'FST (Arlequin)', 'Calculate FST',
            callback = func_callback )


def func_callback( query, user):

    from fatools.lib.analytics.fst_arlequin import run_arlequin, standardized_fst

    dbh = get_dbhandler()
    analytical_sets = query.get_filtered_analytical_sets()

    if len(analytical_sets) < 2:
        return {    'title': 'FST Calculation Result',
                    'html': p(b('Error:'), 'FST can be calculated with 2 or more data set'),
                    'jscode': '',
                    'custom': None,
                    'options': None }

    # prepare the directory

    fso_dir = get_fso_temp_dir(user.login)
    fst = run_arlequin( analytical_sets, dbh,  tmp_dir = fso_dir.abspath)
    fst_max = run_arlequin( analytical_sets, dbh, tmp_dir = fso_dir.abspath, recode=True)
    fst_std = standardized_fst( fst, fst_max )

    html, code = format_output( fst, fst_max, fst_std )

    return {    'custom': None,
                'options': None,
                'title': 'FST Calculation Result',
                'html': html,
                'jscode': code,
                'refs': [
                    'Excoffier, L. and H.E. L. Lischer (2010). '
                    'Arlequin suite ver 3.5: A new series of programs to perform '
                    'population genetics analyses under Linux and Windows. '
                    '<em>Molecular Ecology Resources</em>, <strong>10</strong>: 564-567.',
                    '<a href="http://cmpg.unibe.ch/software/arlequin35/">Arlequin website</a>'
                ],
    }


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
