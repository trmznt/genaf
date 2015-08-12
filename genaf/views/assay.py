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
