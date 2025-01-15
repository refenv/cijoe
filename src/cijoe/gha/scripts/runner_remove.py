"""
Unregister a batch of self-hosted GitHub Action Runners

* This will stop runner-services, uninstall and remove them

Below is an example of the configuration items that this script uses::

    [gha.runner]
    home = "/opt/gha"
    nameprefix = "qemu-host"
    count = 10

Additionally, then ensure that the following environment variables are set::

    GHA_RUNNER_TOKEN
"""

import logging as log
import os
import sys
from pathlib import Path


def main(args, cijoe):
    runner = cijoe.getconf("gha.runner", {})

    home = runner.get("home", None)
    user = runner.get("user", None)
    count = runner.get("count", None)
    nameprefix = runner.get("nameprefix", None)
    token = os.getenv("GHA_RUNNER_TOKEN", runner.get("token", None))

    if None in [home, count, nameprefix, token]:
        log.error(f"missing or invalid config gha.runner({runner})")
        return 1

    errors = []
    for number in range(int(count)):
        name = f"{nameprefix}{number:02d}"
        rdir = f"{home}/runners/{name}"

        for cmd in [
            "sudo ./svc.sh stop",
            "sudo ./svc.sh uninstall",
        ]:
            err, _ = cijoe.run(cmd, cwd=rdir)
            if err:
                log.error(f"cmd({cmd}), err({err})")
                errors.append(err)

        err, _ = cijoe.run(
            f"su {user} -c" f'"./config.sh remove --token {token}"', cwd=rdir
        )
        if err:
            log.error(f"failed to remove runner err({err})")
            return err

    return errors[0] if errors else 0
