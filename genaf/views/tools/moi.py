
from genaf.views.tools import *

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Multiplicity of Infection (MoI) Summary',
            'Calculate MoI', callback = func_callback )


def func_callback( query, request ):

    from fatools.lib.analytics.moi import summarize_moi

    analytical_sets = query.get_filtered_analytical_sets()

    options = None
    results = summarize_moi(analytical_sets)

    html, code = format_output(results, request, options)

    return render_to_response("genaf:templates/tools/report.mako",
        {   'header_text': 'Multiplicity of Infection (MoI) Summary',
            'html': html,
            'code': code,
        }, request = request )


def format_output(results, request, options):
    pass