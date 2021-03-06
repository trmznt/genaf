import logging

log = logging.getLogger(__name__)

import matplotlib
matplotlib.use('Agg')
log.info('Setting up matplotlib to use Agg')

from pyramid.config import Configurator

from rhombus import includeme as rho_includeme, init_app as rhombus_init_app, add_route_view
from rhombus.lib.utils import cout, cerr, cexit, generic_userid_func
from rhombus.lib.fsoverlay import fsomount
from rhombus.models.core import set_func_userid

from genaf.lib.procmgmt import init_queue
from genaf.lib.configs import set_temp_path, get_temp_path, TEMP_TOOLS

import os

def includeme( config ):

    # GenAF configuration

    #config.add_static_view('genaf_assets', 'genaf:static/assets/')
    config.add_static_view(name='genaf_static', path="genaf:static/")


    add_route_view( config, 'genaf.views.marker', 'genaf.marker',
        '/marker',
        '/marker/@@action',
        '/marker/{id}@@edit',
        '/marker/{id}@@save',
        ('/marker/{id}', 'view')
    )

    add_route_view( config, 'genaf.views.panel', 'genaf.panel',
        '/panel',
        '/panel/@@action',
        '/panel/{id}@@edit',
        '/panel/{id}@@save',
        ('/panel/{id}', 'view')
    )

    add_route_view( config, 'genaf.views.batch', 'genaf.batch',
        '/batch',
        '/batch/@@action',
        '/batch/{id}@@edit',
        '/batch/{id}@@save',
        ('/batch/{id}', 'view')

    )

    add_route_view( config, 'genaf.views.sample', 'genaf.sample',
        '/sample',
        '/sample/@@action',
        '/sample/{id}@@edit',
        '/sample/{id}@@save',
        ('/sample/{id}', 'view')

    )

    add_route_view( config, 'genaf.views.location', 'genaf.location',
        '/location',
        '/location/@@action',
        '/location/{id}@@edit',
        '/location/{id}@@save',
        ('/location/{id}', 'view')
    )


    add_route_view( config, 'genaf.views.assay', 'genaf.assay',
        '/assay',
        '/assay/@@action',
        '/assay/{id}@@drawchannels',
        '/assay/{id}@@edit',
        '/assay/{id}@@save',
        ('/assay/{id}', 'view')

    )

    add_route_view( config, 'genaf.views.channel', 'genaf.channel',
        '/channel/@@action',
        ('/channel/{id}', 'view'),
    )


    add_route_view( config, 'genaf.views.uploadmgr', 'genaf.uploadmgr',
        '/uploadmgr',
        '/uploadmgr/@@action',
        '/uploadmgr/{id}@@edit',
        '/uploadmgr/{id}@@save',
        ('/uploadmgr/{id}@@mainpanel', 'mainpanel', 'json'),
        ('/uploadmgr/{id}@@rpc', 'rpc', 'json'),
        ('/uploadmgr/{id}@@uploaddata', 'uploaddata', 'json'),
        ('/uploadmgr/{id}@@uploadinfo', 'uploadinfo', 'json'),
        '/uploadmgr/{id}@@template',
        ('/uploadmgr/{id}', 'view')

    )


    add_route_view( config, 'genaf.views.famgr', 'genaf.famgr',
        '/famgr',
        '/famgr/{id}@@process',
        ('/famgr/{id}', 'view')
    )

    add_route_view( config, 'genaf.views.task', 'genaf.task',
        '/task',
        ('/task/{id}', 'view'),
    )

    add_route_view( config, 'rhombus.views.fso', 'rhombus.fso',
        '/fso{path:.*}@@view',
        '/fso{path:.*}@@edit',
        '/fso{path:.*}@@save',
        '/fso{path:.*}@@action',
        ('/fso{path:.*}', 'index'),
    )

    # tools and analysis

    config.add_route('tools-help', '/tools/help')
    config.add_view('genaf.views.tools.help.index', route_name='tools-help')

    config.add_route('tools-allele', '/tools/allele')
    config.add_view('genaf.views.tools.allele.index', route_name='tools-allele')

    config.add_route('tools-he', '/tools/he')
    config.add_view('genaf.views.tools.he.index', route_name='tools-he')

    config.add_route('tools-genotype', '/tools/genotype')
    config.add_view('genaf.views.tools.genotype.index', route_name='tools-genotype')

    config.add_route('tools-moi', '/tools/moi')
    config.add_view('genaf.views.tools.moi.index', route_name='tools-moi')

    config.add_route('tools-pcoa', '/tools/pcoa')
    config.add_view('genaf.views.tools.pcoa.index', route_name='tools-pcoa')

    config.add_route('tools-mca', '/tools/mca')
    config.add_view('genaf.views.tools.mca.index', route_name='tools-mca')

    config.add_route('tools-export', '/tools/export')
    config.add_view('genaf.views.tools.export.index', route_name='tools-export')

    config.add_route('tools-fst', '/tools/fst')
    config.add_view('genaf.views.tools.fst.index', route_name='tools-fst')

    config.add_route('tools-ld', '/tools/ld')
    config.add_view('genaf.views.tools.ld.index', route_name='tools-ld')

    config.add_route('tools-nj', '/tools/nj')
    config.add_view('genaf.views.tools.nj.index', route_name='tools-nj')

    config.add_route('tools-sample', '/tools/sample')
    config.add_view('genaf.views.tools.sample.index', route_name='tools-sample')

    config.add_route('tools-djost', '/tools/djost')
    config.add_view('genaf.views.tools.djost.index', route_name='tools-djost')

    # utilities

    config.add_route('utils-export', '/utils/export')
    config.add_view('genaf.views.utils.export.index', route_name='utils-export')

    config.add_route('utils-plot', '/utils/plot')
    config.add_view('genaf.views.utils.plot.index', route_name='utils-plot')


def init_app( global_config, settings, prefix = '/mgr' ):

    # global, shared settings

    temp_path = settings['genaf.temp_directory']
    set_temp_path( temp_path )

    fsomount(TEMP_TOOLS, get_temp_path('', TEMP_TOOLS))

    set_func_userid( generic_userid_func )

    # preparing for multiprocessing
    init_queue(settings)

    config = rhombus_init_app( global_config, settings, prefix=prefix )

    return config


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings)
    config.include('pyramid_chameleon')
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_route('home', '/')
    config.scan()
    return config.make_wsgi_app()
