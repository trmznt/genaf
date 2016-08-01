

from genaf.views.tools import *

import numpy as np
from math import isnan

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Data Export Utility', 'Export Data',
            callback = func_callback, form_modifier = form_modifier, mode = 'allele' )


def func_callback( query, user, ns=None ):

    analytical_sets = query.get_filtered_analytical_sets()

    options = query.options

    html, code = format_output(analytical_sets, user, options)

    return {    'custom': None,
                'options': options,
                'title': 'Data Export Utility',
                'html': html,
                'jscode': code,
    }


def form_modifier(html, javacode):
    """ add file format for data output """
    field_set = html.get('additional_fields')
    field_set.add(
        input_select(name='data_format', label='Data format', value='F',
            options = [ ('TM', 'Tab-delimited major genotypes (MLGs)'),
                        ('T', 'Tab-delimited genotypes'),
                        ('F', 'Allele Dataframe'),
                        ('A', 'Arlequin'),
                        ('L', 'LIAN / flat genotype'),
                        ('D', 'DEMEtics (format.table=F)'),
                        ('G', 'GenePOP'),
                        ('R', 'Tab-delimited R-style genotypes'),
                        ('M', 'MoI dataframe')
                        ]
        )
    )

    return (html, javacode)


def format_output(analytical_sets, user, options):

    from fatools.lib.analytics import export

    fmt = options['data_format']

    fso_dir = get_fso_temp_dir(user.login)
    html = div()
    dbh = get_dbhandler()
    outputs = {}

    if fmt == 'F':
        # return allele dataframe
        filename = 'dataframe.txt'
        outpath = fso_dir.abspath + '/' + filename
        with open(outpath, 'w') as fout:
            export.export_alleledf(analytical_sets, dbh, fout)

        outputs['fmt'] = 'Allele dataframe (tab-delimited)'
        outputs['files'] = [ (filename, fso_dir.get_urlpath(outpath)), ]

    elif fmt == 'M':
        # return MoI dataframe
        filename = 'moidf.txt'
        outpath = fso_dir.abspath + '/' + filename
        with open(outpath, 'w') as fout:
            export.export_moidf(analytical_sets, dbh, fout)

        outputs['fmt'] = 'MoI dataframe (tab-delimited)'
        outputs['files'] = [ (filename, fso_dir.get_urlpath(outpath)), ]

    elif fmt == 'A':
        # return Arlequin data format
        filename = 'arlequin.txt'
        outpath = fso_dir.abspath + '/' + filename
        with open(outpath, 'w') as fout:
            export.export_arlequin(analytical_sets, dbh, fout)

        outputs['fmt'] = 'Arlequin data format'
        outputs['files'] = [ (filename, fso_dir.get_urlpath(outpath)), ]

    elif fmt == 'L':
        # return LIAN data format
        outfiles = []
        for analytical_set in analytical_sets:
            label = analytical_set.label.replace('|','_').replace('/', '_').replace(' ', '_')
            label = label.replace("__", '_').replace('__','_')
            filename = 'flat-%s.txt' % label
            outpath = fso_dir.abspath + '/' + filename

            with open(outpath, 'w') as fout:
                export.export_flat(analytical_set, dbh, fout)
            outfiles.append( (filename, fso_dir.get_urlpath(outpath)))


        outputs['fmt'] = 'Flat MLTG data format / LIAN'
        outputs['files'] = outfiles

    elif fmt == 'T':
        # return genotype list
        filename = 'genotypes.txt'
        outpath = fso_dir.abspath + '/' + filename
        with open(outpath, 'w') as fout:
            export.export_tab(analytical_sets, dbh, fout)

        outputs['fmt'] = 'Tab-delimited genotypes file'
        outputs['files'] = [ (filename, fso_dir.get_urlpath(outpath)), ]

    elif fmt == 'TM':
        # return genotype list
        filename = 'mlgs.txt'
        outpath = fso_dir.abspath + '/' + filename
        with open(outpath, 'w') as fout:
            export.export_major_tab(analytical_sets, dbh, fout)

        outputs['fmt'] = 'Tab-delimited multi-locus genotypes (MLGs) file'
        outputs['files'] = [ (filename, fso_dir.get_urlpath(outpath)), ]

    elif fmt == 'D':
        # return DEMEtics data file in non-table format
        filename = 'demetics.txt'
        outpath = fso_dir.abspath + '/' + filename
        with open(outpath, 'w') as fout:
            export.export_demetics(analytical_sets, dbh, fout)

        outputs['fmt'] = 'DEMEtics data format'
        outputs['files'] = [ (filename, fso_dir.get_urlpath(outpath)), ]

    else:

        raise RuntimeError('Format currently not supported')


    html.add(
        table(class_='table table-condensed table-striped')[
            tr(td('Format'), td(outputs['fmt'])),
            tr(td('Files'), td( ul()[
                    tuple( li()[ a(f[0], href=f[1])] for f in outputs['files'] )
            ])),
        ]
    )

    return html, ''


