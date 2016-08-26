

from genaf.views.tools import *

import numpy as np
from math import isnan

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Genotype Summary', 'Summarize genotypes',
            callback = func_callback, format_callback = format_output, mode = 'allele' )


def func_callback( query, user, ns=None ):

    from fatools.lib.analytics.he import summarize_he

    analytical_sets = query.get_filtered_analytical_sets()

    options = None
    genotypes = {}
    for analytical_set in analytical_sets:
        genotypes[analytical_set.label] = analytical_set.allele_df.genotype_df

    return {    'custom': genotypes,
                'options': options,
                'title': 'Genotype Summary',
                'html': None,
                'jscode': None,
    }


    html, code = format_output(genotypes, request, options)

    return ('Genotype Summary', html, code)


def format_output( result, request ):

    print('formatting')

    genotypes = result['custom']

    dbh = get_dbhandler()
    html = div()
    for label in genotypes:

        html.add( h4(label) )
        genotype_table = table(class_='table table-condensed table-striped')
        data = genotypes[label]
        values = data['value']
        heights = data['height']

        # add header columns
        genotype_table.add( thead()[
   			tr(th('Sample code')).add(
   					*( 	th( dbh.get_marker_by_id(m_id).label )
   						for m_id in values.columns )
                )
            ]
        )

        M = len(values.columns)

        # add sample row
        table_body = tbody()
        for alleleinfo in data.itertuples():
            print(alleleinfo)
            pairs = tuple(zip(alleleinfo[1:M+1], alleleinfo[M+1:M*2+1], alleleinfo[M*2+1:M*3+1], alleleinfo[M*3+1:]))
            print(pairs)
            sample = dbh.get_sample_by_id(alleleinfo[0])
            table_body.add(
                tr(td(a(sample.code,
                        href=request.route_url('genaf.sample-view',
                            id=sample.id))))
                .add(
                    * tuple( td( format_allele(v,h,f,i,request) ) for v,h,f,i in pairs )
                    )
                )

        genotype_table.add( table_body )
        html.add(genotype_table)

    return { 'html': html, 'jscode': '' }


def format_allele(v, h, f, i, request):
    if (type(v) is float and isnan(v)) or v is None:
        return 'NaN'
    #return 'a' + literal('<br>') + 'b'
    return literal('<br />'.join(
        str(a('%03d' % x, style="color:black;",
                href=request.route_url('genaf.assay-view', id=w, _anchor='a-'+str(z))))
        for (x,y,w,z) in zip(v, h, f, i))
    )
