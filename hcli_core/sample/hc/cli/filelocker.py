import os
import inspect
import portalocker

class FileLocker:
    root = os.path.dirname(inspect.getfile(lambda: None))

    def __init__(self):
        self.lockfile = self.root + "/stream.lock"
        self.lock_fd = None

    def acquire(self):
        self.lock_fd = open(self.lockfile, 'w')
        portalocker.lock(self.lock_fd, portalocker.LOCK_EX)

    def release(self):
        if self.lock_fd is not None:
            portalocker.unlock(self.lock_fd)
            self.lock_fd.close()
            self.lock_fd = None

    def __enter__(self):
        self.acquire()
        print("acquired")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        print("released")
