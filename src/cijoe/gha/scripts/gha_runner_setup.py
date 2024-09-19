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

    GHAR_TOKEN

Below is an example of the configuration items that this script uses::

    [gha.runner]
    url.repository = "https://github.com/safl/spdk-community-ci"
    home = "/opt/gha"
    nameprefix = "qemu-host"
    count = 10
    labels = ["qemuhost"]
"""

import os
import sys
from pathlib import Path

from cijoe.cli.cli import cli_interface


def main(args, cijoe, step):

    token = os.getenv("GHAR_TOKEN", None)
    if token is None:
        print("GHAR_TOKEN is not set")
        return

    runner = cijoe.config.options.get("gha", {}).get("runner", {})

    url = runner.get("url", {}).get("repository", None)
    user = runner.get("user", None)
    home = runner.get("home", None)
    count = runner.get("count", None)
    labels = runner.get("labels", None)
    nameprefix = runner.get("nameprefix", None)
    if None in [url, home, count, labels, nameprefix]:
        return 1

    labels = ",".join(labels)
    for number in range(int(count)):
        name = f"{nameprefix}{number:02d}"
        rdir = f"{home}/runners/{name}"

        err, _ = cijoe.run(f"cp -r {home}/ghar {home}/runners/{name}")
        if err:
            return err

        for cmd in [
            f"./config.sh --unattended --replace "
            f"--url {url} --token {token} --labels {labels} --name {name}",
            f"./svc.sh install {user}",
            f"./svc.sh start",
            f"./svc.sh status",
        ]:
            err, _ = cijoe.run(cmd, cwd=rdir)
            if err:
                return err

    return err


if __name__ == "__main__":
    cli_interface(__file__)
