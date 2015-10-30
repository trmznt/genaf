

from genaf.views.tools import *

import numpy as np
from math import isnan

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Genotype Summary', 'Summarize genotypes',
            callback = func_callback )


def func_callback( query, request ):

    from fatools.lib.analytics.he import summarize_he

    analytical_sets = query.get_filtered_analytical_sets()

    options = None
    genotypes = {}
    for analytical_set in analytical_sets:
        genotypes[analytical_set.label] = analytical_set.allele_df.genotype_df

    html, code = format_output(genotypes, request, options)

    return render_to_response("genaf:templates/tools/report.mako",
        {	'header_text': 'Genotype Summary',
    			'html': html,
    			'code': code,
        }, request = request )


def format_output( genotypes, request, options ):

    print('formatting')

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
            pairs = tuple(zip(alleleinfo[1:M+1], alleleinfo[M+1:]))
            print(pairs)
            sample = dbh.get_sample_by_id(alleleinfo[0])
            table_body.add(
                tr(td(a(sample.code,
                        href=request.route_url('genaf.sample-view',
                            id=sample.id))))
                .add(
                    * tuple( td( format_allele(v,h) ) for v,h in pairs )
                    )
                )

        genotype_table.add( table_body )
        html.add(genotype_table)
        html.add( b('a') )

    #raise RuntimeError

    return html, ''


def format_allele(v,h):
    if type(v) is float and isnan(v):
        return 'NaN'
    #return 'a' + literal('<br>') + 'b'
    return literal('<br />'.join('%03d' % x for x in v))
