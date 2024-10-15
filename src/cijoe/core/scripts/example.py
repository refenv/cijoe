from argparse import Namespace

from cijoe.cli.cli import cli_interface
from cijoe.core.command import Cijoe


def main(args: Namespace, cijoe: Cijoe, step: dict):
    err, state = cijoe.run("echo 'Hello World!'")
    if "Hello" not in state.output():
        return 1
    return err


if __name__ == "__main__":
    cli_interface(__file__)
