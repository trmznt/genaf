# FSA pre processing

import logging

log = logging.getLogger(__name__)

from rhombus.lib.utils import get_dbhandler, get_dbhandler_notsafe, silent_rmdir

from genaf.views import *
from genaf.lib.procmgmt import subproc, getproc, getmanager, estimate_time

from fatools.lib import params
from fatools.lib.const import assaystatus

from collections import defaultdict
import threading, transaction
from time import time

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

    assay_status_panel = div()
    for (label, key) in [ ('Assigned', assaystatus.assigned),
                            ('Scanned', assaystatus.scanned),
                            ('Preannotated', assaystatus.preannotated),
                            ('Ladder aligned', assaystatus.aligned),
                            ('Called', assaystatus.called),
                            ('Binned', assaystatus.binned),
                            ('Annotated', assaystatus.annotated),
                        ]:
        if key in summaries:
            value = summaries[key]
            assay_status_panel.add(
                row()[ div(class_='col-md-4')[ label ],
                    div(class_='col-md-3')[ value ]
                    ]
                )

    summary_content = div()[ div('FSA status:'), assay_status_panel ]
    summary_content.add(
        row()[ div(class_='col-md-3')[
            a(href=request.route_url('genaf.famgr-process', id=batch_id)) [
                span(class_='btn btn-success')[ 'Process FSA' ] ] ]
        ]
    )

    return render_to_response('genaf:templates/famgr/view.mako',
        {   'content': summary_content,
            'batch': batch,
        }, request = request )


def summarize_assay( assay_list ):

    counter = defaultdict(int)

    for (assay, sample_code) in assay_list:
        counter[assay.status] += 1

    return counter


@roles( PUBLIC )
def process(request):

    batch_id = request.matchdict.get('id')

    if batch_id in local_procs:
        (procid, login, batch_code, ns) = local_procs[batch_id]

        if login != request.user.login:
            seconds = 0
            msg = div()[ p('Another task started by %s is currently running batch: %s' %
                                ( login, batch_code ))
                    ]
        else:

            procunit = getproc(procid)
            if procunit.status in ['D', 'U']:
                seconds = 0
                if procunit.exc:
                    msg = div()[
                        p('Assay processing failed. Please see the following error:'),
                        p( procunit.exc ),
                    ]

                else:
                    result = procunit.result
                    msg = div()[ p('Assay processing finished.'),
                             p('Statistics: %s' % str(result[0]) ),
                             p()[ a(href=request.route_url('genaf.famgr-view',id=batch_id))[
                                            span(class_='btn btn-success')[ 'Continue' ]
                                        ]
                            ]
                        ]
                    if result[1]:
                        msg.add( div()[ p( *result[1] ) ] )

                del ns
                del local_procs[batch_id]

            else:
                seconds = 10
                msg = div()[ p('Output: %s' % ns.output), p('Processing...') ]

    else:

        batch = get_dbhandler().get_batch_by_id(batch_id)
        batch_code = batch.code

        # check authorization
        if not request.user.in_group( batch.group ):
            error_page('You are not authorized to view this batch!')

        if False:
            # set the above to True for single-process debugging purpose
            process_assays(batch_id, request.user.login, None)

        with glock:

            ns = getmanager().Namespace()
            ns.output = ''
            procid, msg = subproc( request.user.login, None,
                    mp_process_assays, request.registry.settings,
                    batch_id, request.user.login, ns )
            local_procs[batch_id] = (procid, request.user.login, batch_code, ns)

        msg = div()[ p('Starting assay processing task') ]
        seconds = 10

    return render_to_response('genaf:templates/famgr/process.mako',
        {   'msg': msg,
            'batch_code': batch_code,
            'seconds': seconds,
        }, request = request )



def scan_assays(assay_list, dbh, log, scanning_parameter, comm):

    success = failed = skipped = subtotal = 0
    total = len(assay_list)
    start_time = time()
    for (assay_id, sample_code) in assay_list:
        with transaction.manager:
            assay = dbh.get_assay_by_id(assay_id)
            try:
                if assay.status == assaystatus.assigned:
                    assay.scan( scanning_parameter )
                    success += 1
                else:
                    skipped += 1
            except RuntimeError as err:
                log.append('ERR scanning -- assay %s | %s - error: %s' %
                    ( assay.filename, sample_code, str(err) )
                )
                failed += 1
        subtotal += 1
        if comm:
            comm.output = (
                'scanned: %d | failed: %d | skipped: %d | remaining: %d | estimated: %s'
                % ( success, failed, skipped, total-subtotal,
                    estimate_time(start_time, time(), success, total-subtotal)) )

    if comm:
        comm.output = 'scanned: %d | failed: %d | skipped: %d' % (
                    success, failed, skipped)

    return (success, failed, skipped)


def preannotate_assays(assay_list, dbh, log, scanning_parameter, comm):

    success = failed = skipped = subtotal = 0
    total = len(assay_list)
    start_time = time()
    for (assay_id, sample_code) in assay_list:
        with transaction.manager:
            assay = dbh.get_assay_by_id(assay_id)
            try:
                if assay.status == assaystatus.scanned:
                    assay.preannotate( scanning_parameter )
                    success += 1
                else:
                    skipped += 1
            except RuntimeError as err:
                log.append('ERR preannotating -- assay %s | %s - error: %s' %
                    ( assay.filename, sample_code, str(err) )
                )
                failed += 1
        subtotal += 1

        if comm and subtotal % 5 == 0:
            comm.output = (
                'preannotated: %d | failed: %d | skipped: %d | remaining: %d | estimated: %s'
                % (success, failed, skipped, total-subtotal,
                    estimate_time(start_time, time(), success, total-subtotal )) )

    if comm:
        comm.output = 'preannotated: %d | failed: %d | skipped: %d' % (
                    success, failed, skipped)

    return (success, failed, skipped)


def align_assays(assay_list, dbh, log, scanning_parameter, comm):

    success = failed = skipped = subtotal = 0
    total = len(assay_list)
    start_time = time()
    for (assay_id, sample_code) in assay_list:
        with transaction.manager:
            assay = dbh.get_assay_by_id(assay_id)
            try:
                if assay.status == assaystatus.preannotated:
                    retval = assay.alignladder(excluded_peaks = None)
                    (dpscore, rss, peaks_no, ladders_no, qcscore, remarks, method) = retval
                    if qcscore < 0.9:
                        log.append('WARN alignladder - '
                            'low qcscore %3.2f %4.2f %5.2f %d/%d %s for %s | %s'
                                % ( qcscore, dpscore, rss, peaks_no, ladders_no,
                                    method, sample_code, assay.filename) )

                    success += 1
                else:
                    skipped += 1

            except RuntimeError as err:
                log.append('ERR aligning ladder - assay %s | %s - error: %s' %
                    ( assay.filename, sample_code, str(err) ) )
                failed += 1
        subtotal += 1

        if comm and subtotal % 5 == 0:
            comm.output = (
                'aligned: %d | failed: %d | skipped: %d | remaining: %d | estimated: %s'
                % ( success, failed, skipped, total-subtotal,
                    estimate_time(start_time, time(), success, total-subtotal)) )

    if comm:
        comm.output = 'aligned: %d | failed: %d | skipped: %d' % (
                    success, failed, skipped)

    return (success, failed, skipped)


def call_assays(assay_list, dbh, log, scanning_parameter, comm):

    success = failed = skipped = subtotal = 0
    total = len(assay_list)
    start_time = time()
    for (assay_id, sample_code) in assay_list:
        with transaction.manager:
            assay = dbh.get_assay_by_id(assay_id)
            try:
                if assay.status == assaystatus.aligned:
                    assay.call( scanning_parameter )
                    success += 1
                else:
                    skipped += 1
            except RuntimeError as err:
                log.append('ERR calling -- assay %s | %s - error: %s' %
                    ( assay.filename, sample_code, str(err) )
                )
                failed += 1
        subtotal += 1

        if comm and subtotal % 10 == 0:
            comm.output = (
                'called: %d | failed: %d | skipped: %d | remaining: %d | estimated: %s'
                % (success, failed, skipped, total-subtotal,
                    estimate_time(start_time, time(), success, total-subtotal )) )

    if comm:
        comm.output = 'called: %d | failed: %d | skipped: %d' % (
                    success, failed, skipped)

    return (success, failed, skipped)

def bin_assays(assay_list, dbh, log, scanning_parameter, comm):

    success = failed = skipped = subtotal = 0
    total = len(assay_list)
    start_time = time()
    for (assay_id, sample_code) in assay_list:
        with transaction.manager:
            assay = dbh.get_assay_by_id(assay_id)
            try:
                if assay.status == assaystatus.called:
                    assay.bin( scanning_parameter )
                    success += 1
                else:
                    skipped += 1
            except RuntimeError as err:
                log.append('ERR binning -- assay %s | %s - error: %s' %
                    ( assay.filename, sample_code, str(err) )
                )
                failed += 1
        subtotal += 1

        if comm and subtotal % 10 == 0:
            comm.output = (
                'binned: %d | failed: %d | skipped: %d | remaining: %d | estimated: %s'
                % (success, failed, skipped, total-subtotal,
                    estimate_time(start_time, time(), success, total-subtotal )) )

    if comm:
        comm.output = 'binned: %d | failed: %d | skipped: %d' % (
                    success, failed, skipped)

    return (success, failed, skipped)


def postannotate_assays(assay_list, dbh, log, scanning_parameter, comm):

    success = failed = skipped = subtotal = 0
    total = len(assay_list)
    start_time = time()
    for (assay_id, sample_code) in assay_list:
        with transaction.manager:
            assay = dbh.get_assay_by_id(assay_id)
            try:
                if assay.status == assaystatus.binned:
                    assay.postannotate( scanning_parameter )
                    success += 1
                else:
                    skipped += 1
            except RuntimeError as err:
                log.append('ERR postannotating -- assay %s | %s - error: %s' %
                    ( assay.filename, sample_code, str(err) )
                )
                failed += 1
        subtotal += 1

        if comm and subtotal % 5 == 0:
            comm.output = (
                'postannotated: %d | failed: %d | skipped: %d | remaining: %d | estimated: %s'
                % (success, failed, skipped, total-subtotal,
                    estimate_time(start_time, time(), success, total-subtotal )) )

    if comm:
        comm.output = 'postannotated: %d | failed: %d | skipped: %d' % (
                    success, failed, skipped)

    return (success, failed, skipped)


def process_assays(batch_id, login, comm = None, stage = 'all'):

    dbh = get_dbhandler()

    # get assay list
    assay_list = get_assay_ids( batch_id )

    log = []
    stats = {}

    scanning_parameter = params.Params()

    # scan peaks
    if stage in ['all', 'scan']:
        stats['scan'] = scan_assays(assay_list, dbh, log, scanning_parameter, comm)

    # preannotate peaks
    if stage in ['all', 'preannotate']:
        stats['preannotated'] = preannotate_assays(assay_list, dbh, log, scanning_parameter, comm)

    # align peaks
    if stage in [ 'all', 'align' ]:
        stats['aligned'] = align_assays(assay_list, dbh, log, scanning_parameter, comm)

    # call peaks
    if stage in ['all', 'call']:
        stats['called'] = call_assays(assay_list, dbh, log, scanning_parameter, comm)

    # bin peaks
    if stage in ['all', 'bin']:
        stats['binned'] = bin_assays(assay_list, dbh, log, scanning_parameter, comm)

    # postannotate peaks
    if stage in ['all', 'postannotate']:
        stats['postannotated'] = postannotate_assays(assay_list, dbh, log,
                scanning_parameter, comm)

    return stats, log

    # ladder alignment
    success = failed = 0
    for (assay_id, sample_code) in assay_list:
        with transaction.manager:
            assay = dbh.get_assay_by_id(assay_id)
            try:
                if assay.status == assaystatus.preannotated:
                    retval = assay.alignladder(excluded_peaks = None)
                    (dpscore, rss, peaks_no, ladders_no, qcscore, remarks, method) = retval
                    if qcscore < 0.9:
                        log.append('WARN alignladder - '
                            'low qcscore %3.2f %4.2f %5.2f %d/%d %s for %s | %s'
                                % ( qcscore, dpscore, rss, peaks_no, ladders_no,
                                    method, sample_code, assay.filename) )

                    success += 1

            except RuntimeError as err:
                log.append('ERR alignladder - assay %s | %s - error: %s' %
                    ( assay.filename, sample_code, str(err) ) )
                failed += 1

        if comm and (success + failed) % 10 == 0:
            comm.output = 'Aligned ladder with %d successful assay(s), %d failed assay(s)' % (
                     success, failed )

    if comm:
        comm.output = 'Aligned ladder with %d successful assay(s), %d failed assay(s)' % (
            success, failed )
    stats['aligned'] = (success, failed)

    # calling peaks
    success = failed = 0
    for (assay_id, sample_code) in assay_list:
        with transaction.manager:
            assay = dbh.get_assay_by_id(assay_id)
            try:
                if assay.status == assaystatus.aligned:
                    assay.call(scanning_parameter.nonladder)
                    success += 1

            except RuntimeError as err:
                log.append('ERR call - assay %s | %s - error: %s' %
                    ( assay.filename, sample_code, str(err) ) )
                failed += 1

        if comm and (success + failed) % 10 == 0:
            comm.output = 'Called %d successful assay(s), %d failed assay(s)' % (
                     success, failed )

    if comm:
        comm.output = 'Called %d successful assay(s), %d failed assay(s)' % (
            success, failed )
    stats['called'] = (success, failed)

    # binning peaks
    if stage in ['all', 'bin']:
        stats['binned'] = bin_assays(assay_list, dbh, log, scanning_parameter, comm)


    if stage in ['all', 'postannotate']:
        stats['postannotated'] = postannotate_assays(assay_list, dbh, log,
                scanning_parameter, comm)


    return stats, log


def get_assay_ids(batch_id):

    dbh = get_dbhandler()

    assay_list = []
    with transaction.manager:
        batch = dbh.get_batch_by_id(batch_id)

        for sample in batch.samples:
            for assay in sample.assays:
                assay_list.append( (assay.id, sample.code) )

    return assay_list



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


