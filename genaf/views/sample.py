import logging

log = logging.getLogger(__name__)

from rhombus.lib.utils import cerr, cout
from rhombus.views.generics import error_page

from genaf.views import *


@roles( PUBLIC )
def index(request):

    dbh = get_dbhandler()

    q = dbh.Sample.query(dbh.session()).join(dbh.Batch)

    batch_id = request.params.get('batch_id', False)
    location_id = request.params.get('location_id', False)

    if batch_id:
        batch = dbh.get_batch_by_id( batch_id )
        q = q.filter( dbh.Sample.batch_id == batch.id )
    else:
        batch = None

    if location_id:
        q = q.filter( dbh.Sample.location_id == location_id )

    q = q.order_by( dbh.Sample.code )

    samples = q.all()

    mode = request.params.get('mode','meta')

    if mode == 'meta':
        outtable = format_sampleinfo(samples)
    elif mode == 'fsa':
        outtable = format_samplefsa(samples)

    return render_to_response("genaf:templates/sample/index.mako",
                    {   'samples': samples,
                        'batch': batch,
                        'table': outtable
                    },
                    request = request)

@roles( PUBLIC )
def view(request):

    sample_id = int(request.matchdict.get('id'))
    sample = get_dbhandler().get_sample_by_id( sample_id )
    #if sample.batch.group_id not in request.user.groups:
    #    return not_authorized()

    return render_to_response("genaf:templates/sample/view.mako",
                    {   'sample': sample,
                        'allele_list': [],
                    },
                    request = request)


def edit(request):

    return render_to_response("genaf:templates/sample/edit.mako",
                    {   'sample': sample,
                    },
                    request = request)


def save(request):

    pass

@roles( PUBLIC )
def action(request):

    method = request.params.get('_method', None)

    if method == 'add-assay-files':

        if not request.POST:
            return error_page(request, 'Only accept POST request!')

        sample_id = request.POST.get('sample_id')
        sample = get_dbhandler().get_sample_by_id( sample_id )

        request.session.flash(
            (   'success',
                'Sample code [%s] has been added with %d assay files' % ( sample.code,
                            len(request.params.getall('genaf-assay_file')) )))

        return HTTPFound(location = request.route_url('genaf.sample-view', id=sample.id))

    else:
        return error_page(request, 'Unknown method!')

def lookup(request):
    pass


def format_samplefsa_table(samples):
    pass

def format_sampleinfo(samples):

    T = table(class_='table table-condensed table-striped', id='sample_table')

    data = [
        [   '<a href="%s">%s</a>' % (request.route_url('genaf.sample-view',
                                                id = s.id),
                                    s.code),
            s.altcode,
            s.category,
            s.location.country,
            s.location.adminl1,
            s.location.adminl2,
            s.location.adminl3,
            s.location.adminl4,
            s.collection_date
        ] for s in samples
    ]

    jscode = ''

