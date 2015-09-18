
from genaf.views import *


def basic_query_form(request):

    dbh = get_dbhandler()

    qform = form(name='queryform', action='#')

    # samples
    batches = list( dbh.get_batches(groups = request.user.groups) )
    qform.add(
        fieldset()[
            input_select(name='batches', label='Batch code(s)', multiple = True,
                    options = [ (b.id, b.code) for b in batches ]),
            input_text(name='queryset', label='Query set'),
        ]
    )

    qform.get('queryset').add_error('Optional, can be left blank')

    # markers
    markers = list( dbh.get_markers() )
    markers.sort( key = lambda x: x.label )
    qform.add(
        fieldset()[
            input_select(name='markers', label='Marker(s)', multiple = True,
                    options = [ (m.id, m.label) for m in markers ]),
        ]
    )

    # allele & marker filtering
    qform.add(
        fieldset()[
            input_text(name='allele_abs_treshhold', label='Allele absolute threshold',
                        value=100),
            input_text(name='allele_rel_threshold', label='Allele relative threshold',
                        value=0.33),
            input_text(name='allele_rel_cutoff', label='Allele relative cutoff',
                        value=0.00),
            input_text(name='sample_qual_threshold', label='Sample quality threshold',
                        value=0.50),
            input_text(name='marker_qual_threshold', label='Marker quality threshold',
                        value=0.10)
        ]
    )

    qform.add(
        fieldset()[ submit_bar('Execute', '_exec') ]
    )

    return qform


def process_request( request, header_text, button_text, callback ):

    if not request.GET.get('_method', None) in ['_exec', '_yamlexec']:

        return render_to_response('genaf:templates/tools/index.mako',
            {   'header_text': header_text,
                'queryform': basic_query_form(request),
            }, request = request)


        
