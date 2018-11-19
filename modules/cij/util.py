"""
    Miscellaneous utilities
"""
from __future__ import print_function
from subprocess import Popen, PIPE
import os
import re
import cij


def expand_path(path):
    """Expands variables from the given path and turns it into absolute path"""

    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def regex_find(pattern, content):
    """Find the given 'pattern' in 'content'"""

    find = re.findall(pattern, content)
    if len(find) == 0:
        cij.err("pattern <%r> is invalid, no matched result!" % pattern)
        cij.err("content: %r" % content)
        return ''

    elif len(find) >= 2:
        cij.err("pattern <%r> is too simple, matched result more than 2!" % pattern)
        cij.err("content: %r" % content)
        return ''

    return find[0]


def execute(cmd=None, shell=True, echo=True):
    """
    Execute the given 'cmd'

    @returns (rcode, stdout, stderr)
    """
    if echo:
        cij.emph("cij.util.execute: shell: %r, cmd: %r" % (shell, cmd))

    rcode = 1
    stdout, stderr = ("", "")

    if cmd:
        if shell:
            cmd = " ".join(cmd)

        proc = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=shell, close_fds=True)
        stdout, stderr = proc.communicate()
        rcode = proc.returncode

    if rcode and echo:
        cij.warn("cij.util.execute: stdout: %s" % stdout)
        cij.err("cij.util.execute: stderr: %s" % stderr)
        cij.err("cij.util.execute: rcode: %s" % rcode)

    return rcode, stdout, stderr
