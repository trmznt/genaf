import logging

log = logging.getLogger(__name__)

from genaf.views import *


dye_colours = {  'B': 'label label-primary',
                'G': 'label label-success',
                'Y': 'label label-warning',
                'R': 'label label-danger'
}

@roles( PUBLIC )
def index(request):

    dbh = get_dbhandler()
    panels = dbh.get_panels().order_by(dbh.Panel.code)

    # create the table body

    panel_table = table(class_='table table-condensed table-striped')
    panel_table[ thead()[ tr()[
                    th(''), th('Panel code'), th('Ladder'), th('Markers')
                    ] ] ]
    body_table = tbody()

    for panel in panels:
        labels = []
        if panel.data:
            for l,d in panel.data['markers'].items():
                m = panel.get_marker(l)
                labels.append(
                    a(href=request.route_url('genaf.marker-view', id=m.id))[
                            span(class_=dye_colours[d['filter']])[ l ] ]
                )
        body_table[ tr() [
                    td(''), td( panel.code ), td(panel.get_ladder_code()),
                    td( * labels )
#                    td( * list(
#                        a(href=request.route_url('genaf.marker', id=m.id))[
#                            span(class_='badge')[ m.code ] ] for m in panel.get_markers() )
#                    )
                ]
            ]

    panel_table[ body_table ]

    return render_to_response( 'genaf:templates/panel/index.mako',
        {   'panel_table': panel_table,
        }, request = request )


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
