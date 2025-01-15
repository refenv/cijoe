"""
Setup a batch of self-hosted GitHub Action Runners

* This script will register 'gha.runner.count' number of GitHub Action runners
* Each runner will have 'gha.runner.labels' associated
* Each runner will be named e.g. 'gha.runner.nameprefix-12'
* The runners will live in 'gha.runner.home / runners / gha.runner.nameprefix-12'

Ensure that the system has docker, qemu, and a user 'ghar' exists::

    adduser ghar
    usermod -aG sudo ghar
    usermod -aG libvirt ghar
    usermod -aG docker ghar

Before running, then the environment variable::

    GHA_RUNNER_TOKEN

Below is an example of the configuration items that this script uses::

    [gha.runner]
    token = "your_secret_runner_token_set_here_or_env"
    url.repository = "https://github.com/safl/spdk-community-ci"
    home = "/opt/gha"
    nameprefix = "qemu-host"
    count = 10
    labels = ["qemuhost"]
"""

import logging as log
import os
import sys
from pathlib import Path


def main(args, cijoe):
    runner = cijoe.getconf("gha.runner", {})

    url = runner.get("url", {}).get("repository", None)
    user = runner.get("user", None)
    home = runner.get("home", None)
    count = runner.get("count", None)
    labels = runner.get("labels", None)
    nameprefix = runner.get("nameprefix", None)
    token = os.getenv("GHA_RUNNER_TOKEN", runner.get("token", None))

    if token is None:
        log.error("Could not run setup, GHA_RUNNER_TOKEN not set")
        return 1
    if None in [url, home, count, labels, nameprefix]:
        log.error(f"missing or invalid config gha.runner({runner})")
        return 1

    labels = ",".join(labels)
    for number in range(int(count)):
        name = f"{nameprefix}{number:02d}"
        rdir = f"{home}/runners/{name}"
        log.debug(f"Installing runner {name} at {rdir}")

        for cmd in [
            f"mkdir {rdir}/",
            f"cp -r {home}/ghar/. {rdir}/.",
        ]:
            err, _ = cijoe.run(cmd)
            if err:
                log.error(f"failed copying runner err({err})")
                return err

        err, _ = cijoe.run(f"chown -R {user}:{user} .", cwd=rdir)
        if err:
            log.error(f"failed 'chown -R {user}:{user} .' in {rdir} err({err})")
            return err

        err, _ = cijoe.run(
            f"su {user} -c "
            '"./config.sh --unattended '
            f'--url {url} --token {token} --labels {labels} --name {name}"',
            cwd=rdir,
        )
        if err:
            log.error(f"failed to configure runner err({err})")
            return err

        for cmd in [
            "sudo ./svc.sh install",
            "sudo ./svc.sh start",
            "sudo ./svc.sh status",
        ]:
            err, _ = cijoe.run(cmd, cwd=rdir)
            if err:
                log.error(f"cmd({cmd}), err({err})")
                return err

    return err
