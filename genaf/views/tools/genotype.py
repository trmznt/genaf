

from genaf.views.tools import *

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Heterozygosity (He)', 'Calculate He',
            callback = func_callback )


def func_callback( query, request ):

    from fatools.lib.analytics.he import summarize_he

    analytical_sets = query.get_filtered_analytical_sets()

    options = None
    genotypes = {}
    for analytical_set in analytical_sets:
        genotypes[analytical_set.label] = analytical_set.allele_df.genotype_df

    html, code = format_output(genotypes, options)

    return render_to_response("genaf:templates/tools/report.mako",
        {	'header_text': 'Genotype Summary',
    			'html': html,
    			'code': code,
        }, request = request )


def format_output( genotypes, options ):

    print('formatting')

    dbh = get_dbhandler()
    html = div()
    for label in genotypes:

        html.add( h4(label) )
        genotype_table = table(class_='table table-condensed table-striped')
        data = genotypes[label]

        # add header columns
        genotype_table.add( thead()[
   			tr(td('Sample code')).add(
   					*( 	td( dbh.get_marker_by_id(m_id).label )
   						for m_id in data.columns.levels[1] )
                )
            ]
        )

        # add sample row
        table_body = tbody()
        for sample_id, alleles in data.iterrows():
            table_body.add(
                tr(td(sample_id)).add(
                    * ( td(x) for x in alleles )
                    )
                )

        genotype_table.add( table_body )
        html.add(genotype_table)

    #raise RuntimeError

    return html, ''

