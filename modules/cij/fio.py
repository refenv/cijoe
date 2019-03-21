"""
fio.py    - Script providing operation of fio

Classes:
    Job.import_parms()  - Import FIO parameters from dict
    Job.set_parm()      - Set FIO parameter
    Job.get_parm()      - Get FIO parameter
    Job.start()         - Start FIO in thread
    Job.join()          - Wait until FIO thread ended
    Job.result()        - Get result of FIO thread
    Job.run()           - Start FIO in foreground and return result

Require:
    cij.ssh.env()
"""
# pylint: disable=E0012,R0205
from collections import OrderedDict
from threading import Thread
import cij.ssh
import cij


def env():
    """Verify FIO variables and construct exported variables"""

    if cij.ssh.env():
        cij.err("cij.fio.env: invalid SSH environment")
        return 1
    return 0


def pkill():
    """Kill all of FIO processes"""

    if env():
        return 1

    cmd = ["ps -aux | grep fio | grep -v grep"]
    status, _, _ = cij.ssh.command(cmd, shell=True, echo=False)
    if not status:
        status, _, _ = cij.ssh.command(["pkill -f fio"], shell=True)
        if status:
            return 1
    return 0


class Threads(Thread):
    """Class of threads"""

    def __init__(self, target=None, args=()):
        Thread.__init__(self)
        self.target = target
        self.args = args
        self.output = None

    def run(self):
        """Start run thread"""

        self.output = self.target(*self.args)

    def result(self):
        """Get result of thread"""

        return self.output


class Job(object):
    """Class of FIO job"""

    def __init__(self):
        self.__thread = None
        self.__parm = OrderedDict()

    def __parse_parms(self):
        """Translate dict parameters to string"""

        args = list()
        for key, val in self.__parm.items():
            key = key.replace("FIO_", "").lower()

            if key == "runtime":
                args.append("--time_based")

            if val is None:
                args.append("--%s" % key)
            else:
                args.append("--%s=%s" % (key, val))
        return args

    def import_parms(self, args):
        """Import external dict to internal dict"""

        for key, val in args.items():
            self.set_parm(key, val)

    def set_parm(self, key, val=None):
        """
        Set parameter of FIO
        If val is None, the parameter is "--key"
        If val is not None, the parameter is "--key=val"
        """

        self.__parm[key] = val

    def get_parm(self, key):
        """Get parameter of FIO"""

        if key in self.__parm.keys():
            return self.__parm[key]

        return None

    def start(self):
        """Run FIO job in thread"""

        self.__thread = Threads(target=self.run, args=(True, True, False))
        self.__thread.setDaemon(True)
        self.__thread.start()

    def join(self, timeout=None):
        """Wait until the FIO thread terminates"""

        if self.__thread:
            self.__thread.join(timeout)

    def result(self):
        """Get result of FIO thread"""

        if self.__thread:
            return self.__thread.result()

        return None

    def run(self, shell=True, cmdline=False, echo=True):
        """Run FIO job"""

        if env():
            return 1

        cmd = ["fio"] + self.__parse_parms()
        if cmdline:
            cij.emph("cij.fio.run: shell: %r, cmd: %r" % (shell, cmd))

        return cij.ssh.command(cmd, shell, echo)
