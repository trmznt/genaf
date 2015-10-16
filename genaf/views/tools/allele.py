# allele summary 


from genaf.views.tools import *


@roles(PUBLIC)
def index(request):
    
    return process_request( request, 'Allele Summary', 'Summarize Alleles',
            callback = func_callback )


def func_callback( query, request ):

    from fatools.lib.analytics.summary import summarize_alleles, plot_alleles

    analytical_sets = query.get_filtered_analytical_sets()
    report = summarize_alleles( analytical_sets )

    html, code = format_output(report)

    return render_to_response("genaf:templates/tools/report.mako",
    		{	'header_text': 'Allele Summary Result',
    			'html': html,
    			'code': code,
    		}, request = request )


def format_output(summaries):

    dbh = get_dbhandler()

    html = div()

    for label in summaries:
        summary = summaries[label]['summary']
        html.add( h3()[ 'Sample Set: %s' % label ] )

        marker_div = div()
        for marker_id in summary:
            marker_div.add(
            	p('Marker ID: %d' % marker_id),
            	p('Marker code: %s' % dbh.get_marker_by_id(marker_id).label),
            	p('Unique alleles: %d' % summary[marker_id]['unique_allele']),
            	p('Total alleles: %d' % summary[marker_id]['total_allele'])
            )

            tbl = table()
            for data in summary[marker_id]['alleles']:
                tbl.add(
                	tr()[
                		td('%3d' % data[0]),
                		td('%5.3f' % data[1]),
                	]
                )
            marker_div.add( tbl )
        html.add( marker_div )

    return (marker_div, '')
#            %3d  %5.3f  %3d  %5.2f - %5.2f  %5.2f  %4.2f' %
#                        (data[0], data[1], data[2], data[4], data[5], data[8], data[6]))
#    
#    retu
#
#	return ("", "")
