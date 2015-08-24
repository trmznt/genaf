import logging

log = logging.getLogger(__name__)

from genaf.views import *


@roles( PUBLIC )
def index(request):
    
    batch_id = request.params.get('batch_id',None)
    if not batch_id:
        return error_page('ERR - required batch id')


@roles( PUBLIC )
def view(request):
    pass

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
