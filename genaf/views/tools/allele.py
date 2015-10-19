# allele summary 


from genaf.views.tools import *


PLOTFILE = 'alleles.pdf'
TABFILE = 'alleles.tab'

@roles(PUBLIC)
def index(request):
    
    return process_request( request, 'Allele Summary', 'Summarize Alleles',
            callback = func_callback )


def func_callback( query, request ):

    from fatools.lib.analytics.summary import summarize_alleles, plot_alleles

    analytical_sets = query.get_filtered_analytical_sets()
    report = summarize_alleles( analytical_sets )

    options={}
    fso_dir = None
    if False:
    	# create plot file
    	if fso_dir is None:
    		fso_dir = get_fso_temp_dir(request.user.login)

    	plotfile = fso_dir.abspath + '/' + PLOTFILE
    	plot_alleles(report, plotfile)
    	options['plotfile'] = fso.get_virtpath(plotfile)


    if False:
    	# create tab-delimited text file
    	if fso_dir is None:
    		fso_dir = get_fso_temp_dir(request.user.login)

    	tabfile = fso_dir.abspath + '/' + TABFILE
    	options['tabfile'] = fso.get_virpath(tabfile)

    html, code = format_output(report, options)

    return render_to_response("genaf:templates/tools/report.mako",
    		{	'header_text': 'Allele Summary Result',
    			'html': html,
    			'code': code,
    		}, request = request )


def format_output(summaries, plotfile=None):


    dbh = get_dbhandler()

    html = div()

    for label in summaries:
        summary = summaries[label]['summary']
        html.add( h3()[ 'Sample set: %s' % label ] )

        marker_div = div()
        for marker_id in summary:
            marker_div.add(
            	h4(dbh.get_marker_by_id(marker_id).label),
            	p('Unique alleles: %d' % summary[marker_id]['unique_allele']),
            	p('Total alleles: %d' % summary[marker_id]['total_allele'])
            )

            tbl = table(class_='table table-condensed table-striped')
            tbl.add(
            	thead(
            		tr(
            			th('Allele'), th('Freq'), th('Count'), th('Boundaries'),
            			th('Mean'), th('Delta')
            		)
            	)
            )
            tbl_body = tbody()
            tbl.add( tbl_body )
            for data in summary[marker_id]['alleles']:
                tbl_body.add(
                	tr()[
                		td('%3d' % data[0]),
                		td('%5.3f' % data[1]),
                		td('%3d' % data[2]),
                		td('%5.2f - %5.2f' % (data[4], data[5])),
                		td('%5.2f' % data[8]),
                		td('%4.2f' % data[6]),
                	]
                )
            marker_div.add( tbl )
        html.add( marker_div )

    return (html, '')
#            %3d  %5.3f  %3d  %5.2f - %5.2f  %5.2f  %4.2f' %
#                        (data[0], data[1], data[2], data[4], data[5], data[8], data[6]))
#    
#    retu
#
#	return ("", "")
