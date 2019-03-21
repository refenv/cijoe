"""
    Environment for DMESG
"""
# pylint: disable=E0012,R0205
from threading import Thread
import cij.ssh
import cij.util
import cij


def env():
    """Verify FIO variables and construct exported variables"""

    if cij.ssh.env():
        cij.err("cij.dmesg.env: invalid SSH environment")
        return 1
    return 0


class Job(object):
    """Class of DMESG job"""

    def __init__(self, fout):
        self.__thread = None
        self.__prefix = ["dmesg", "-w", "-T"]
        self.__suffix = [">>", fout]

    def __run(self, shell=True, echo=True):
        """Run DMESG job"""

        if env():
            return 1

        cij.emph("cij.dmesg.start: shell: %r, cmd: %r" % (shell, self.__prefix + self.__suffix))

        return cij.ssh.command(self.__prefix, shell, echo, self.__suffix)

    def start(self):
        """Start DMESG job in thread"""

        self.__thread = Thread(target=self.__run, args=(True, False))
        self.__thread.setDaemon(True)
        self.__thread.start()

    def terminate(self):
        """Terminate DMESG job"""

        if self.__thread:
            cmd = ["who am i"]
            status, output, _ = cij.util.execute(cmd, shell=True, echo=True)
            if status:
                cij.warn("cij.dmesg.terminate: who am i failed")
                return 1

            tty = output.split()[1]

            cmd = ["pkill -f '{}' -t '{}'".format(" ".join(self.__prefix), tty)]
            status, _, _ = cij.util.execute(cmd, shell=True, echo=True)
            if status:
                cij.warn("cij.dmesg.terminate: pkill failed")
                return 1

            self.__thread.join()
            self.__thread = None

        return 0
