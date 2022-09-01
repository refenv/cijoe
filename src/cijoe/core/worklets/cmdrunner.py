"""
cmdrunner
=========

Executes a list of commands in the given order. Note that multi-line commands are not
support, each line or list of strings are treated as individual commands.

Retargetable: True
------------------
"""
import errno


def worklet_entry(args, cijoe, step):
    """Run commands one at a time via cijoe.run()"""

    err = 0
    if "with" not in step and "commands" not in step["with"]:
        return errno.EINVAL

    for cmd in step["with"]["commands"]:
        err, state = cijoe.run(cmd)
        if err:
            break

    return err
