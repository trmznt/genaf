import logging

log = logging.getLogger(__name__)

from genaf.views import *
import json


@roles( PUBLIC )
def index(request):

    dbh = get_dbhandler()

    markers = dbh.get_markers()

    return render_to_response( "genaf:templates/marker/index.mako",
                { 'markers': markers },
                request = request )


@roles( PUBLIC )
def view(request):

    marker_id = int(request.matchdict.get('id'))
    if marker_id <= 0:
        return error_page('Please provide marker ID')

    dbh = get_dbhandler()

    marker = dbh.get_marker_by_id(marker_id)
    if not marker:
        return error_page('Marker with ID: %s does not exist!' % marker_id)

    return render_to_response( "genaf:templates/marker/view.mako",
            { 'marker': marker }, request = request )



@roles( SYSADM, DATAADM )
def edit(request):

    #check permisson
    if not request.user.in_group(('_SysAdm_', None)):
        return error_page(request, 'Current user is not part of Administrator')

    marker_id = int(request.matchdict.get('id'))
    if marker_id < 0:
        return error_page(request, 'Please provide marker ID')

    dbh = get_dbhandler()

    if request.method == 'GET':
        # return a form

        if marker_id == 0:
            marker = dbh.new_marker()
            marker.id = 0
            marker.species = 'X'

        else:
            marker = dbh.get_marker_by_id(marker_id)
            if not marker:
                return error_page(request,
                    'Marker with ID: %s does not exist!' % marker_id)

        form = edit_form(marker, dbh, request)

        return render_to_response( "genaf:templates/marker/edit.mako",
            {   'marker': marker,
                'form': form,
            }, request = request )


    elif request.method == 'POST':

        marker = parse_form(request.POST, dbh.new_marker())
        if marker.id != marker_id:
            return error_page(request, "Inconsistent data!")

        try:

            if marker_id == 0:
                # create new marker
                dbh.session().add( marker )
                dbh.session().flush()
                db_marker = marker
                request.session.flash(
                    (   'success',
                        'Marker [%s] has been added' % db_marker.label )
                )

            else:

                db_marker = dbh.get_marker_by_id( marker.id )
                db_marker.update( marker )
                dbh.session().flush()
                request.session.flash(
                    (   'success',
                        'Marker [%s] has been updated' % db_marker.label )
                )
        except RuntimeError as err:
            return error_page(request, str(err))
        except:
            raise

        return HTTPFound(location = request.route_url('genaf.marker-view',
                                        id = db_marker.id))

    return error_page(request, "Unknown HTTP method!")


@roles( PUBLIC )
def save(request):

    if not request.user.has_roles( PUBLIC ):
        return not_authorized()

    if not request.POST:
        return error_page("Need a POST form submission")

    dbh = get_dbhandler()

    marker_id = int(request.matchdict.get('id'))
    marker = parse_form(request.POST, dbh.new_marker())


    if marker_id != marker.id:
        return error_page()

    if marker.id == 0:

        marker.id = None
        dbs = dbh.session()
        dbs.add( marker )
        dbs.flush()
        db_marker = marker
        request.session.flash(
            (   'success',
                'Marker [%s] has been added' % db_marker.label ))

    else:

        db_marker = dbh.get_marker_by_id( marker_id )
        db_marker.update( marker )
        request.session.flash(
            (   'success',
                'Marker [%s] has been updated' % db_marker.label ))

    return HTTPFound(location = request.route_url('genaf.marker-view', id = db_marker.id))



def edit_form(marker=None, dbh=None, request=None):


    eform = form( name="genaf/marker", method=POST,
                action = request.route_url('genaf.marker-edit',
                    id=marker.id if marker else 0) )
    eform.add(
        fieldset(
            input_hidden(name="genaf/marker.id", value = marker.id if marker else 0),
            input_text( name="genaf/marker.code", label="Marker code",
                                    value = marker.code if marker else '' ),
            input_text( name="genaf/marker.locus", label="Locus",
                                    value = marker.locus if marker else ''),
            input_text( name="genaf/marker.species", label="Species",
                                    value = marker.species if marker else ''),
            input_text( name='genaf/marker.repeats', label='Repeats',
                                    value = marker.repeats if marker else ''),
            input_text( name='genaf/marker.min_size', label='Min size',
                                    value = marker.min_size if marker else ''),
            input_text( name="genaf/marker.max_size", label='Max size',
                                    value = marker.max_size if marker else ''),
            submit_bar(),
        )
    )

    return eform

def parse_form( d, m ):

    m.id = int(d.get('genaf/marker.id', 0))
    m.code = d.get('genaf/marker.code')
    m.locus = d.get('genaf/marker.locus')
    m.species = d.get('genaf/marker.species')
    m.repeats = int(d.get('genaf/marker.repeats') or 0)
    m.min_size = int(d.get('genaf/marker.min_size') or 0)
    m.max_size = int(d.get('genaf/marker.max_size') or 0)

    return m



def action(request):
    pass


def lookup(request):
    pass
