"""Small cross-process file lock helpers used by publish/schedule workers.

Uses stdlib only. Windows uses msvcrt byte-range locks; POSIX uses fcntl.
The lock is released by the OS if a process crashes.
"""

import contextlib
import os
import time

if os.name == "nt":
    import msvcrt
else:
    import fcntl


class _FileLock:
    def __init__(self, path, blocking=True, timeout=None):
        self.path = path
        self.blocking = blocking
        self.timeout = timeout
        self._fh = None

    def acquire(self):
        parent = os.path.dirname(os.path.abspath(self.path))
        os.makedirs(parent, exist_ok=True)
        self._fh = open(self.path, "a+b")
        # msvcrt needs at least one byte in the locked range.
        self._fh.seek(0, os.SEEK_END)
        if self._fh.tell() == 0:
            self._fh.write(b"\0")
            self._fh.flush()
        self._fh.seek(0)

        if os.name == "nt":
            mode = msvcrt.LK_LOCK if self.blocking else msvcrt.LK_NBLCK
            if self.timeout is not None and self.blocking:
                deadline = time.monotonic() + self.timeout
                while True:
                    try:
                        msvcrt.locking(self._fh.fileno(), msvcrt.LK_NBLCK, 1)
                        return True
                    except OSError:
                        if time.monotonic() >= deadline:
                            self._close()
                            return False
                        time.sleep(0.05)
            try:
                msvcrt.locking(self._fh.fileno(), mode, 1)
                return True
            except OSError:
                self._close()
                return False

        flags = fcntl.LOCK_EX
        if not self.blocking:
            flags |= fcntl.LOCK_NB
        try:
            fcntl.flock(self._fh.fileno(), flags)
            return True
        except OSError:
            self._close()
            return False

    def release(self):
        if self._fh is None:
            return
        try:
            if os.name == "nt":
                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        finally:
            self._close()

    def _close(self):
        if self._fh is not None:
            try:
                self._fh.close()
            finally:
                self._fh = None


@contextlib.contextmanager
def file_lock(path, blocking=True, timeout=None):
    """Yield True when the lock is held, False when non-blocking acquisition failed."""
    lock = _FileLock(path, blocking=blocking, timeout=timeout)
    acquired = lock.acquire()
    try:
        yield acquired
    finally:
        if acquired:
            lock.release()
