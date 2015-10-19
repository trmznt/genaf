import logging

log = logging.getLogger(__name__)

from genaf.views import *

from fatools.lib.fautil.wavelen2rgb import wavelen2rgb

import json


@roles( PUBLIC )
def index(request):
    
    batch_id = request.params.get('batch_id',None)
    if not batch_id:
        return error_page('ERR - required batch id')

    dbh = get_dbhandler()
    batch = dbh.get_batch_by_id(batch_id)

    assays = dbh.Assay.query().join(dbh.Sample).filter(dbh.Sample.batch_id == batch.id)

    data = [ [a.filename, a.sample.code, a.panel.code, a.score, a.rss, a.process_time]
            for a in assays ]

    return render_to_response( 'genaf:templates/assay/index.mako',
            { 'data': json.dumps(data),
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
    pass


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
