"""
    Monitor

    ...
"""
import logging as log
import re
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class Handler(FileSystemEventHandler):
    """Monitor workflow for creation of 'cmd*.output files"""

    def __init__(self, cmdlogs, match, log_level):
        self.cmdlogs = cmdlogs
        self.match = match
        self.log_level = log_level

    def on_created(self, event):

        path = Path(event.src_path).resolve()
        if not re.match(self.match, str(path.name)):
            return

        self.cmdlogs.append(path)
        if not self.log_level:
            return

        log.info(f"cmd.output: {path}")


class WorkflowMonitor(object):
    def __init__(self, path, log_level):
        self.path = path
        self.cmdlogs = []
        self.handler = Handler(self.cmdlogs, r"cmd_\d+\.output", log_level)
        self.observer = Observer()

    def latest_cmdlog(self):
        """Returns the last created 'cmd*.output' file; if any."""

        if not self.cmdlogs:
            return None

        return self.cmdlogs[-1]

    def start(self):
        self.observer.schedule(self.handler, self.path, recursive=True)
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()
