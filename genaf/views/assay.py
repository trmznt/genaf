import logging

log = logging.getLogger(__name__)

from genaf.views import *

from fatools.lib.fautil.wavelen2rgb import wavelen2rgb
from fatools.lib.const import peaktype

import json


@roles( PUBLIC )
def index(request):

    batch_id = request.params.get('batch_id',None)
    if not batch_id:
        return error_page(request, 'ERR - required batch id')

    dbh = get_dbhandler()
    batch = dbh.get_batch_by_id(batch_id)

    assays = dbh.Assay.query(dbh.session()).join(dbh.Sample).filter(dbh.Sample.batch_id == batch.id)

    data = [ [  '<a href="%s">%s</a>' % (request.route_url('genaf.assay-view',
                                                id = a.id),
                                        a.filename),
                '<a href="%s">%s</a>' % (request.route_url('genaf.sample-view',
                                                id = a.sample.id),
                                        a.sample.code),
                a.panel.code,
                '%3.2f' % a.score, '%5.2f' % a.rss, a.process_time]
            for a in assays ]

    return render_to_response( 'genaf:templates/assay/index.mako',
            { 'dataset': json.dumps(data),
            }, request = request )


@roles( PUBLIC )
def view(request):

    assay_id = int(request.matchdict.get('id', -1))

    if not assay_id > 0:
        return error_page(request, 'ERR 101: invalid command!')

    dbh = get_dbhandler()
    assay = dbh.get_assay_by_id( assay_id )

    if not assay:
        return error_page(request, "Invalid command!")

    #if not assay.is_authorized( request.userinstance().groups ):
    #    return not_authorized()

    sample = assay.sample
    batch = sample.batch
    assay_info = div(class_='form-horizontal input-group-sm')[ fieldset()[
        input_text('genaf-fsa_batch', 'Batch',
            value = a( batch.code,
                    href=request.route_url('genaf.batch-view', id=batch.id)),
            static=True),
        input_text('genaf-fsa_sample', 'Sample',
            value = a( sample.code,
                    href=request.route_url('genaf.sample-view', id=sample.id)),
            static=True),
        input_text('genaf-fsa_filename', 'Filename', value=assay.filename,
            static=True),
        input_text('genaf-fsa_ladder', 'Ladder', value=assay.size_standard,
            static=True),
        input_text('genaf-fsa_score', 'Score', value=assay.score, static=True),
        input_text('genaf-fsa_rss', 'RSS', value=assay.rss, static=True),
    ]]

    allele_table, allele_table_js = assay_allele_table(assay, request)

    return render_to_response( 'genaf:templates/assay/view.mako',
            {   'assay': assay,
                'assay_info': assay_info,
                'allele_table': allele_table,
                'code': allele_table_js,
            }, request = request )


@roles( PUBLIC )
def edit(request):

    if request.GET:

        # show form
        pass

    elif request.POST:

        # save to database
        pass

    else:
        return error_page('ERR - invalid command')


@roles( PUBLIC )
def save(request):
    raise NotImplementedError('PROG/ERR - not a valid function')


@roles( PUBLIC )
def action(request):
    if request.POST:
        return action_post(request)

    return action_get(request)


def action_get(request):

    method = request.GET.get('_method', None)
    dbh = get_dbhandler()

    if method == 'edit_allele':

        from genaf.views.allele import edit_form as allele_edit_form

        allele_id = request.GET.get('id')
        allele = dbh.Allele.get(allele_id, dbh.session())

        eform = allele_edit_form(allele, dbh, request)
        body = div( class_='row')[
            div(class_='col-md-12')[
                h3('Edit Allele'),
                eform
            ]
        ]

        return Response(body=str(body), content_type='text/html')

    elif method == 'process_fsa':

        from fatools.lib.params import Params

        parameters = Params()
        assay_id = request.GET.get('id')
        assay = dbh.Assay.get(assay_id, dbh.session())

        eform = assay_process_form(assay, dbh, request, parameters)
        body = div( class_='row')[
            div(class_ = 'col-md-12')[
                h3('Process FSA'),
                p('The FSA processing involves scanning for peaks, '
                    'preannotating the peaks, aligning peaks to ladder peaks, '
                    'calling and binning the peaks '
                    'and finally post-annotating the peaks.'),
                p('The process may take approximately 1 to 5 minutes, depending on '
                    'how clean or how noisy the trace is.'),
                eform
            ]
        ]

        return Response(body=str(body), content_type='text/html')

    raise RuntimeError('Unknown GET method: %s' % method)


def action_post(request):

    method = request.POST.get('_method', None)
    dbh = get_dbhandler()

    if method == 'update_allele':

        from genaf.views.allele import parse_form as allele_parse_form

        allele_d = allele_parse_form(request.POST)

        db_allele = dbh.get_allele_by_id(allele_d['id'])

        # XXX: check authorization here !!

        db_allele.update(allele_d)

        request.session.flash(
            ('success', 'Successfully updating allele %s for marker %s.'
                % (str(db_allele.bin), db_allele.alleleset.marker.label))
        )

        return HTTPFound( location = request.route_url('genaf.assay-view',
                    id = db_allele.alleleset.channel.assay.id) )

        #return render_to_response( 'genaf:templates/allele/edit_form.mako',
        #    { 'allele': allele }, request = request )

    elif method == 'process_fsa':

        assay_id = int(request.POST.get('genaf-assay_id', 0))
        assay = dbh.Assay.get(assay_id, dbh.session()) if assay_id else None

        if not assay:
            return error_page('Cannot find assay with id: %d' % assay_id)

        from fatools.lib.params import Params
        params = Params()

        # parse parameter
        params.nonladder.stutter_ratio = float(
                    request.POST.get('genaf-assay_stutter_ratio'))
        params.nonladder.stutter_range = float(
                    request.POST.get('genaf-assay_stutter_range'))
        params.nonladder.expected_peak_number = float(
                    request.POST.get('genaf-assay_expected_ladder_peak_number'))

        # start processing FSA

        assay.clear()
        assay.scan( params )
        dbh.session().flush()
        assay.preannotate( params )
        retval = assay.alignladder( excluded_peaks = None )
        (dpscore, rss, peaks_no, ladders_no, qcscore, remarks, method) = retval
        dbh.session().flush()
        assay.call( params )
        assay.bin( params )
        assay.postannotate( params )

        request.session.flash(
            ('success', 'Successfully processing FSA file %s with score: %3.2f '
                'RSS: %5.2f and %d ladder peaks.'
                % (assay.filename, qcscore, rss, peaks_no)
            )
        )

        return HTTPFound( location = request.route_url('genaf.assay-view',
                    id = assay.id) )


    raise RuntimeError('Unknown method: %s' % method)


@roles( PUBLIC )
def drawchannels(request):

    assay_id = request.matchdict.get('id')

    dbh = get_dbhandler()
    assay = dbh.get_assay_by_id( assay_id )
    if not assay:
        return error_page()

    datasets = {}
    for c in assay.channels:
        #downsample = decimate( c.raw_data, 3 )
        downsample = c.data
        rgb = wavelen2rgb( c.wavelen, 255 )
        datasets[c.dye] = { "data": [ [x,int(downsample[x])] for x in range(len(downsample)) ],
                            "label": "%s / %s" % (c.dye, c.marker.code),
                            "anchor": "#C-%d" % c.id,
                            "color": "rgb(%d,%d,%d)" % tuple(rgb) }

    return render_to_response( 'genaf:templates/assay/drawchannels.mako',
                { 'datasets': json.dumps( datasets ) }, request = request )


def assay_process_form(assay, dbh, request, params):

    eform = form( name='genaf/assay', method=POST,
                    action=request.route_url('genaf.assay-action') )
    eform.add(
        fieldset(
            input_hidden(name='genaf-assay_id', value=assay.id),
            #input_show('genaf-allele_marker', 'Marker', value=allele.alleleset.marker.label),
            #input_show('genaf-allele_size', 'Size', value=allele.size),
            #input_show('genaf-allele_rtime', 'Retention time', value=allele.rtime),
            #input_show('genaf-allele_height', 'Height', value=allele.height),
            input_text('genaf-assay_stutter_ratio', 'Stutter Ratio',
                    value = params.nonladder.stutter_ratio),
            input_text('genaf-assay_stutter_range', 'Stutter Range',
                    value = params.nonladder.stutter_range),
            input_text('genaf-assay_expected_ladder_peak_number', 'Expected Peak Number',
                    value = params.nonladder.expected_peak_number),
            submit_bar('Process FSA', 'process_fsa')
        )
    )

    return eform


def assay_allele_table(assay, request):

    html = div()
    guest = request.user.has_roles(GUEST)

    # create placeholder for tables

    holder = div(class_='row', id='table-holder', style="height:300px;overflow-y:auto;position-relative;",
        #** { 'data-spy':"scroll", 'data-target': "#navbar-alleles" }
    )

    # create table here

    table_area = div(class_='col-md-12')

    jscode = ''

    for c in assay.channels:
        #table_area.add(
        #    h4("%s | %s" % (c.dye, c.marker.code), id='C-%d' % c.id)
        #)
        allele_table = table(class_='table table-striped table-condensed', id='T-%d' % c.id)[
            thead(
                tr( th( b("%s | %s" % (c.dye, c.marker.code), id='C-%d' % c.id), colspan=9 ) ),
                tr(
                    th('Allele'),
                    th('Size'),
                    th('RTime'),
                    th('Height'),
                    th('Area'),
                    th('Boundary'),
                    th('Beta'),
                    th('Type'),
                    th('')
                ),
                style="background-color: #fff;"
            )
        ]
        kwargs = { 'data-toggle':'modal', 'data-target':'#allele-modal-view', 'data-remote': 'false' }
        body = tbody()
        for al in sorted(c.get_latest_alleleset().alleles, key=lambda x: x.rtime):
            if guest and al.type != peaktype.bin:
                continue
            body.add(
                tr(
                    td(al.bin),
                    td('%03.2f' % al.size),
                    td('%05d' % al.rtime),
                    td('%05d' % al.height),
                    td('%06.1f' % al.area),
                    td('%05d - %05d' % (al.brtime, al.ertime)),
                    td('%02.3f' % al.beta),
                    td(al.type),
                    td(
                        a('Edit',
                            href=request.route_url('genaf.assay-action',
                                    _query=dict(_method='edit_allele', id=al.id)),
                            **kwargs )
                        if not guest else ''
                    ),
                    id='a-%d' % al.id
                )
            )
        allele_table.add( body )
        table_area.add( allele_table )
        jscode += "$('#T-%d').stickyTableHeaders({scrollableArea: $('#table-holder')});\n" % c.id
    holder.add( table_area )

    html.add( holder )

    return html, jscode
    # + "$('#table-holder').scrollspy({target:'#navbar-alleles'});"
    #"$('table').stickyTableHeaders({scrollableArea: $('#table-holder')});"

