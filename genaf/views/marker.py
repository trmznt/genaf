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



@roles( PUBLIC )
def edit(request):

    marker_id = int(request.matchdict.get('id'))
    if marker_id < 0:
        return error_page('Please provide marker ID')

    dbh = get_dbhandler()

    if marker_id == 0:
        marker = dbh.new_marker()
        marker.id = 0
        marker.species = 'X'

    else:
        marker = dbh.get_marker_by_id(marker_id)
        if not marker:
            return error_page('Marker with ID: %s does not exist!' % marker_id)

    form = edit_form(marker)

    return render_to_response( "genaf:templates/marker/edit.mako",
            {   'marker': marker,
                'form': form,
            }, request = request )



    return form
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
            (   'sucess',
                'Marker [%s] has been updated' % db_marker.label ))

    return HTTPFound(location = request.route_url('genaf.marker-view', id = db_marker.id))



def edit_form(marker=None):

    from rhombus.lib import tags

    form = tags.form( name="genaf/marker", action="/", method=tags.POST )
    form.add( tags.input_hidden(name="genaf/marker.id", value = marker.id if marker else 0) )
    form.add( tags.input_text( name="genaf/marker.code", label="Marker code",
                                    value = marker.code if marker else '' ) )
    form.add( tags.input_text( name="genaf/marker.species", label="Species",
                                    value = marker.species if marker else '') )
    form.add( tags.input_textarea( name="genaf/marker.bins", label="Bins",
                                    value = marker.bins if marker else '') )

    return form

def parse_form( d, m ):

    m.id = int(d.get('genaf/marker.id', 0))
    m.code = d.get('genaf/marker.code')
    m.locus = d.get('genaf/marker.locus')
    m.species = d.get('genaf/marker.species')
    m.repeats = int(d.get('genaf/marker.repeats') or 0)
    m.min_size = int(d.get('genaf/marker.min_size') or 0)
    m.max_size = int(d.get('genaf/marker.max_size') or 0)
    m.bins = json.loads(d.get('genaf/marker.bins') or '[]')

    return m



def action(request):
    pass


def lookup(request):
    pass
