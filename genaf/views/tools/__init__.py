
from genaf.views import *
from genaf.lib.query import Query, load_params, load_yaml
from genaf.lib.querytext import query2dict
from genaf.lib.configs import get_temp_path, TEMP_TOOLS
from genaf.lib.procmgmt import subproc, getproc

from rhombus.lib import fsoverlay
from rhombus.lib.utils import get_dbhandler_notsafe

from pyramid.settings import asbool

from time import time
import threading, transaction


def get_fso_temp_dir(userid, rootdir = TEMP_TOOLS):
    """ return a fileoverlay object on temporary directory
    """

    absrootdir = get_temp_path('', rootdir)
    fso_dir = fsoverlay.mkranddir(absrootdir, userid)
    return fso_dir


def basic_query_form(request, mode='mlgt'):
    """ mode: mlgt or allele """

    if mode not in ['mlgt', 'allele']:
        return RuntimeError('ERR - basic_query_form mode unknown: %s' % mode)
    #allele_mode = True if mode == 'allele' else False

    # we need all options because of sample genotype filtering (low complexity & unique haplotype)
    allele_mode = True

    dbh = get_dbhandler()

    qform = form(name='queryform', action='#')

    # samples
    if request.user.has_roles(SYSADM, DATAADM):
        batches = list( dbh.get_batches(groups=None) )
    else:
        batches = list( dbh.get_batches(groups = request.user.groups) )

    qform.add(
        fieldset(name='simple_query')[
            input_select(name='batch_ids', label='Batch code(s)', multiple = True,
                    options = [ (b.id, '%s | %s' % (b.code, b.description)) for b in batches ],
                    extra_control = '<a class="show_syntax_query">Use query set</a> | '
                                    '<a class="show_file_query">Use source file</a>'),
        ],
        fieldset(name='syntax_query', style="display: none;")[
            input_textarea(name='queryset', label='Query set', disabled='disabled',
                    extra_control = '<a class="show_simple_query">Use query form</a> | '
                                    '<a class="show_file_query">Use source file</a>'),
        ],
        fieldset(name="file_query", style="display:none;")[
            input_file(name='queryfile', label='Sample source file', disabled='disabled',
                    extra_control = '<a class="show_simple_query">Use query form</a> | '
                                    '<a class="show_syntax_query">Use query set</a>'
                                    )
        ],
        fieldset(name='sample_options')[
            input_select(name='sample_selection', label='Sample selection', value='P',
                    options = [ ('A', 'All available samples'),
                                ('F', 'All field samples'),
                                ('R', 'All reference samples'),
                    ] )
        ],
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
                        info = "popup:/tools/help#allele_abs_threshold"),
            input_text(name='allele_rel_threshold', label='Allele relative threshold',
                        value=0.33, size=2,
                        info = "popup:/tools/help#allele_rel_threshold")
                if allele_mode else '',
            input_text(name='allele_rel_cutoff', label='Allele relative cutoff',
                        value=0.00, size=2,
                        info = "popup:/tools/help#allele_rel_cutoff"),
            input_text(name='sample_qual_threshold', label='Sample quality threshold',
                        value=0.50, size=2,
                        info = "popup:/tools/help#sample_qual_threshold"),
            input_text(name='marker_qual_threshold', label='Marker quality threshold',
                        value=0.10, size=2,
                        info = "popup:/tools/help#marker_qual_threshold"),
            input_text(name='stutter_ratio', label='Stutter ratio',
                        value=0.00, size=2,
                        info = "popup:/tools/help#stutter_ratio")
                if allele_mode else '',
            input_text(name='stutter_range', label='Stutter range',
                        value=0.00, size=2,
                        info = "popup:/tools/help#stutter_range")
                if allele_mode else '',
        ]
    )

    qform.add(
        fieldset(name='differentiation_fields')[

            input_select(name='sample_filtering', label='Sample filtering', value='A',
                    options = [ ('N', 'No futher sample filtering'),
                                ('M', 'Monoclonal samples'),
                                ('S', 'Strict/low-complexity samples'),
                                ('U', 'Unique genotype samples'),
                            ]
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

    qform.add(fieldset(name='additional_fields'))

    qform.add(
        fieldset()[ submit_bar('Execute', '_exec') ]
    )

    return qform


def jscode(request, mode = 'mlgt'):

    return '\n'.join([
            "function template(data, container) { return data.text.split(' ', 1); };",
            "$('#batch_ids').select2({ templateSelection: template });",
            "$('#marker_ids').select2();",
            "$('#markers_clear').on('click', function() { $('#marker_ids').val(null).trigger('change'); });",
            "$('.show_syntax_query').on('click', function() {"
                "$('#syntax_query').show();"
                "$('#queryset').prop('disabled', false);"
                "$('#queryfile').prop('disabled', true);"
                "$('#batch_ids').prop('disabled', true);"
                "$('#file_query').hide();"
                "$('#simple_query').hide(); });",
            "$('.show_simple_query').on('click', function() {"
                "$('#syntax_query').hide();"
                "$('#file_query').hide();"
                "$('#queryset').prop('disabled', true);"
                "$('#queryfile').prop('disabled', true);"
                "$('#batch_ids').prop('disabled', false);"
                "$('#simple_query').show(); });",
            "$('.show_file_query').on('click', function() {"
                "$('#syntax_query').hide();"
                "$('#simple_query').hide();"
                "$('#queryset').prop('disabled', true);"
                "$('#batch_ids').prop('disabled', true);"
                "$('#queryfile').prop('disabled', false);"
                "$('#file_query').show(); });",
            "$('#queryform').submit( function() {"
                "if ( ! $('#marker_ids').val() )"
                    "{ alert('Error: please provide the marker(s)!'); return false; }"
                "if ( ! ( $('#batch_ids').val() || $('#queryset').val() || $('#queryfile').val() ) )"
                    "{ alert('Error: please provide Batch id(s) or query set or sample source file!');"
                    "return false; }"
                "});",

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



def process_request( request, header_text, button_text, callback, format_callback=None,
        mode = 'mlgt', form_modifier = None, stdout=False, stderr=False ):

    global task_ids

    # check whether request have taskid as GET parameter
    taskid = request.GET.get('taskid', None)
    if taskid:

        if taskid not in task_ids:
            return error_page(request, 'task with ID %s is not registered in the system!')

        (procid, login, title, current_route_path, format_callback, path_qs) = task_ids[taskid]

        procunit = getproc(procid)

        if procunit.status in ['D', 'U']:

            result = procunit.result
            if not result and procunit.exc:
                raise procunit.exc

            if format_callback:
                output = format_callback(result, request)
                html = output['html']
                jscode = output['jscode']
                refs = format_refs(output.get('refs', ''))
            else:
                html = result['html']
                jscode = result['jscode']
                refs = format_refs(result.get('refs', ''))

            # dummy
            sample_html, sample_code = result['sample_filtering']
            marker_html, marker_code = result['marker_filtering']

            return render_to_response("genaf:templates/tools/report.mako",
                {   'header_text': result['title'],
                    'sample_report': sample_html,
                    'marker_report': marker_html,
                    'html': html if html is not None else '',
                    'code': sample_code + marker_code + jscode if jscode is not None else '',
                    'path_qs': path_qs,
                    'refs': refs,
                }, request = request )

            clearproc(procid)
            del task_ids[taskid]

        else:
            seconds = 5
            ns = procunit.ns

            return render_to_response('genaf:templates/tools/progress.mako',
                {   'msg': ns.cerr,
                    'title': title,
                    'taskid': taskid,
                    'seconds': seconds,
                }, request = request )


    # prepare form and/or process form

    if not request.GET.get('_method', None) in ['_exec', '_yamlexec']:

        queryform, javacode = create_form( request, mode )

        if form_modifier:
            queryform, javacode = form_modifier(queryform, javacode)

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


    if not asbool(request.registry.settings['genaf.concurrent.analysis']):
        # set this to false for debugging in non-concurrent mode

        result = mp_run_callback(request.registry.settings,
                    callback, params, request.user, mode)

        if format_callback:
            output = format_callback(result, request)
            html = output['html']
            jscode = output['jscode']
            refs = format_refs(output.get('refs', ''))
        else:
            html = result['html']
            jscode = result['jscode']
            refs = format_refs(result.get('refs', ''))


        # dummy
        sample_html, sample_code = result['sample_filtering']
        marker_html, marker_code = result['marker_filtering']

        return render_to_response("genaf:templates/tools/report.mako",
            {   'header_text': result['title'],
                'sample_report': sample_html,
                'marker_report': marker_html,
                'html': html if html is not None else '',
                'code': sample_code + marker_code + jscode if jscode is not None else '',
                'path_qs': request.path_qs,
                'refs': refs,
            }, request = request )

    # this is code for concurrent mode

    with glock:
        procid, msg = subproc( request.user.login, None,
                    mp_run_callback, request.registry.settings, callback, params,
                    request.user, mode )
        task_ids[procid] = ( procid, request.user.login, header_text,
                                request.current_route_path(), format_callback, request.path_qs )

    return HTTPFound(location = request.current_route_path(_query = { 'taskid': procid }))

    raise NotImplementedError()
    ## method stops here

    q = Query( params, get_dbhandler() )

    # callback needs to return (header_text, html, jscode) tuple

    response = callback(q, request)

    if type(response) != tuple:
        return response

    (header_text, html, code) = response

    sample_html, sample_code = format_sample_summary( q.get_sample_summary(mode) )
    marker_html, marker_code = format_marker_summary( q )

    return render_to_response("genaf:templates/tools/report.mako",
            {   'header_text': header_text,
                'sample_report': sample_html,
                'marker_report': marker_html,
                'html': html if html is not None else '',
                'code': sample_code + marker_code + code if code is not None else '',
            }, request = request )



def create_form( request, mode = 'mlgt' ):
    """ return the form and javascript code """
    return _FORM_FACTORY_(request, mode)


def set_form_factory( factory_func ):
    """ factory_func needs to return a tuple of (form, jscode) """
    global _FORM_FACTORY_
    _FORM_FACTORY_ = factory_func

def genaf_form_factory( request, mode = 'mlgt' ):
    return ( basic_query_form(request, mode), jscode(request, mode) )

_FORM_FACTORY_ = genaf_form_factory


def form2dict( request ):
    d = {}
    p = request.params

    if p.get('queryset', None):
        query_text = p.get('queryset')
        selector_d = query2dict(query_text)

    elif p.getall('batch_ids'):
        selector_d = { 'all': [] }
        batch_ids = p.getall('batch_ids')
        for batch_id in batch_ids:
            selector_d['all'].append( { 'batch_id': int(batch_id) })
    else:
        raise RuntimeError('WHOA, need to have either batch code(s) or queryset')

    if p.get('sample_selection', None):
        sample_selection = p.get('sample_selection')
        if sample_selection != 'N':
            selector_d['_:_'] = { 'sample_selection': sample_selection}

    filter_d = {}
    filter_d['marker_ids'] = [ int(x) for x in p.getall('marker_ids') ]
    filter_d['abs_threshold'] = int(p.get('allele_abs_treshhold'))
    filter_d['rel_threshold'] = float( p.get('allele_rel_threshold', 1))
    filter_d['rel_cutoff'] = float( p.get('allele_rel_cutoff'))
    filter_d['sample_qual_threshold'] = float( p.get('sample_qual_threshold'))
    filter_d['marker_qual_threshold'] = float( p.get('marker_qual_threshold'))
    filter_d['sample_filtering'] = p.get('sample_filtering')
    filter_d['stutter_ratio'] = float( p.get('stutter_ratio', 0) )
    filter_d['stutter_range'] = float( p.get('stutter_range', 0) )

    d['selector'] = selector_d
    d['filter'] = filter_d

    d['differentiator'] = {
                'spatial': int(p.get('spatial_differentiation', -1)),
                'temporal': int(p.get('temporal_differentiation', 0))
    }

    d['options'] = {
                'tip_label': p.get('tip_label', None),
                'data_format': p.get('data_format', None),
                'tree_type': p.get('tree_type', None),
                'font_size': p.get('font_size', None),
                'branch_coloring': p.get('branch_coloring', None),
    }

    return d


def sample_summary(sample_summary_df):
    return None

def format_sample_summary(sample_summary_df):
    """ return (html, jscode) """

    body = div()

    tbl = table(class_='table table-condensed table-striped')
    headings = ['Label'] + list(sample_summary_df.columns)
    tbl.add( thead( tr( * ( th(heading) for heading in headings ) ) ) )

    tbl_body = tbody()
    tbl.add( tbl_body )
    for data in sample_summary_df.itertuples():
        row = tr()
        row.add( td(data[0] ))
        for N in data[1:]:
            row.add( td(str(N)) )
        tbl_body.add( row )

    body.add( tbl )

    return (body, '')


def marker_summary(query):
    return None

def format_marker_summary(query):

    dbh = get_dbhandler()

    body = div()

    marker_ids = query.get_analytical_sets().marker_ids
    if marker_ids is None:
        marker_ids = []
    markers = ' | '.join( dbh.get_marker_by_id(x).label for x in marker_ids )
    body.add( div(class_='row')[
        div(b('Initial markers'), class_='col-md-2'),
        div(markers + ' : [%d]' % len(marker_ids), class_='col-md-10')
        ])

    marker_ids = query.get_filtered_analytical_sets().marker_ids
    if marker_ids is None:
        marker_ids = []
    markers = ' | '.join( dbh.get_marker_by_id(x).label for x in marker_ids )
    body.add( div(class_='row')[
        div(b('Filtered markers'), class_='col-md-2'),
        div(markers + ' : [%d]' % len(marker_ids), class_='col-md-10')
        ])
    body.add( br() )

    return (body, '')

def format_refs(ref_list):
    if not ref_list:
        return ''
    if type(ref_list) == str:
        ref_list = [ ref_list ]

    return '<ul>' + ''.join('<li>%s</li>' % s for s in ref_list) + '</ul>'


# multiprocessing capabilities

task_ids = {}
glock = threading.Lock()


def mp_run_callback( settings, callback, params, user, mode, ns=None):
    """ run analyis """

    if ns:
        ns.start_time = int(time())
        ns.status = 'R'
        ns.msg = 'Processing...'
        ns.cerr += 'mp_run_callback(): connecting to db...\n'

    dbh = get_dbhandler_notsafe()
    if dbh is None:
        dbh = get_dbhandler(settings)


    # user authorization should be performed by Query
    q = Query( params, dbh )

    # callback needs to return result (a dictionary object)
    # { 'custom': data, 'options': options,
    # 'html': html_or_None, 'jscode': jscode_or_None }

    if ns:
        ns.cerr += 'mp_run_callback(): processing callback...\n'
        with transaction.manager:
            result = callback( q, user )

    else:
        result = callback( q, user )

    if type(result) != dict:
        return result

    #result['sample_filtering'] = sample_summary( q.get_sample_summary(mode))
    #result['marker_filtering'] = marker_summary( q )

    result['sample_filtering'] = format_sample_summary( q.get_sample_summary(mode) )
    result['marker_filtering'] = format_marker_summary( q )

    if ns:
        ns.finish_time = int(time())
        ns.status = 'D'
        ns.msg = 'Finished...'
        ns.cerr += 'mp_run_callback(): callback finished...\n'

    return result

