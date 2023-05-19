#!/usr/bin/env python
"""
Monitor a directory for creation and modification of cijoe command-output files
and dump their content to stdout. It is intentional that this should be
executed standalone like so::

    cijoe -m

That is, a command/process to start and have running in a terminal across
multiple invocations of cijoe. Thereby separating the output from the
instrumentation.

.. note::
    This is a quick-n-dirty prototype. Not much error-handling is done here, so
    expect crashing in case of non-printable characters and potential
    un-expected behavior.

.. note::
    In a perfect world, then this would not need to be implemented, instead
    tail / xtail could be used. However, those excellent tools are just not
    readily available everywhere.
"""
import logging as log
import queue
import re
import threading
import time
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


def worker(monitor):
    """Worker dumping the contents of cijoe command-output files"""

    bytes_read = {}

    while True:
        task, path = monitor.workq.get()

        ident = str(path)  # Output identifier
        if ident not in bytes_read:
            bytes_read[ident] = 0

        if task == "print":
            with path.open(
                "r"
            ) as cmdlog:  # Read, update stats, inform, dump, and update stats
                cmdlog.seek(bytes_read[ident])
                buf = cmdlog.read()
                nbytes = len(buf)
                log.info(
                    f"# cijoe.monitor: output({path})@{bytes_read[ident]}+{nbytes}"
                )
                print(buf, end="")
                monitor.dumped_at = time.time()
                bytes_read[ident] += nbytes

        monitor.workq.task_done()


class CommandOutputHandler(FileSystemEventHandler):
    """
    Handler filtering out creation and modification events for cijoe
    command-output files, forwarding these events to the worker to dump the
    file-content.
    """

    REGEX_CMDLOG_FILENAME = r"cmd_\d+\.output"

    def __init__(self, workq):
        self.workq = workq

    def skipevent(self, event):
        path = Path(event.src_path).resolve()
        if not re.match(CommandOutputHandler.REGEX_CMDLOG_FILENAME, str(path.name)):
            return True
        if event.is_directory:
            return True

        return False

    def on_created(self, event):
        """When a file is created, then reset the meta-data"""

        if self.skipevent(event):
            return

        self.workq.put(("reset", Path(event.src_path)))

    def on_modified(self, event):
        """When a file is modified, then dump the additions to stdout"""

        if self.skipevent(event):
            return

        self.workq.put(("print", Path(event.src_path)))


class WorkflowMonitor(object):
    """
    Monitors a directory path, recursively, for the creation and modification
    of cijoe commmand-output files for the purpose of dumping the file-content
    to stdout.
    """

    def __init__(self, path: Path = None):
        if path is None:
            path = Path.cwd()

        self.path = path
        self.observer = Observer()
        self.dumped_at = None
        self.dumped_notify = 3.0

        self.workq = queue.Queue()
        self.workt = threading.Thread(
            kwargs={"monitor": self}, target=worker, daemon=True
        )

    def start(self):
        log.info(f"# cijoe.monitor: Recursively observing path({self.path})")

        self.workt.start()

        self.observer.schedule(
            CommandOutputHandler(self.workq), str(self.path), recursive=True
        )
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

        self.workt.stop()

    def join(self):
        try:
            while True:
                time.sleep(1)

                if self.dumped_at is None:
                    log.info(
                        "# cijoe.monitor: no command-output yet; start your workflow?"
                    )
                    continue

                when = self.dumped_at
                seconds = time.time() - when
                if seconds >= self.dumped_notify:
                    log.info(
                        f"# cijoe.monitor: no output for seconds({seconds:.2f}) .."
                    )
                    if seconds >= self.dumped_notify * 2:
                        log.info(
                            "# cijoe.monitor: .. possibly just a silent command .."
                        )
                    if seconds >= self.dumped_notify * 3:
                        log.info("# cijoe.monitor: .. or, workflow is finished ..")
                    if seconds >= self.dumped_notify * 4:
                        log.info(
                            "# cijoe.monitor: .. run 'cijoe -p' to see the progress"
                        )

        except KeyboardInterrupt:
            pass
