# FSA bulk upload manager

import logging

log = logging.getLogger(__name__)

from rhombus.views.fso import save_file
from rhombus.lib.utils import get_dbhandler, get_dbhandler_notsafe, silent_rmdir
from rhombus.lib.roles import SYSADM, DATAADM

from genaf.views import *
from genaf.lib.procmgmt import subproc, getproc, getmanager, estimate_time

from fatools.lib.utils import tokenize, detect_buffer

from sqlalchemy.exc import IntegrityError

from pyramid.response import Response
from pyramid.settings import asbool
from datetime import datetime
import os, yaml, re, shutil, time, csv, threading, transaction, sys, io

from pprint import pprint

TEMP_ROOTDIR = 'uploadmgr'

glock = threading.Lock()
commit_procs = {}

## at some point, the metadata will be stored in dogpile.cache rather than in individual
## meta.dat file



class UploaderSession(object):

    def __init__(self, sesskey=None, user=None, batch=None):
        self.meta = None
        self.rootpath = None
        self.sesskey = sesskey
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
        os.makedirs(self.rootpath + '/tmp')
        os.makedirs(self.rootpath + '/payload')
        curtime = time.time()
        self.meta = dict(   user = user.login, batch = batch.code, batch_id = batch.id,
                            payload = '', ctime = curtime, mtime = curtime,
                            state = 'N' )
        self.save_metadata()


    def save_metadata(self):
        with open( self.get_metafile(), 'w' ) as f:
            yaml.dump( self.meta, f )


    def load_metadata(self):
        with open( self.get_metafile() ) as f:
            self.meta = yaml.load( f )


    def get_metafile(self):
        return '%s/meta.json' % self.rootpath


    def is_authorized(self, user):
        return self.meta['user'] == user.login or user.has_roles(SYSADM, DATAADM)


    def get_sesskey(self):
        return self.sesskey

    def has_payload(self):
        return 'payload' in self.meta and self.meta['payload']

    def payload_verified(self):
        return 'payload_count' in self.meta and self.meta['payload_count'] >= 0

    def has_metaassay(self):
        return 'infofile' in self.meta and self.meta['infofile']

    def metaassay_verified(self):
        return 'infofile_count' in self.meta and self.meta['infofile_count'] >= 0


    def add_file(self, filename, filestorage, request):

        dest_path = '%s/tmp/%s' % (self.rootpath, filename)
        (size, total) = save_file(dest_path, filestorage, request)
        return (size, total)


    def check_datafile(self):

        if 'payload' in self.meta and self.meta['payload']:
            return dict(    filename = self.meta['payload'],
                            filesize = self.meta.get('payload_size', 0),
                        )
        return None

    def check_infofile(self):

        if 'infofile' in self.meta and self.meta['infofile']:
            return dict(    filename = self.meta['infofile'],
                            filesize = self.meta.get('infofile_size', 0),
                        )
        return None


    def extract_payload(self):
        shutil.unpack_archive( '%s/tmp/%s' % (self.rootpath, self.meta['payload']),
                                '%s/payload/' % self.rootpath )


    def verify_datafile(self):
        # get assay list file

        self.extract_payload()

        assay_files = {}
        err_log = []
        for (rootdir, _, filenames) in os.walk( '%s/payload/' % self.rootpath ):
            for filename in filenames:
                if filename in assay_files:
                    err_log.append('Duplicate assay filename found: %s' % filename)
                    continue
                assay_files[filename] = '%s/%s' % (rootdir, filename)

        with open('%s/assay_list.yaml' % self.rootpath, 'w') as f:
            yaml.dump( assay_files, f)

        if not err_log:
            self.meta['payload_count'] = len(assay_files)

        return (len(assay_files), err_log)


    def upload_payload(self, dry_run=False, comm = None):
        """ if dry_run = False, this method can be used to verify FSA info file """

        print('running upload_payload')

        with open('%s/assay_list.yaml' % self.rootpath) as f:
            assay_files = yaml.load( f )

        # check for Mac Excel file
        with open('%s/tmp/%s' % (self.rootpath, self.meta['infofile'])) as f:
            buf, delim = detect_buffer( f.read() )

        inrows = csv.DictReader( io.StringIO(buf), delimiter = delim )

        for f in ['SAMPLE', 'FILENAME', 'PANEL', 'OPTIONS']:
            if f not in inrows.fieldnames:
                return 0, ['ERROR - field %s not in the header of FSA manifest file!' % f]

        dbh = get_dbhandler()
        batch = dbh.get_batch( self.meta['batch'] )

        total_assay = 0
        failed_assay = 0
        line_counter = 1
        counted_assay = self.meta.get('infofile_count', 0)
        start_time = time.time()
        err_log = []

        for r in inrows:

            line_counter += 1

            if not (r['FILENAME'] and r['SAMPLE']) or '#' in [ r['FILENAME'][0], r['SAMPLE'][0] ]:
                continue

            options = None
            if r['OPTIONS']:
                options = tokenize( r['OPTIONS'] )

            try:

                # get & check sample
                sample = batch.search_sample( r['SAMPLE'] )
                if not sample:
                    err_log.append('Line %03d - sample code: %s does not exist' %
                                        ( line_counter, r['SAMPLE'] ))
                    continue

                # get & check assay file
                if r['FILENAME'] not in assay_files:
                    err_log.append('Line %03d - assay file: %s is not in the payload file' %
                                        ( line_counter, r['FILENAME'] ))
                    continue

                filename = r['FILENAME']
                panel_code = r['PANEL']
                sample_code = sample.code

                try:
                    with open( assay_files[ filename ], 'rb') as f:
                        trace = f.read()

                    a = sample.add_fsa_assay( trace,
                                filename=filename,
                                panel_code = panel_code,
                                options = options,
                                species = batch.species,
                                dbhandler = dbh,
                                dry_run = dry_run )
                    dbh.session().flush()

                    total_assay += 1

                except RuntimeError as err:
                    err_log.append('Line %03d - runtime error: %s' % (line_counter, str(err)))
                    failed_assay += 1


                except IntegrityError as err:
                    if 'uq_assays_filename_panel_id_sample_id' in repr(err):
                        raise RuntimeError('Line %03d - integrity error: '
                            'FSA with filename %s for sample %s with panel %s already exists in the database. '
                            'Please recheck your data, or remove the FSA from the database first, or '
                            'remove this line entry.'
                            % (line_counter, filename, sample_code, panel_code))
                    else:
                        raise err

            except RuntimeError as err:
                failed_assay += 1
                raise

            if (total_assay + failed_assay) % 5 == 0 and comm is not None:

                remaining_assay = counted_assay - total_assay - failed_assay
                comm.cout = ('uploaded: %d | failed: %d | remaining: %d | estimated remaining time: %s'
                        % (total_assay, failed_assay, remaining_assay,
                            estimate_time(start_time, time.time(), total_assay, remaining_assay)))

        if comm is not None:
            comm.cout = 'uploaded %d FSA file(s), failed %d FSA file(s)' % (
                                total_assay, failed_assay )

        if not err_log:
            self.meta['infofile_count'] = total_assay

        return total_assay, err_log


    def get_template(self):

        with open('%s/assay_list.yaml' % self.rootpath) as f:
            assay_files = yaml.load( f )

        filenames = sorted(assay_files.keys())\

        buf_str = io.StringIO()
        buf_str.write('FILENAMES\tSAMPLE\tPANEL\tOPTIONS\n')
        for filename in filenames:
            buf_str.write('%s\t\t\t\n' % filename)
        buf_str.seek(0)
        return buf_str


    def clear(self):
        silent_rmdir(self.rootpath)

    @property
    def ctime(self):
        return datetime.fromtimestamp(self.meta['ctime'])

    @property
    def mtime(self):
        return datetime.fromtimestamp(self.meta['mtime'])


def new_session(request, batch):

    uploader_session = UploaderSession( user = request.user, batch = batch )
    return uploader_session.get_sesskey()


def list_sessions(batch):

    root_temp_path = get_temp_path('', TEMP_ROOTDIR)
    paths = os.listdir( root_temp_path )

    # in this directory, search for path that starts with batch_id

    prefix = '%03d-' % batch.id
    session_paths = [ x for x in paths if x.startswith(prefix) ]

    uploader_sessions = []
    for sesspath in session_paths:
        uploader_session = UploaderSession( sesskey = sesspath )
        uploader_sessions.append( uploader_session )

    return uploader_sessions


@roles( PUBLIC )
def index(request):
    """ provide listing of available upload sessions """

    batch_id = request.params.get('batch_id', 0)
    if batch_id == 0:
        return error_page(request, 'Please provide batch id!')

    batch = get_dbhandler().get_batch_by_id( batch_id )

    # check authorization
    if not batch.is_manageable(request.user):
        return error_page(request, 'You are not authorized to view this batch!')

    uploader_sessions = list_sessions(batch)

    return render_to_response('genaf:templates/uploadmgr/index.mako',
                {   'sessions': uploader_sessions,
                    'batch': batch,
                }, request = request )


@roles( PUBLIC )
def view(request):

    sesskey = request.matchdict.get('id')

    # if sesskey does not exists, this will throw exception
    uploader_session = UploaderSession( sesskey = sesskey )

    # sanity checks
    #if not os.path.exists(temp_path):
    #    raise error_page('Upload session with key: %s does not exist!' % sesskey)

    if not uploader_session.is_authorized( request.user ):
        raise error_page('You are not authorized to view this session')

    # if sesskey in commit_procs, just redirect to the running uploading process page
    if sesskey in commit_procs:
        return HTTPFound(location = request.route_url('genaf.uploadmgr-save', id=sesskey))

    batch = get_dbhandler().get_batch_by_id( uploader_session.meta['batch_id'] )

    # convert time
    uploader_session.meta['ctime'] = time.ctime(uploader_session.meta['ctime'])
    uploader_session.meta['mtime'] = time.ctime(uploader_session.meta['mtime'])

    return render_to_response('genaf:templates/uploadmgr/view2.mako',
            {   'meta': uploader_session.meta,
                'batch': batch,
                'sesskey': sesskey,
            },
            request = request)


@roles( PUBLIC )
def mainpanel(request):
    """ return JSON response """

    sesskey = request.matchdict.get('id')

    uploader_session = UploaderSession( sesskey = sesskey )

    if not uploader_session.is_authorized( request.user ):
        return dict( html = p('You are not authorized to view this session') )

    html, code = compose_mainpanel(uploader_session, request)

    return dict( html = str(html), code = code)


def compose_mainpanel(uploader_session, request):

    payload_panel = get_payload_info(uploader_session, request)
    payload_buttons, payload_code = get_payload_bar(uploader_session, request)
    metaassay_panel = get_metaassay_info(uploader_session, request)
    metaassay_buttons, metaassay_code = get_metaassay_bar(uploader_session, request)
    html = div( payload_panel, metaassay_panel, metaassay_buttons, payload_buttons )

    code = payload_code + metaassay_code

    return (html, code)


def get_payload_info(up_session, request):

    info_panel = div()
    if up_session.has_payload():
        # doesn't have payload yet, show upload pan

        info_panel.add(
            row()[
                div(class_='col-md-3')[ span(class_='pull-right')['FSA archived/payload file :'] ],
                div(class_='col-md-5')[ up_session.meta['payload'] ],
            ],
            row()[
                div(class_='col-md-3')[ span(class_='pull-right')['File size :'] ],
                div(class_='col-md-5')[ up_session.meta['payload_size'] ],
            ]
        )

    if up_session.payload_verified():
        info_panel.add(
            row()[
                div(class_='col-md-3')[ span(class_='pull-right')['FSA file count :'] ],
                div(class_='col-md-5')[ up_session.meta['payload_count'] ],
            ]
        )

        info_panel.add( div(id="payload_error_report") )
    return info_panel


def get_payload_bar(up_session, request):

    if not up_session.has_payload():
        html = row()[
            p('Please upload archived file (zip, tgz, tar.gz) containing FSA files'),
            span(class_="btn btn-primary fileinput-button")[
                span('Select and upload FSA archived file'),
                input(id='dataupload', type='file', name='files[]'),
            ]
        ]

    elif not up_session.payload_verified():
        html = row()[
            p()[
                #span(id='verifypayload', class_='btn btn-info')[
                #    'Verify assay file'
                #],
                #'to continue', br(),
                span(id='verifypayload', class_='btn btn-primary')[
                    'Continue to verify the uploaded archive file'
                ], br(),
                span(class_="btn btn-default fileinput-button")[
                    span('Change/replace the uploaded archive file'),
                    input(id='dataupload', type='file', name='files[]')
                ],
            ]
        ]

    else:
        html = row()[
            p()[
                span( a( id='gettemplatefile', class_='btn btn-default', target='_blank',
                        href=request.route_url('genaf.uploadmgr-template', id=up_session.get_sesskey())
                    )[
                     'Get CSV template for FSA info file'
                     ] ),
                br(),
                span(class_="btn btn-default fileinput-button")[
                    span('Change/replace the uploaded archive file'),
                    input(id='dataupload', type='file', name='files[]')
                ],
            ]
        ]

    code = '''
    'use strict';

    $('#dataupload').fileupload({
        url: '%(url)s',
        dataType: 'json',
        maxChunkSize: 1000000,
        done: function (e, data) {
            get_main_panel();
        },
        progressall: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            $('#fileprogress .progress-bar').css('width', progress + '%%');
        },
        start: function (e) {
            $('#fileprogress .progress-bar').css('width','0%%');
            $('#fileprogress').show();
        },
        stop: function(e) {
            $('#fileprogress').hide();
        }
    }).prop('disabled', !$.support.fileInput)
        .parent().addClass($.support.fileInput ? undefined : 'disabled');
    ''' % dict( url = request.route_url("genaf.uploadmgr-uploaddata", id = up_session.sesskey) )

    if 'verifypayload' in html:
        code += '''

    $('#verifypayload').click( function() {
        $.getJSON( "%(url)s", { _method: 'verifypayload' },
            function(data) { show_main_panel(data); } );
        return false;
    });

    ''' % dict( url = request.route_url('genaf.uploadmgr-rpc', id=up_session.sesskey) )


    return (html, code)


def get_metaassay_info(up_session, request):

    if not up_session.payload_verified():
        return ''

    info_panel = div()
    if up_session.has_metaassay():
        info_panel.add(
            row()[
                div(class_='col-md-3')[ span(class_='pull-right')['FSA info file :'] ],
                div(class_='col-md-5')[ up_session.meta['infofile'] ],
            ],
            row()[
                div(class_='col-md-3')[ span(class_='pull-right')['File size :'] ],
                div(class_='col-md-5')[ up_session.meta['infofile_size'] ],
            ]
        )

        if up_session.metaassay_verified():
            info_panel.add(
                row()[
                    div(class_='col-md-3')[ span(class_='pull-right')['FSA info count :'] ],
                    div(class_='col-md-5')[ up_session.meta['infofile_count'] ],
                ]
            )

        info_panel.add( div(id="infofile_error_report") )


    return info_panel


def get_metaassay_bar(up_session, request):

    html = ''
    if up_session.metaassay_verified():
        html = row()[
            p()[
                a(href=request.route_url('genaf.uploadmgr-save', id=up_session.sesskey))[
                        span(class_='btn btn-primary')[ 'Continue to process FSA files' ]
                ],
                br(),
                span(class_="btn btn-default fileinput-button")[
                    span('Change/replace the uploaded FSA info file'),
                    input(id='infoupload', type='file', name='files[]')
                ],
            ]
        ]

    elif up_session.has_metaassay():
        html = row()[
            p()[
                span(id='verifymetaassay', class_='btn btn-primary')[
                    'Continue to verify FSA info file'
                ],
                br(),
                span(class_="btn btn-default fileinput-button")[
                    span('Change/replace the uploaded FSA info file'),
                    input(id='infoupload', type='file', name='files[]')
                ],
            ]
        ]

    elif up_session.payload_verified():

        html = row()[
            span(class_="btn btn-primary fileinput-button")[
                span('Continue to upload FSA info file (CSV or tab-delimited)'),
                input(id='infoupload', type='file', name='files[]'),
            ],
            br(), br(),
        ]

    code = '''
    'use strict';

    $('#infoupload').fileupload({
        url: '%(url)s',
        dataType: 'json',
        maxChunkSize: 1000000,
        done: function (e, data) {
            get_main_panel();
        },
        progressall: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            $('#fileprogress .progress-bar').css('width', progress + '%%');
        },
        start: function (e) {
            $('#spinner').hide();
            $('#fileprogress .progress-bar').css('width','0%%');
            $('#fileprogress').show();
        },
        stop: function(e) {
            $('#fileprogress').hide();
        }
    }).prop('disabled', !$.support.fileInput)
        .parent().addClass($.support.fileInput ? undefined : 'disabled');
    ''' % dict( url = request.route_url("genaf.uploadmgr-uploadinfo", id = up_session.sesskey) )

    if html and 'verifymetaassay' in html:
        code += '''

    $('#verifymetaassay').click( function() {
        $.getJSON( "%(url)s", { _method: 'verifymetaassay' },
            function(data) { show_main_panel(data); } );
        return false;
    });

    ''' % dict( url = request.route_url('genaf.uploadmgr-rpc', id=up_session.sesskey) )


    return (html, code)



@roles( PUBLIC )
def edit(request):
    raise NotImplementedError('PROG/ERR - Not implemented!')


@roles( PUBLIC )
def save(request):

    sesskey = request.matchdict.get('id')
    uploader_session = UploaderSession( sesskey = sesskey )

    if not uploader_session.is_authorized( request.user ):
        raise error_page('You are not authorized to view this session')

    if not asbool( request.registry.settings.get('genaf.concurrent.upload', 'false') ):
        # NOTE: set the above condition to True for non-multiprocess flow
        result = uploader_session.upload_payload()
        assay_no, err_log = result

    if sesskey in commit_procs:

        # check whether we have done or not
        procid = commit_procs[sesskey]
        procunit = getproc(procid)
        if procunit.status in [ 'D', 'U' ]:
            seconds = 0
            if procunit.exc:
                msg = div()[ p('Uploading failed. Please see the following error and log:'),
                                p( procunit.exc ),
                    ]

                result = procunit.result

                # NOTE: uncomment these 2 lines for debugging the exception
                #if result is None:
                #    raise procunit.exc

                if result and result[1]:
                    msg.add( div()[ p( *result[1] ) ] )

            else:
                result = procunit.result
                msg = div()[ p('Uploading finished.'),
                             p('Total uploaded FSA file(s): %d' % result[0] ),
                             p()[ a(href=request.route_url('genaf.batch-view',
                                        id = uploader_session.meta['batch_id']))[
                                            span(class_='btn btn-success')[ 'Continue' ]
                                        ]
                            ]
                    ]
                uploader_session.clear()
            del commit_procs[sesskey]
        else:
            # XXX: need to check whether the process is still running or stopped
            seconds = 10
            msg = div()[ p('Output: %s' % procunit.ns.cout),
                        p('Processing...')
                ]

        #return dict(html = str( p('Processing') ), status=True)

    else:

        with glock:
            procid, msg = subproc( request.user.login, uploader_session.rootpath,
                                mp_commit_payload, request.registry.settings,
                                sesskey, request.user.login, request.user.id)
            commit_procs[sesskey] = procid

        msg = div()[ p('Submitting...') ]
        seconds = 10


    batch_code = uploader_session.meta['batch']

    return render_to_response('genaf:templates/uploadmgr/save.mako',
            {   'msg':   msg,
                'batch_code': batch_code,
                'seconds': seconds,
            }, request = request )



@roles( PUBLIC )
def action(request):
    pass


@roles( PUBLIC )
def uploaddata(request):
    """ this function has been configured to return JSON, converted automatically from dict """

    sesskey = request.matchdict.get('id')
    uploader_session = UploaderSession( sesskey = sesskey )

    if not uploader_session.is_authorized( request.user ):
        raise error_page('You are not authorized to view this session')


    filestorage = request.POST.get('files[]')
    filename = os.path.basename(filestorage.filename)
    current_size, total = uploader_session.add_file(filename, filestorage, request)
    if current_size == total:
        # the last chunk
        uploader_session.meta['payload'] = filename
        uploader_session.meta['payload_size'] = total
        uploader_session.meta['payload_count'] = -1
        uploader_session.meta['infofile'] = ''
        uploader_session.meta['infofile_count'] = -1
        uploader_session.save_metadata()

    cerr('Uploaded data for %s with %d/%d bytes!' % (filename, current_size, total))
    return []


@roles( PUBLIC )
def uploadinfo(request):

    sesskey = request.matchdict.get('id')
    uploader_session = UploaderSession( sesskey = sesskey )

    if not uploader_session.is_authorized( request.user ):
        raise error_page('You are not authorized to view this session')


    filestorage = request.POST.get('files[]')
    filename = os.path.basename(filestorage.filename)
    current_size, total = uploader_session.add_file(filename, filestorage, request)
    if current_size == total:
        # the last chunk
        uploader_session.meta['infofile'] = filename
        uploader_session.meta['infofile_size'] = total
        uploader_session.meta['infofile_count'] = -1
        uploader_session.save_metadata()

    return []


@roles( PUBLIC )
def rpc(request):
    """ this function return JSON: true or false
    """

    sesskey = request.matchdict.get('id')
    uploader_session = UploaderSession( sesskey = sesskey )

    if not uploader_session.is_authorized( request.user ):
        return dict( html = p('You are not authorized to view this session') )

    if request.params.get('_method','') == 'verifypayload':

        assay_no, err_log = uploader_session.verify_datafile()
        html, code = compose_mainpanel(uploader_session, request)
        if err_log:
            html.get('payload_error_report').add( div()[ err_log ] )
        uploader_session.save_metadata()
        return dict( html = str(html), code = code )

    if request.params.get('_method','') == 'verifymetaassay':

        err_log = None
        try:
            assay_no, err_log = uploader_session.upload_payload(dry_run=True)
        except RuntimeError:
            exc_info = sys.exc_info()
            if err_log:
                err_log.append( 'Exception %s : %s' % (str(exc_info[0]), exc_info[1]) )
            else:
                err_log = [ 'Exception %s : %s' % (str(exc_info[0]), exc_info[1]) ]
            get_dbhandler().session().rollback()

        html, code = compose_mainpanel(uploader_session, request)

        if err_log:
            html.get('infofile_error_report').add(
                    div()[ 'Error message:'],
                    pre()[ '\n'.join( err_log ) ]
            )
        uploader_session.save_metadata()
        return dict( html = str(html), code = code )

    return dict( html='', code='' )


@roles( PUBLIC)
def template(request):

    sesskey = request.matchdict.get('id')
    uploader_session = UploaderSession( sesskey = sesskey )

    if not uploader_session.is_authorized( request.user ):
        raise error_page('You are not authorized to view this session')

    resp = Response()
    resp.content_type = 'text/plain'
    resp.text = uploader_session.get_template().read()
    resp.content_disposition = 'attachment; filename="template.txt"'

    return resp



## prototype multiprocessing stuff

def mp_commit_payload(settings, sesskey, login, user_id, ns):
    """ this function will be started in different process, so it must initialize
        everything from scratch, including database connection
    """

    pid = os.getpid()

    cerr('mp_commit_payload()[%d]: connecting to db' % pid)
    dbh = get_dbhandler_notsafe()
    if dbh is None:
        dbh = get_dbhandler(settings)
    dbh.session().global_user = dbh.get_user(user_id)

    uploader_session = UploaderSession( sesskey = sesskey)

    with transaction.manager:
        cerr('mp_commit_payload()[%d]: processing' % pid)
        result = uploader_session.upload_payload( comm = ns)

    dbh.session().global_user = None

    return result


