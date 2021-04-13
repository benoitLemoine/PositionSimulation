from multiprocessing import Process, Queue


def _worker(function, args, queue):
    ret = function(*args)
    queue.put(ret)


class AsyncTask:
    def __init__(self, function, args):
        self._function = function
        self._args = args

        self._queue = Queue()
        self._process = Process(target=_worker, args=(self._function, self._args, self._queue))

    def start(self):
        self._process.start()

    def get(self):
        return self._queue.get()

    def is_alive(self):
        return self._process.is_alive()
