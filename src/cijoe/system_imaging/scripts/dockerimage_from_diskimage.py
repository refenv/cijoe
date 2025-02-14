#!/usr/bin/env python3
"""
Create docker image using a disk image
======================================

This will produce dockers images for all the system images described in config. section:

* ``system_imaging.images``

You can reduce this by providing a case-incensitive fnmatch pattern as input to the
script via workflow, such as these::

    # This will build all images
    with:
      pattern: "*"

    # This will build all those starting with debian
    with:
      pattern: "debian*"

Retargetable: False
-------------------

This script only runs on the iniator; due to the use of 'shutil', 'download' etc.
"""
import logging as log
import shutil
from argparse import ArgumentParser
from fnmatch import fnmatch
from pathlib import Path

from cijoe.core.misc import download
from cijoe.core.resources import get_resources


def add_args(parser: ArgumentParser):
    parser.add_argument("--pattern", type=str, help="Pattern for image names to build")


def dockerimage_from_diskimage(cijoe, image):
    resources = get_resources()

    err, state = cijoe.run_local("mktemp -d")  # Create temporary directory
    if err:
        log.error("Failed creating workdir")
        return

    workdir = Path(state.output().strip())
    mountpoint = workdir / "mount"

    shutil.copyfile(
        str(resources.get("auxiliary", {}).get("system_imaging.Dockerfile").path),
        str(workdir / "Dockerfile"),
    )
    shutil.copyfile(
        str(resources.get("auxiliary", {}).get("system_imaging.dockerignore").path),
        str(workdir / ".dockerignore"),
    )

    err, _ = cijoe.run_local(f'mkdir -p "{mountpoint}"')

    commands = [
        f"guestmount -a {image['disk']['path']} -i --ro {mountpoint}",
        f"docker build -t {image['docker']['name']}:{image['docker']['tag']} -f {workdir}/Dockerfile {mountpoint}",
        f"guestunmount {mountpoint}",
    ]
    for command in commands:
        err, _ = cijoe.run_local(command)
        if err:
            log.error(f"command({command}); err({err})")
            return err

    cijoe.run_local(f'echo "Needs cleanup!" && find {workdir}')
    cijoe.run_local(
        f'echo "Run with: docker run -it {image["docker"]["name"]}:{image["docker"]["tag"]} bash"'
    )

    return 0


def main(args, cijoe):
    """Create a docker image using the content of a .qcow2 image"""

    if "pattern" not in args:
        log.error("missing step-argument: with.pattern")
        return 1
    pattern = args.pattern

    log.info(f"Got pattern({pattern})")

    entry_name = "system-imaging.images"
    images = cijoe.getconf(entry_name, {})
    if not images:
        log.error(f"missing: '{entry_name}' in configuration file")
        return 1

    count = 0
    for image_name, image in cijoe.getconf("system-imaging.images", {}).items():
        if not fnmatch(image_name.lower(), pattern.lower()):
            log.info(f"image_name({image_name}); did not match pattern({pattern}")
            continue

        log.info(f"image_name({image_name}); matched pattern({pattern})")

        err = dockerimage_from_diskimage(cijoe, image)
        if err:
            log.error(f"failed dockerimage_from_diskimage(); err({err})")
            return err

        count += 1

    if not count:
        log.error(f"did not build anything, count({count}); invalid with.pattern?")
        return err

    return 0
