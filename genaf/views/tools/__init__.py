
from genaf.views import *
from genaf.lib.query import Query, load_params, load_yaml

from rhombus.lib import fsoverlay

TEMP_ROOTDIR = 'analyses'

def get_fso_temp_dir(userid, rootdir = TEMP_ROOTDIR):
    """ return a fileoverlay object on temporary directory
    """

    fso_dir = fsoverlay.mkranddir(rootdir, userid)
    return fso_dir


def basic_query_form(request):

    dbh = get_dbhandler()

    qform = form(name='queryform', action='#')

    # samples
    batches = list( dbh.get_batches(groups = request.user.groups) )
    qform.add(
        fieldset(name='simple_query')[
            input_select(name='batch_ids', label='Batch code(s)', multiple = True,
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
            input_select(name='marker_ids', label='Marker(s)', multiple = True,
                    options = [ (m.id, m.label) for m in markers ],
                    extra_control = '<a id="markers_clear">Clear</a>'),
        ]
    )

    # allele & marker filtering
    qform.add(
        fieldset(name='filter_fields')[
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
        fieldset(name='differentiation_fields')[

            input_select(name='sample_option', label='Sample option', value='AP',
                    options = [ ('AA', 'All available samples'),
                                ('AS', 'Strict samples'),
                                ('PS', 'Strict samples for each differentiation '),
                                ('AU', 'Unique samples'),
                                ('PU', 'Unique samples for each differentiation'), ]
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


def jscode(request):

    return '\n'.join([
            "$('#batch_ids').select2();",
            "$('#marker_ids').select2();",
            "$('#markers_clear').on('click', function() { $('#marker_ids').val(null).trigger('change'); });",
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

        queryform, javacode = create_form( request )

        return render_to_response('genaf:templates/tools/index.mako',
            {   'header_text': header_text,
                'queryform': queryform,
                'code': javacode,
                'yamlform': yaml_query_form(request),
            }, request = request)

    # process request
    if request.GET.get('_method', None) == '_exec':
        params = load_params(form2dict( request ))

    elif request.GET.get('_method', None) == '_yamlexec':
        params = load_yaml( request.params.get('yamlquery') )

    q = Query( params, get_dbhandler() )

    return callback(q, request)



def create_form( request ):
    """ return the form and javascript code """
    return _FORM_FACTORY_(request)


def set_form_factory( factory_func ):
    """ factory_func needs to return a tuple of (form, jscode) """
    global _FORM_FACTORY_
    _FORM_FACTORY_ = factory_func

def genaf_form_factory( request ):
    return ( basic_query_form(request), jscode(request) )

_FORM_FACTORY_ = genaf_form_factory


def form2dict( request ):
    d = {}
    p = request.params

    if p.get('queryset', None):
        query_text = p.get('queryset')
        if '$' in query_text:
            raise RuntimeError('ERR - sample differentiation is not supported yet')
        else:
            selector_d = { 'all': [ {'query': p.get('queryset') } ] }

    elif p.getall('batch_ids'):
        selector_d = { 'all': [] }
        batch_ids = p.getall('batch_ids')
        for batch_id in batch_ids:
            selector_d['all'].append( { 'batch_id': int(batch_id) })
    else:
        raise RuntimeError('WHOA, need to have either batch code(s) or queryset')

    filter_d = {}
    filter_d['marker_ids'] = [ int(x) for x in p.getall('marker_ids') ]
    filter_d['abs_threshold'] = int(p.get('allele_abs_treshhold'))
    filter_d['rel_threshold'] = float( p.get('allele_rel_threshold'))
    filter_d['rel_cutoff'] = float( p.get('allele_rel_cutoff'))
    filter_d['sample_qual_threshold'] = float( p.get('sample_qual_threshold'))
    filter_d['marker_qual_threshold'] = float( p.get('marker_qual_threshold'))
    filter_d['sample_option'] = p.get('sample_option')

    d['selector'] = selector_d
    d['filter'] = filter_d

    d['differentiator'] = {}

    return d
        


