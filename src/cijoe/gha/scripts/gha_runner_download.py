"""
Download and unpack the GitHub Action Runner

* This script will download GitHub Action Runner from 'gha.runner.url'
* Unpack the GitHub Action to 'gha.runner.home / ghar' associated

Below is an example of the configuration items that this script uses::

    [gha.runner]
    url = "https://github.com/actions/runner/releases/download/v2.319.1/actions-runner-linux-x64-2.319.1.tar.gz"
    home = "/opt/gha"
"""

import sys
from pathlib import Path
import requests

om cijoe.cli.cli import cli_interface


def url_to_latest_runner_on_x86():

    tag_name = requests.get(
        "https://api.github.com/repos/actions/runner/releases/latest"
    ).json()["tag_name"]

    return f"https://github.com/actions/runner/releases/download/{latest_version}/"
        f"actions-runner-linux-x64-{latest_version}.tar.gz"


def main(args, cijoe, step):

    runner = cijoe.config.options.get("gha", {}).get("runner", {})

    url = runner.get("url", {}).get("download", None)
    home = runner.get("home", None)
    if None in [url, home]:
        return 1

    for cmd in [
        f"mkdir -p {home}/ghar",
        f"mkdir -p {home}/runners",
        f"curl -o {home}/ghar.tar.gz -L {url}",
        f"tar xzf {home}/ghar.tar.gz -C {home}/ghar",
    ]:
        err, _ = cijoe.run(cmd)
        if err:
            return err

    return 0


if __name__ == "__main__":
    cli_interface(__file__)
