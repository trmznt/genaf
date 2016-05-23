import logging

log = logging.getLogger(__name__)

from rhombus.views.fso import save_file
from rhombus.lib.utils import get_dbhandler, get_dbhandler_notsafe, silent_rmdir
from rhombus.lib.roles import SYSADM, DATAADM
from rhombus.lib.tags import *

from genaf.views import *
from genaf.lib.procmgmt import subproc, getproc, getmanager, estimate_time, get_queue


@roles( PUBLIC )
def index(request):

    queue = get_queue()
    table_body = tbody()

    for (procid, proc) in queue.procs.items():
        table_body.add(
            tr()[
                td('%s' % procid),
                td('%s' % proc.uid),
                td('%s' % str(proc.time_queue)),
                td('%s' % str(proc.time_start if proc.time_start else 'Not started')),
                td('%s' % str(proc.time_finish if proc.time_finish else 'Not finished')),
                td('%s' % proc.status),
            ]
        )

    html = div()[
        table(class_='table table-condensed table-stripped')[
            thead()[
                th('Task ID'),
                th('User'),
                th('Submitted'),
                th('Started'),
                th('Finished'),
                th('Status')
            ],
            table_body,
        ]
    ]

    return render_to_response("genaf:templates/task/index.mako",
            { 'html': html,
            }, request=request)


@roles( PUBLIC )
def view(request):

    raise NotImplementedError()