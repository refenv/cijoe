"""
Download and unpack the GitHub Action Runner

* This script will download GitHub Action Runner from 'gha.runner.url'
* Unpack the GitHub Action to 'gha.runner.home / ghar' associated

Below is an example of the configuration items that this script uses::

    [gha.runner]
    url = "https://github.com/actions/runner/releases/download/v2.319.1/actions-runner-linux-x64-2.319.1.tar.gz"
    home = "/opt/gha"
"""

import logging as log
import sys
from pathlib import Path

import requests


def url_to_latest_runner_on_x86():
    tag_name = requests.get(
        "https://api.github.com/repos/actions/runner/releases/latest"
    ).json()["tag_name"]

    return (
        f"https://github.com/actions/runner/releases/download/{tag_name}/"
        f"actions-runner-linux-x64-{tag_name[1:]}.tar.gz"
    )


def main(args, cijoe, step):
    runner = cijoe.config.options.get("gha", {}).get("runner", {})

    url = runner.get("url", {}).get("download", url_to_latest_runner_on_x86())
    home = runner.get("home", None)
    if None in [url, home]:
        log.error(f"missing or invalid config gha.runner({runner})")
        return 1

    for cmd in [
        f"mkdir -p {home}/ghar",
        f"mkdir -p {home}/runners",
        f"curl -o {home}/ghar.tar.gz -L {url}",
        f"tar xzf {home}/ghar.tar.gz -C {home}/ghar",
    ]:
        err, _ = cijoe.run(cmd)
        if err:
            log.error(f"cmd({cmd}), err({err})")
            return err

    return 0
