import logging

log = logging.getLogger(__name__)

from rhombus.lib.utils import cerr, cout
from rhombus.views.generics import error_page

from genaf.views import *

import json
import sqlalchemy.exc, transaction


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

    mode = request.params.get('mode','fsa')

    if mode == 'meta':
        html, jscode = format_sampleinfo(samples, request)
    elif mode == 'fsa':
        html, jscode = format_samplefsa(samples, request)
    else:
        return error_page(request, 'No suitable mode provided!')

    return render_to_response("genaf:templates/sample/index.mako",
                    {   'samples': samples,
                        'batch': batch,
                        'html': html,
                        'code': jscode,
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

@roles( PUBLIC )
def edit(request):
    """ editing sample metadata """

    sample_id = int(request.matchdict.get('id'))
    if sample_id < 0:
        return error_page(request, 'Please provide valid sample ID')

    dbh = get_dbhandler()

    if request.method == 'GET':
        sample = dbh.get_sample_by_id( sample_id )

        batch = sample.batch

        # XXX: check authorization here: whether current user belongs to batch owner group
        if not request.user.in_group( batch.group ):
            return error_page(request, 'User is not a member of batch: %s' % batch.code)


        # prepare form

        eform = edit_form(sample, dbh, request)

        return render_to_response("genaf:templates/sample/edit.mako",
                    {   'sample': sample,
                        'eform': eform,
                    },
                    request = request)

    elif request.method == 'POST':

        sample_d = parse_form( request.POST )
        if sample_d['id'] != sample_id:
            return error_page(request, 'Inconsistent sample ID!')

        try:
            if sample_id == 0:

                pass

            else:

                sample = dbh.get_sample_by_id( sample_id )
                batch = sample.batch

                # authorisation: current user must belongs to batch owner group
                if not request.user.in_group( batch.group ):
                    return error_page(request,
                        'User is not a member of batch: %s' % batch.code)

                sample.update(sample_d)
                dbh.session().flush()
                request.session.flash(
                    (   'success',
                        'Sample [%s] has been updated.' % sample.code )
                )


        except RuntimeError as err:
            return error_Page(request, str(err))

        except sqlalchemy.exc.IntegrityError as err:
            dbh.session().rollback()
            detail = err.args[0]
            if not sample.id: sample.id = sample_id
            editform = edit_form(sample, dbh, request)
            if 'DETAIL' in detail:
                if 'code, batch_id' in detail:
                    editform.get('genaf-sample_code').add_error('The sample code: %s is '
                        'already being used. Please use other sample code!'
                        % sample_d['code'])
                r = render_to_response( "genaf:templates/sample/edit.mako",
                    {   'sample': None,
                        'eform': editform,
                    },
                    request = request )
                transaction.abort()
                return r
            return error_page(request, str(err))


        return HTTPFound(location = request.route_url('genaf.sample-view', id = sample.id))


    return error_page(request, 'Invalid method!')


def edit_form(sample, dbh, request):

    eform = form( name='genaf/sample', method=POST,
                action=request.route_url('genaf.sample-edit', id=sample.id))
    eform.add(
        fieldset(
            input_hidden(name='genaf-sample_id', value=sample.id),
            input_show('genaf-sample_batch', 'Batch', value=sample.batch.code),
            input_text('genaf-sample_code', 'Code', value=sample.code),
            input_text('genaf-sample_type', 'Type', value=sample.type),

            submit_bar(),
        )
    )

    return eform


def parse_form(f):

    d = dict()
    d['id'] = int( f['genaf-sample_id'] )
    d['code'] = f['genaf-sample_code']
    d['type'] = f['genaf-sample_type']

    return d


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


def format_samplefsa(samples, request):

    T = table(class_='table table-condensed table-striped', id='sample_table')

    data = [
        [   '<a href="%s">%s</a>' % (request.route_url('genaf.sample-view',
                                                id = s.id),
                                    s.code),
            s.batch.code,
            s.assays.count()
        ] for s in samples
    ]

    jscode = '''
var dataset = %s;

$(document).ready(function() {
    $('#sample_table').DataTable( {
        data: dataset,
        paging: false,
        fixedHeader: true,
        columns: [
            { title: "Sample Code" },
            { title: "Batch" },
            { title: "FSA counts" }
        ]
    } );
} );
''' % json.dumps( data )

    return (str(T), jscode)


def format_sampleinfo(samples, request):

    T = table(class_='table table-condensed table-striped', id='sample_table')

    data = [
        [   '<a href="%s">%s</a>' % (request.route_url('genaf.sample-view',
                                                id = s.id),
                                    s.code),
            s.altcode,
            s.category,
            s.location.country,
            s.location.level1,
            s.location.level2,
            s.location.level3,
            s.location.level4,
            str(s.collection_date)
        ] for s in samples
    ]

    jscode = '''
var dataset = %s;

$(document).ready(function() {
    $('#sample_table').DataTable( {
        data: dataset,
        paging: false,
        fixedHeader: true,
        columns: [
            { title: "Sample Code" },
            { title: "Alt Code" },
            { title: "Category" },
            { title: "Country" },
            { title: "Admin L1" },
            { title: "Admin L2" },
            { title: "Admin L3" },
            { title: "Admin L4" },
            { title: "Collection Date" }
        ]
    } );
} );
''' % json.dumps( data )

    return ( str(T), jscode )
