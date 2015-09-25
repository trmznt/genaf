
from genaf.views import *


def basic_query_form(request):

    dbh = get_dbhandler()

    qform = form(name='queryform', action='#')

    # samples
    batches = list( dbh.get_batches(groups = request.user.groups) )
    qform.add(
        fieldset(name='simple_query')[
            input_select(name='batches', label='Batch code(s)', multiple = True,
                    options = [ (b.id, b.code) for b in batches ],
                    extra_control = '<a id="show_syntax_query">Use query set</a>'),
        ],
        fieldset(name='syntax_query', style="display: none;")[
            input_textarea(name='queryset', label='Query set', disabled='disabled',
                    extra_control = '<a id="show_simple_query">Use query form</a>'),
        ]
    )

    # markers
    markers = list( dbh.get_markers() )
    markers.sort( key = lambda x: x.label )
    qform.add(
        fieldset()[
            input_select(name='markers', label='Marker(s)', multiple = True,
                    options = [ (m.id, m.label) for m in markers ],
                    extra_control = '<a id="markers_clear">Clear</a>'),
        ]
    )

    # allele & marker filtering
    qform.add(
        fieldset()[
            input_text(name='allele_abs_treshhold', label='Allele absolute threshold',
                        value=100, size=2,
                        info = "The minimum absolute rfu value for each peak to be considered as a real peak"),
            input_text(name='allele_rel_threshold', label='Allele relative threshold',
                        value=0.33, size=2),
            input_text(name='allele_rel_cutoff', label='Allele relative cutoff',
                        value=0.00, size=2),
            input_text(name='sample_qual_threshold', label='Sample quality threshold',
                        value=0.50, size=2),
            input_text(name='marker_qual_threshold', label='Marker quality threshold',
                        value=0.10, size=2)
        ]
    )

    qform.add(
        fieldset()[

            input_select(name='sample_option', label='Sample option', value='AP',
                    options = [ ('AA', 'All available samples'),
                                ('AP', 'All population (day-0) samples'),
                                ('AS', 'Strict population samples'),
                                ('PS', 'Strict population samples for each differentiation '),
                                ('AU', 'Unique population samples'),
                                ('PU', 'Unique population samples for each differentiation'),
                                ('NP', 'All non-population (e.g. recurrent) samples') ]
                    ),
            input_select(name='spatial_differentiation', label='Spatial differentiation', value=-1,
                    options = [ (-1, 'No spatial differentiation'),
                                (0, 'Country level'),
                                (1, '1st Administration level'),
                                (2, '2nd Administration level'),
                                (3, '3rd Administration level'),
                                (4, '4th Administration level') ]
                    ),
            input_select(name='temporal_differentiation', label='Temporal differentiation', value=0,
                    options = [ (0, 'No temporal differentiation'),
                                (1, 'Yearly'),
                                (2, 'Quaterly')]
                    ),
        ]
    )

    qform.add(
        fieldset()[ submit_bar('Execute', '_exec') ]
    )

    return qform


def jscode():

    return '\n'.join([
            "$('#batches').select2();",
            "$('#markers').select2();",
            "$('#markers_clear').on('click', function() { $('#markers').val(null).trigger('change'); });",
            "$('#show_syntax_query').on('click', function() {"
                "$('#syntax_query').show(); $('#queryset').prop('disabled', false); "
                "$('#simple_query').hide(); });",
            "$('#show_simple_query').on('click', function() {"
                "$('#syntax_query').hide(); $('#queryset').prop('disabled', true); "
                "$('#simple_query').show(); });",

        ])

def yaml_query_form(request):

    yform = form(name='yamlform', action='#')
    yform.add(
        fieldset()[
            input_textarea(name="yamlquery", label='YAML query', size='8x8'),
        ]
    )

    yform.add(
        fieldset()[ submit_bar('Execute', '_yamlexec')]
    )

    return yform



def process_request( request, header_text, button_text, callback ):

    if not request.GET.get('_method', None) in ['_exec', '_yamlexec']:

        return render_to_response('genaf:templates/tools/index.mako',
            {   'header_text': header_text,
                'queryform': basic_query_form(request),
                'code': jscode(),
                'yamlform': yaml_query_form(request),
            }, request = request)


        
