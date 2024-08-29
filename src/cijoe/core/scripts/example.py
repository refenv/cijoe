from cijoe.cli.cli import cli_interface

def main(args, cijoe, step):
    err, state = cijoe.run("echo 'Hello World!'")
    if "Hello" not in state.output():
        return 1
    return err

if __name__ == "__main__":
    cli_interface(__file__)