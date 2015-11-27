
from genaf.views import *

@roles(PUBLIC)
def index(request):

    return render_to_response("genaf:templates/tools/help.mako",
            {
            }, request = request )