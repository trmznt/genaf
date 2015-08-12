import logging

log = logging.getLogger(__name__)

from genaf.views import *


@roles( PUBLIC )
def index(request):
    
    dbh = get_dbhandler()
    panels = dbh.get_panels().order_by(dbh.Panel.code)

    # create the table body

    panel_table = table(class_='table table-condensed table-striped')
    panel_table[ thead()[ tr()[
                    th(''), th('Panel code'), th('Markers')
                    ] ] ]
    body_table = tbody()

    for panel in panels:
        body_table[ tr() [
                    td(''), td( panel.code ),
                    td( * list(
                        a(href=request.route_url('genaf.marker', id=m.id))[
                            span(class_='badge')[ m.code ] ] for m in panel.get_markers() )
                    )
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
