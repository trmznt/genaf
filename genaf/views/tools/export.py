
from genaf.views.tools import *

@roles(PUBLIC)
def index(request):

    return process_request( request, 'Data Export Tools', 'Export data',
            callback = func_callback, form_modifier = func_form_modifier )


def func_callback( query, request ):

    from fatools.lib.analytics.export import export_format

    dbh = get_dbhandler()
    analytical_sets = query.get_filtered_analytical_sets()

    output_format = request.GET.get('export_format')
    export_func = export_format[output_format]

    export_func(analytical_sets, dbh, None, recode=True)
    html, code = format_output(haplo_res, options)

    return render_to_response("genaf:templates/tools/report.mako",
        {   'header_text': 'Genotype Summary',
                'html': html,
                'code': code,
        }, request = request )


def func_form_modifier( eform, jcode):
    eform.get('additional_fields').add(
        input_select(name='export_format', label="Export format",
            value=0,
            options = [
                ('arlequin', 'Arlequin data format (MLGT data)'),
                ('alleledf', 'Allele dataframe'),
                ('moidf', 'Multiplicity of Infection dataframe'),
            ]
        )
    )

    return (eform, jcode)


def format_output( results, options ):

    return '', ''