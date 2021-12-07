"""
    Miscellaneous utilities
"""
from __future__ import print_function
from subprocess import Popen, PIPE
import argparse
import dataclasses
import os
import re
import stat
import cij


class ExtendAction(argparse.Action):
    """Custom action, since the extend-action is not available until 3.8"""

    # pylint: disable=too-few-public-methods
    def __call__(self, parser, namespace, values, option_string=None):
        items = getattr(namespace, self.dest) or []
        items.extend(values)
        setattr(namespace, self.dest, items)


def expand_path(path):
    """Expands variables from the given path and turns it into absolute path"""

    return os.path.abspath(os.path.expanduser(os.path.expandvars(path)))


def regex_find(pattern, content):
    """Find the given 'pattern' in 'content'"""

    find = re.findall(pattern, content)
    if not find:
        cij.err("pattern <%r> is invalid, no matches!" % pattern)
        cij.err("content: %r" % content)
        return ''

    if len(find) >= 2:
        cij.err("pattern <%r> is too simple, matched more than 2!" % pattern)
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

        with Popen(
                cmd, stdout=PIPE, stderr=PIPE, shell=shell, close_fds=True
        ) as proc:
            stdout, stderr = proc.communicate()
            rcode = proc.returncode

    if rcode and echo:
        cij.warn("cij.util.execute: stdout: %s" % stdout)
        cij.err("cij.util.execute: stderr: %s" % stderr)
        cij.err("cij.util.execute: rcode: %s" % rcode)

    return rcode, stdout, stderr


def rehome(old, new, struct):
    """
    Replace all absolute paths to "re-home" it
    """
    # pylint: disable=too-many-branches

    if old == new:
        return

    if isinstance(struct, list):
        for item in struct:
            rehome(old, new, item)

    elif isinstance(struct, dict):
        for key, val in struct.items():
            if isinstance(val, (dict, list)):
                rehome(old, new, val)
            elif "conf" in key:
                continue
            elif "orig" in key:
                continue
            elif "root" in key or "path" in key:
                struct[key] = struct[key].replace(old, new)

    elif dataclasses.is_dataclass(struct):
        for key in struct.__dataclass_fields__:
            val = getattr(struct, key)
            if isinstance(val, (dict, list)) or dataclasses.is_dataclass(val):
                rehome(old, new, val)
            elif "conf" in key:
                continue
            elif "orig" in key:
                continue
            elif "root" in key or "path" in key:
                setattr(struct, key, val.replace(old, new))


def _list_dir(path, dirs, files, ext):
    for fname in os.listdir(path):
        fpath = os.path.join(path, fname)
        mode = os.stat(fpath).st_mode

        isdir = stat.S_ISDIR(mode)
        isfile = stat.S_ISREG(mode)

        dir_ = dirs and isdir
        file_ = files and isfile and (ext is None or
                                      os.path.splitext(fname)[1] == ext)

        if dir_ or file_:
            yield fpath


def list_dir(path='.', dirs=False, files=True, ext=None, recursive=False):
    """ List the contents of a directory.
    If recursive is set to True, list_dir will recurse through sub-dirs as
    well.
    Returns directories if dirs is set to True.
    Returns files if files is set True.
    Returns only files with the given extension if ext is set. Note that
    the extension includes the dot, i.e. '.jpg'.
    """
    if not recursive:
        yield from _list_dir(path, dirs, files, ext)
        return

    yield from _list_dir(path, dirs=False, files=True, ext=ext)

    for dir_ in _list_dir(path, dirs=True, files=False, ext=None):
        if dirs:
            yield dir_
        yield from list_dir(dir_, dirs, files, ext, recursive=True)
