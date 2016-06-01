import logging

log = logging.getLogger(__name__)

from concurrent import futures
from threading import Lock
import multiprocessing, functools, traceback

from rhombus.lib.utils import random_string, cerr

def create_proc_path():
    while True:
        # create random proc path
        proc_path = get_proc_path()
        if not os.path.exists( proc_path ):
            # path does not exists
            os.mkdir( proc_path )
            break
    return proc_path


class ProcUnit(object):

    def __init__(self, proc, uid, wd=None):
        self.proc = proc    # future object
        self.uid = uid  # user uid
        self.wd = wd        # proc working directory
        self.time_queue = None
        self.time_start = None
        self.time_finish = None
        self.status = 'Q'
        self.output = None
        self.error = None
        self.result = None
        self.ns = None


def reraise_with_stack(func):

    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            traceback_str = traceback.format_exc(e)
            raise StandardError("Error occurred. Original traceback "
                                "is\n%s\n" % traceback_str)

    return wrapped


class ProcQueue(object):

    def __init__(self, settings, max_workers = 2, max_queue = 25):
        self._manager = multiprocessing.Manager()
        self.pool = futures.ProcessPoolExecutor(max_workers=max_workers)
        self.pool._adjust_process_count()

        self.procs = {}
        self.queue = 0
        self.max_queue = max_queue
        self.lock = Lock()

        self.settings = settings


    def submit(self, uid, wd, func, *args, **kwargs):
        with self.lock:  # can use with self.lock.acquire() ???
            if self.queue >= self.max_queue:
                raise MaxQueueError(
                    "Queue reached maximum number. Please try again in few moments")

            while True:
                procid = random_string(16)
                if procid not in self.procs:
                    break

            procunit = ProcUnit(None, uid, wd)
            procunit.ns = self.prepare_namespace()
            kwargs['ns'] = procunit.ns
            proc = self.pool.submit( func, *args, **kwargs )
            procunit.proc = proc
            self.procs[procid] = procunit
            self.queue += 1
            proc.add_done_callback( lambda x: self.callback(x, procid) )

        return (procid, "Task submitted to queue")


    def callback(self, proc, procid):
        print('callback(): procid = %s' % procid)
        status = 'D' if proc.done() else 'U'
        exc = proc.exception()
        result = proc.result() if exc is None else None

        with self.lock:  # can use with self.lock.acquire() ???
            self.queue -= 1
            procunit = self.procs[procid]
            if procunit.proc != proc:
                raise RuntimeError('FATAL PROG/ERR!')
            procunit.status = status     # set status to Stop
            procunit.exc = exc
            procunit.result = result


    def get(self, procid):
        return self.procs[procid]

    def clear(self, procid):
        del self.procs[procid]

    def manager(self):
        return self._manager

    def prepare_namespace(self):
        ns = self.manager().Namespace()
        ns.cout = ''
        ns.cerr = ''
        ns.msg = None
        ns.status = 'Q'
        ns.start_time = 0
        ns.finish_time = 0
        return ns


class PoolExecuter(futures.ProcessPoolExecutor):

    def __del__(self):
        print("DELETE THIS POOL, HOW?")
        self.__del__()


_PROC_QUEUE_ = None

def init_queue( settings, max_workers = 2, max_queue = 10 ):
    global _PROC_QUEUE_, _MANAGER_
    if _PROC_QUEUE_ is None:
        _PROC_QUEUE_ = ProcQueue( settings, max_workers, max_queue )
        log.info("Multiprocessing queue has been setup with %d process" % max_workers)
    else:
        raise RuntimeError("PROC_QUEUE has been defined!!")


def get_queue():
    global _PROC_QUEUE_
    if _PROC_QUEUE_ is None:
        raise RuntimeERror("PROG/ERR - PROC_QUEUE has not been initialized")
    return _PROC_QUEUE_


def subproc( uid, wd, func, *args, **kwargs ):
    return get_queue().submit( uid, wd, func, *args, **kwargs )


def getproc( procid ):
    return get_queue().get(procid)

def clearproc( procid ):
    return get_queue().clear(procid)


def getmanager():
    return get_queue().manager()

def estimate_time(start_time, current_time, processed, unprocessed):
    """ return string of '2d 3h 23m' """
    used_time = current_time - start_time   # in seconds
    if processed == 0:
        return 'undetermined'
    average_time = used_time / processed
    estimated = average_time * unprocessed
    cerr('Average time: %3.6f sec' % average_time)
    cerr('Estimated remaining time: %3.6f sec' % estimated)

    text = ''
    if estimated > 86400:
        text += '%dd ' % int( estimated / 86400 )
        estimated = estimated % 86400
    if estimated > 3600:
        text += '%dh ' % int( estimated / 3600 )
        estimated = estimated  % 3600
    text += '%dm' % (int( estimated / 60) + 1)

    return text
