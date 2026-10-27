"""
Check the tools of a target
===========================

Checks that the target has the tools a task needs, at the versions it needs,
and records what it has as facts, 'targets.<target>.tools.<tool>': 'found',
and when found its 'path' and 'version'. The configuration describes a tool
once:

    [tools.fio]
    version = "fio --version"   # how to ask; default: '<tool> --version'
    min = "3.38"                # the least version; default: any

and 'tools' names those a step checks, by default every one the
configuration describes; a tool it names that the configuration does not is
checked with the defaults. A tool whose facts already satisfy what is needed is
not asked again, unless 'refresh'. The step fails, naming every tool that is
missing or too old, when the target lacks any.

A script that needs tools declares them as 'TOOLS', and cijoe checks those
before it runs the script; see cijoe.core.tools.

Retargetable: True
------------------
"""

import errno
import logging as log
from argparse import ArgumentParser

from cijoe.core.tools import check, configured


def add_args(parser: ArgumentParser):
    parser.add_argument(
        "--tools",
        type=str,
        default=None,
        help="Comma-separated tools to check; default: those '[tools]' describes.",
    )
    parser.add_argument(
        "--target_name",
        type=str,
        default=None,
        help="The transport of the target to check; default: cijoe's.",
    )
    parser.add_argument(
        "--refresh",
        type=str,
        default="false",
        help="Ask the target even about tools its facts already describe.",
    )


def main(args, cijoe):
    """Check the target's tools, and record them as facts"""

    target = args.target_name or cijoe.default_target
    if target not in cijoe.transports:
        log.error(f"no target({target}); known: {', '.join(cijoe.transports)}")
        return errno.EINVAL

    tools = configured(cijoe)
    if tools is None:
        log.error("[tools] is not a table: describe each tool as [tools.<tool>]")
        return errno.EINVAL
    if args.tools:
        names = [t.strip() for t in args.tools.split(",") if t.strip()]
    else:
        names = list(tools.keys())
    if not names:
        log.error("no tools to check: give 'tools' or describe them as '[tools]'")
        return errno.EINVAL

    refresh = str(args.refresh).lower() in ("true", "1", "yes")
    problems = check(cijoe, target, {name: None for name in names}, refresh)
    if problems:
        log.error(f"target({target}) lacks:\n  " + "\n  ".join(problems))
        return errno.ENOENT

    return 0
