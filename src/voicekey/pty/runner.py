# src/voicekey/pty/runner.py
import os
import sys
import subprocess
import selectors
import threading
import logging
import signal
from typing import Optional

logger = logging.getLogger(__name__)

class PtyRunner:
    def __init__(self, cmd):
        self.cmd = cmd
        self.process: Optional[subprocess.Popen] = None
        self.master_fd: Optional[int] = None
        self._stop = threading.Event()

    def start(self, on_exit=None):
        # Create PTY pair
        self.master_fd, self.slave_fd = os.openpty()

        # Start subprocess in its own process group
        self.process = subprocess.Popen(
            self.cmd,
            stdin=self.slave_fd,
            stdout=self.slave_fd,
            stderr=self.slave_fd,
            preexec_fn=os.setsid,  # important for killpg
            close_fds=True,
        )

        # Parent does not need slave FD
        os.close(self.slave_fd)

        # Start output forwarding thread
        threading.Thread(target=self._forward_output, daemon=True).start()

        # Start watcher thread
        threading.Thread(
            target=self._watch_process,
            args=(on_exit,),
            daemon=True,
        ).start()

    def send(self, data: bytes):
        if self.master_fd is not None:
            try:
                os.write(self.master_fd, data)
            except OSError:
                logger.exception("Failed to write to PTY master (process may have exited)")

    def wait(self):
        if self.process:
            return self.process.wait()
        return None

    def stop(self):
        self._stop.set()

        if self.process and self.process.poll() is None:
            try:
                logger.debug("Terminating child process %s", self.process.pid)
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=2)
            except Exception:
                try:
                    logger.debug("Killing child process %s", self.process.pid)
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except Exception:
                    logger.exception("Failed to terminate/kill child process")

        if self.master_fd is not None:
            try:
                os.close(self.master_fd)
            except Exception:
                pass
            self.master_fd = None
    
    def _forward_output(self):
        sel = selectors.DefaultSelector()
        sel.register(self.master_fd, selectors.EVENT_READ)

        try:
            while not self._stop.is_set():
                events = sel.select(timeout=0.1)
                for _, _ in events:
                    try:
                        data = os.read(self.master_fd, 1024)
                    except OSError:
                        # Slave closed the PTY (child exited) -> expected
                        logger.debug("PTY slave closed, stopping forwarder")
                        return

                    if not data:
                        return

                    sys.stdout.buffer.write(data)
                    sys.stdout.buffer.flush()
        finally:
            try:
                sel.unregister(self.master_fd)
            except Exception:
                pass
    
    def _watch_process(self, on_exit):
        """
        Wait for the process to exit and notify callback.
        """
        self.process.wait()

        if on_exit:
            on_exit()