import logging

log = logging.getLogger(__name__)

from concurrent import futures
from threading import Lock
import multiprocessing

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

            proc = self.pool.submit( func, *args, **kwargs )
            procunit = ProcUnit(proc, uid, wd)
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

    def manager(self):
        return self._manager



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


def getmanager():
    return get_queue().manager()

