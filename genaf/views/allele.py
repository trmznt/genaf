import logging

log = logging.getLogger(__name__)

from rhombus.lib.utils import cerr, cout
from rhombus.views.generics import error_page

from genaf.views import *


@roles( PUBLIC )
def index(request):
    pass

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


def edit_form(allele, dbh, request, static=False):

    eform = form( name='genaf/allele', method=POST,
                    action=request.route_url('genaf.assay-action') )
    eform.add(
        fieldset(
            input_hidden(name='genaf-allele_id', value=allele.id),
            input_show('genaf-allele_marker', 'Marker', value=allele.alleleset.marker.label),
            input_show('genaf-allele_size', 'Size', value=allele.size),
            input_show('genaf-allele_rtime', 'Retention time', value=allele.rtime),
            input_show('genaf-allele_height', 'Height', value=allele.height),
            input_text('genaf-allele_bin', 'Bin', value=allele.bin),
            input_select_ek('genaf-allele_type_id', 'Type', value=allele.type_id,
                    parent_ek = dbh.get_ekey('@PEAK-TYPE')),
            submit_bar('Update allele', 'update_allele')
        )
    )

    return eform


def parse_form(d):

    allele_d = dict()
    allele_d['id'] = int(d.get('genaf-allele_id'))
    allele_d['type_id'] = int(d.get('genaf-allele_type_id'))

    return allele_d

