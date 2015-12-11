import logging

log = logging.getLogger(__name__)

from genaf.views import *

from fatools.lib.fautil.wavelen2rgb import wavelen2rgb

import json


@roles( PUBLIC )
def index(request):

    batch_id = request.params.get('batch_id',None)
    if not batch_id:
        return error_page(request, 'ERR - required batch id')

    dbh = get_dbhandler()
    batch = dbh.get_batch_by_id(batch_id)

    assays = dbh.Assay.query().join(dbh.Sample).filter(dbh.Sample.batch_id == batch.id)

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


    return render_to_response( 'genaf:templates/assay/view.mako',
            {   'assay': assay,
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

    if method == 'edit_allele':

        from genaf.views.allele import edit_form as allele_edit_form

        allele_id = request.GET.get('id')
        dbh = get_dbhandler()
        allele = dbh.Allele.get(allele_id)

        eform = allele_edit_form(allele, dbh, request)

        return Response(body=str(eform), content_type='text/html')

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
                            "color": "rgb(%d,%d,%d)" % tuple(rgb) }

    return render_to_response( 'genaf:templates/assay/drawchannels.mako',
                { 'datasets': json.dumps( datasets ) }, request = request )
