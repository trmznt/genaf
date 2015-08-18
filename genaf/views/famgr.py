# FSA pre processing

import logging

log = logging.getLogger(__name__)

from genaf.views import *

from collections import defaultdict
import threading

TEMP_ROOTDIR = 'famgr'

glock = threading.Lock()
local_procs = {}    # -> locks against batch, ensuring only one processing per batch
                    # items: ( procid, current_user, ns )
                    # ns is Namespace object 

class ProcessingSession(object):

    def __init__(self, sesskey=None, user=None, batch=None):

        self.meta = None
        self.rootpath = None
        self.batch = batch
        if self.sesskey is None:
            self.new_session( user, batch )
        else:
            self.rootpath = get_temp_path(self.sesskey, TEMP_ROOTDIR)
            self.load_metadata()


    def new_session(self, user, batch):

        while True:
            sesskey = '%03d-%s' % (batch.id, random_string(16))
            temp_path = get_temp_path(sesskey, TEMP_ROOTDIR)
            if not os.path.exists(temp_path):
                break

        self.sesskey = sesskey
        self.rootpath = temp_path
        os.makedirs(self.rootpath)
        os.makedirs(self.rootpath + '/wd')
        self.meta = dict( user = user, batch = batch.code, batch_id = batch.id, state = 'N' )
        self.save_metadata()


    def save_metadata(self):
        with open( self.get_metafile(), 'w' ) as f:
            yaml.dump( self.meta, f )


    def load_metadata(self):
        with open( self.get_metafile() ) as f:
            self.meta = yaml.load( f )


    def get_metafile(self):
        return '%s/meta.json' % self.rootpath

        

@roles( PUBLIC )
def index(request):

    return None


@roles( PUBLIC )
def view(request):

    batch_id = request.matchdict.get('id')
    batch = get_dbhandler().get_batch_by_id(batch_id)

    # check authorization
    if not request.user.in_group( batch.group ):
        error_page('You are not authorized to view this batch!')


    # get all assay list
    assay_list = []
    for sample in batch.samples:
        for assay in sample.assays:
            assay_list.append( (assay, sample.code) )

    summaries = summarize_assay( assay_list )

    summary_content = div()
    for (item, value) in summaries.items():
        summary_content.add(
            row()[ div(class_='col-md-4')[ item ],
                    div(class_='col-md-3')[ value ]
                ]
            )

    return render_to_response('genaf:templates/famgr/view.mako',
        { 'content': summary_content,
        }, request = request )


def summarize_assay( assay_list ):

    counter = defaultdict(int)

    for (assay, sample_code) in assay_list:
        counter[assay.status] += 1

    return counter

@roles( PUBLIC )
def process(request):



def process_assays(batch_id, login, comm = None, stage = None):

    dbh = get_dbhandler()

    # get assay list
    batch = dbh.get_batch_by_id(batch_id)

    assay_list = []
    for sample in batch.samples:
        for assay in sample.assays:
            assay_list.append( (assay, sample.code) )

    


    


def mp_process_assays(settings, batch_id, login, ns):
    """ this function will be started in different process, so it must initialize
        everything from scratch, including database connection
    """

    cerr('mp_process_assays(): connecting to db')

    dbh = get_dbhandler_notsafe()
    if dbh is None:
        dbh = get_dbhandler(settings)

    cerr('mp_process_assays(): processing...')
    result = process_assays(batch_id, login, ns)

    return result
    

