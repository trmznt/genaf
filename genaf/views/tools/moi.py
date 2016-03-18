
from genaf.views.tools import *
from rhombus.lib import fsoverlay as fso

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Multiplicity of Infection (MoI) Summary',
            'Calculate MoI', callback = func_callback, mode = 'allele' )


def func_callback( query, request ):

    from fatools.lib.analytics.moi import summarize_moi

    analytical_sets = query.get_filtered_analytical_sets()

    options = None
    results = summarize_moi(analytical_sets)

    html, code = format_output(results, request, options)

    return ('Multiplicity of Infection (MoI) Summary', html, code)


def format_output(results, request, options):

    dbh = get_dbhandler()

    html = div()

    # construct table header
    table_header = tr( th('') )
    labels = results.keys()
    for label in labels:
        table_header.add( th(label) )


    # construct table body
    table_body = tbody()

    for row_label, row_key in ( ('Mean', 'mean'), ('Median', 'med'),
                                ('Max', 'max'), ('Std Dev', 'std')):
        cerr('formating table')
        table_row = tr( td(row_label) )
        table_row.add( * tuple( td('%4.3f' % getattr(results[l], row_key))
                        for l in labels ))
        table_body.add( table_row )

    table_row = tr( td('# of polyclonal samples)') )
    for l in labels:
        res = results[l]
        table_row.add( td('%d (%3.2f)' % (res.M, res.M/res.N)) )
    table_body.add( table_row )

    # construct histonum

    table_row = tr( td('# of MoI') )
    for l in labels:
        res = results[l]
        txt = "<table><tr><td>MoI &nbsp;|&nbsp;</td><td># samples</td></tr>"
        for r in res.histogram.items():
            txt += '<tr><td> %d </td><td> %d </td></tr>' % r
        txt += '</table>'
        table_row.add( td( literal(txt) ))
    table_body.add( table_row )

    table_row = tr( td('# of polyclonal markers') )
    for l in labels:
        res = results[l]
        txt = "<table><tr><td># markers &nbsp;|&nbsp;</td><td># samples</td></tr>"
        for r in res.alleles.items():
            txt += '<tr><td> %d </td><td> %d </td></tr>' % r
        txt += '</table>'
        table_row.add( td( literal(txt) ))
    table_body.add( table_row )


    table_row = tr( td('Polyclonality by markers') )
    for l in labels:
        res = results[l]
        txt = "<table><tr><td>Marker &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;</td><td>Proportion</td></tr>"
        for r in res.markers.items():
            txt += '<tr><td>%s</td><td>%4.3f</td></tr>' % (
                dbh.get_marker_by_id(r[0]).code, r[1]/res.N)
        txt += '</table>'
        table_row.add( td( literal(txt) ))
    table_body.add( table_row )


    table_row = tr( td('Polyclonality rank') )
    for l in labels:
        res = results[l]
        txt = "<table><tr><td>Marker &nbsp;&nbsp;&nbsp;&nbsp;|&nbsp;</td><td>Proportion</td></tr>"
        for r in res.markers_rank:
            txt += '<tr><td>+ %s</td><td>%4.3f</td></tr>' % (
                dbh.get_marker_by_id(r[0]).code, r[1]/res.M)
        txt += '</table>'
        table_row.add( td( literal(txt) ))
    table_body.add( table_row )

    fso_dir = get_fso_temp_dir(request.user.login)
    table_row = tr( td('Data file') )
    for l in labels:
        res = results[l]
        data_file = 'moi-%s.txt' % l.replace('|','_').replace('/','_').replace(' ', '_')
        data_path = fso_dir.abspath + '/' + data_file
        outstream = open(data_path, 'w')
        outstream.write('SAMPLE_ID\tSAMPLE\tMOI\tMLOCI\n')
        for t in res.sample_dist.itertuples():
            (sample_id, moi_number, mloci_number) = t
            sample_code = dbh.get_sample_by_id(sample_id).code
            outstream.write('%d\t%s\t%d\t%d\n' %
                (sample_id, sample_code, moi_number, mloci_number))
        outstream.close()
        #res.sample_dist.to_csv(data_path)
        table_row.add( td(
            literal('<a href="%s">%s</a>' % (fso.get_urlpath(data_path), data_file)) )
        )
    table_body.add( table_row )

    # construct full table
    cerr('constructing table')
    moi_table = table(class_='table table-condensed table-striped')[
        table_header, table_body
    ]

    html.add( moi_table )

    return (html, '')



