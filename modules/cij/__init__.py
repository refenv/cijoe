"""
    Collection of Python utilities for CIJOE and CIJOE testing
"""
from __future__ import print_function
import os
import sys
import time

VERSION_MAJOR = 0
VERSION_MINOR = 0
VERSION_PATCH = 1
VERSION = "%d.%d.%d" % (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)

PR_EMPH_CC = "\033[0;36m"
PR_GOOD_CC = "\033[0;32m"
PR_WARN_CC = "\033[0;33m"
PR_ERR_CC = "\033[0;31m"
PR_NC = "\033[0m"

ENV = os.environ
CIJ_ECHO_TIME_STAMP = ENV.get("CIJ_ECHO_TIME_STAMP")


def get_time_stamp():
    """Get time stampe if CIJ_ECHO_TIME_STAMP is 1"""

    if CIJ_ECHO_TIME_STAMP == "1":
        return time.strftime('[%Y-%m-%d %H:%M:%S] ', time.localtime(time.time()))

    return ""


def info(txt):
    """Print, emphasized 'neutral', the given 'txt' message"""

    print("%s# %s%s%s" % (PR_EMPH_CC, get_time_stamp(), txt, PR_NC))
    sys.stdout.flush()


def good(txt):
    """Print, emphasized 'good', the given 'txt' message"""

    print("%s# %s%s%s" % (PR_GOOD_CC, get_time_stamp(), txt, PR_NC))
    sys.stdout.flush()


def warn(txt):
    """Print, emphasized 'warning', the given 'txt' message"""

    print("%s# %s%s%s" % (PR_WARN_CC, get_time_stamp(), txt, PR_NC))
    sys.stdout.flush()


def err(txt):
    """Print, emphasized 'error', the given 'txt' message"""

    print("%s# %s%s%s" % (PR_ERR_CC, get_time_stamp(), txt, PR_NC))
    sys.stdout.flush()


def emph(txt, rval=None):
    """Print, emphasized based on rval"""

    if rval is None:    # rval is not specified, use 'neutral'
        info(txt)
    elif rval == 0:     # rval is 0, by convention, this is 'good'
        good(txt)
    else:               # any other value, considered 'bad'
        err(txt)


def env_to_dict(prefix, names):
    """
    Construct dict from environment variables named: PREFIX_NAME

    @returns dict of names
    """

    env = {}
    for name in names:
        env[name] = ENV.get("_".join([prefix, name]))
        if env[name] is None:
            return None

    return env


def env_export(prefix, exported, env):
    """
    Define the list of 'exported' variables with 'prefix' with values from 'env'
    """

    for exp in exported:
        ENV["_".join([prefix, exp])] = env[exp]
