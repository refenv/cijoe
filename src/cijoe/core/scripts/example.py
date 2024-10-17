from argparse import Namespace

from cijoe.core.command import Cijoe


def main(args: Namespace, cijoe: Cijoe, step: dict):
    err, state = cijoe.run("echo 'Hello World!'")
    if "Hello" not in state.output():
        return 1
    return err
