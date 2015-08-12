import logging

log = logging.getLogger(__name__)

from genaf.views import *


@roles( PUBLIC )
def index(request):
    
    dbh = get_dbhandler()

    locations = dbh.get_locations()

    return render_to_response("genaf:templates/location/index.mako",
            {   'locations': locations,
            }, request = request)


@roles( PUBLIC )
def view(request):
    pass

@roles( PUBLIC )
def edit(request):
    pass

@roles( PUBLIC )
def save(request):
    pass

@roles( PUBLIC )
def action(request):
    pass
