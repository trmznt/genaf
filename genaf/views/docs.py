
from genaf.views import *
from rhombus.views import fso
from pyramid.response import FileResponse

import os

def formatter( abspath, request ):

    basepath, ext = os.path.splitext( abspath )

    if ext == '.rst':
        # restructuredtext
        with open(abspath) as f:
            text = f.read()
            content = fso.render_rst( text )

            return render_to_response('rhombus:templates/generics/page.mako',
                { 'content': content },
                request = request)

    elif ext == '.md':
        # markdown
        raise NotImplementedError

    else:
        # don't know the format, just throw the file
        return FileResponse( abspath )
