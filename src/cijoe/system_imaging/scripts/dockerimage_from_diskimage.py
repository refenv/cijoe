#!/usr/bin/env python3
"""
Create a Docker image using a disk image
========================================

This will produce docker images for all the system images described in config. section:

* ``system_imaging.collection``

You can reduce this by providing a glob expression as input to the script via workflow.

Tools
-----

* docker
* guestmount / guestumount
* ...

Todo
----

Add glob-expression as input argument

Retargetable: False
-------------------
"""
from cijoe.qemu.wrapper import Guest


def main(args, cijoe, step):
    """Create a docker image using the content of a .qcow2 image"""

    return 0
