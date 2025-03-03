"""
Linux Custom Kernel as Debian Package
=====================================

There are a myriad of ways to build and install a custom Linux kernel. This worklet
builds it as a Debian package. The generated .deb packages are stored in
cijoe.output_path.

Retargetable: False
-------------------

It is intended to be run "locally" since, currently the collection of the generated
.debs are not retrieved via cijoe.get(), doing so would make it retargetable.
"""

import logging as log
from argparse import ArgumentParser, _StoreAction
from pathlib import Path


def add_args(parser: ArgumentParser):
    class StringToBoolAction(_StoreAction):
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, values == "true")

    parser.add_argument(
        "--local_version",
        type=str,
        default="custom",
        help="Path to local version of kdebs",
    )
    parser.add_argument(
        "--run_local",
        choices=["true", "false"],
        default=True,
        action=StringToBoolAction,
        help="Whether or not to execute in the same environment as 'cijoe'.",
    )


def main(args, cijoe):
    """Configure, build and collect the build-artifacts"""

    path = cijoe.getconf("linux.repository.path")
    if not path:
        log.error("missing config: linux.repository.path")
        return 1

    repos = Path(path).resolve()
    err, _ = cijoe.run(f"[ -d {repos} ]")
    if err:
        return err

    run = cijoe.run_local if args.run_local else cijoe.run

    commands = [
        "[ -f .config ] && rm .config || true",
        "yes " " | make olddefconfig",
        "./scripts/config --disable CONFIG_DEBUG_INFO",
        "./scripts/config --disable SYSTEM_TRUSTED_KEYS",
        "./scripts/config --disable SYSTEM_REVOCATION_KEYS",
        f"yes '' | make -j$(nproc) bindeb-pkg LOCALVERSION={args.local_version}",
        f"mkdir -p {cijoe.output_path}/artifacts/linux",
        f"mv ../*.deb {cijoe.output_path}/artifacts/linux",
        f"mv ../*.changes {cijoe.output_path}/artifacts/linux",
        f"mv ../*.buildinfo {cijoe.output_path}/artifacts/linux",
    ]
    for cmd in commands:
        err, _ = run(cmd, cwd=str(repos))
        if err:
            return err

    return 0
