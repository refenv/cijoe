"""
ssh.py      - Script providing operation of SSH

Functions:
    ssh.env()       - Check environment of SSH connection
    ssh.command()   - Send SSH command to TARGET
    ssh.push()      - Push file to TARGET by SSH
    ssh.pull()      - Pull file from TARGET by SSH
    ssh.wait()      - Wait for TARGET get ready until timeout
    ssh.reboot()    - Reboot TARGET and wait for TARGET get ready

Require:
    SSH_KEY         - SSH key of TARGET
    SSH_PORT        - SSH port of TARGET
    SSH_USER        - SSH user of TARGET
    SSH_HOST        - Name or IP of TARGET
    SSH_CMD_TIME    - Measure time of SSH command
    SSH_CMD_TIMEOUT - Timeout for SSH command
"""
import time
import cij.util
import cij

PREFIX = "SSH"
REQUIRED = ["USER", "HOST"]
EXPORTED = []

DEFAULTS = {"PORT": "22", "CMD_TIME": "1"}
OPTIONAL = ["CMD_TIMEOUT", "KEY"]


def env():
    """Verify SSH variables and construct exported variables"""

    ssh = cij.env_to_dict(PREFIX, REQUIRED)
    if "KEY" in ssh:
        ssh["KEY"] = cij.util.expand_path(ssh["KEY"])

    if cij.ENV.get("SSH_PORT") is None:
        cij.ENV["SSH_PORT"] = "22"
        cij.warn("cij.ssh.env: SSH_PORT was not set, assigned: %r" % (
            cij.ENV.get("SSH_PORT")
        ))

    if cij.ENV.get("SSH_CMD_TIME") is None:
        cij.ENV["SSH_CMD_TIME"] = "1"
        cij.warn("cij.ssh.env: SSH_CMD_TIME was not set, assigned: %r" % (
            cij.ENV.get("SSH_CMD_TIME")
        ))

    return 0


def command(cmd, shell=True, echo=True, suffix=None):
    """SSH: Run the given command over SSH as defined in environment"""

    if env():
        cij.err("cij.ssh.command: Invalid SSH environment")
        return 1

    prefix = []

    if cij.ENV.get("SSH_CMD_TIME") == "1":
        prefix.append("/usr/bin/time")

    if cij.ENV.get("SSH_CMD_TIMEOUT"):
        prefix.append("timeout")
        prefix.append(cij.ENV.get("SSH_CMD_TIMEOUT"))

    prefix.append("ssh")

    args = []

    if cij.ENV.get("SSH_KEY"):
        args.append("-i")
        args.append(cij.ENV.get("SSH_KEY"))

    if cij.ENV.get("SSH_PORT"):
        args.append("-p")
        args.append(cij.ENV.get("SSH_PORT"))

    args.append("@".join([cij.ENV.get("SSH_USER"), cij.ENV.get("SSH_HOST")]))

    wrapped = prefix + args + ["'%s'" % " ".join(cmd)]
    if suffix:
        wrapped += suffix

    return cij.util.execute(wrapped, shell, echo)


def push(src, dst, folder=False):
    """SSH: push data to remote linux"""

    if env():
        cij.err("cij.ssh.push: Invalid SSH environment")
        return 1

    args = []

    if cij.ENV.get("SSH_KEY"):
        args.append("-i")
        args.append(cij.ENV.get("SSH_KEY"))

    if cij.ENV.get("SSH_PORT"):
        args.append("-P")
        args.append(cij.ENV.get("SSH_PORT"))

    if folder:
        args.append("-r")

    target = "%s:%s" % ("@".join([cij.ENV.get("SSH_USER"), cij.ENV.get("SSH_HOST")]), dst)
    wrapped = ["scp", " ".join(args), src, target]

    return cij.util.execute(wrapped, shell=True, echo=True)


def pull(src, dst, folder=False):
    """SSH: pull data from remote linux"""

    if env():
        cij.err("cij.ssh.pull: Invalid SSH environment")
        return 1

    args = []

    if cij.ENV.get("SSH_KEY"):
        args.append("-i")
        args.append(cij.ENV.get("SSH_KEY"))

    if cij.ENV.get("SSH_PORT"):
        args.append("-P")
        args.append(cij.ENV.get("SSH_PORT"))

    if folder:
        args.append("-r")

    target = "%s:%s" % ("@".join([cij.ENV.get("SSH_USER"), cij.ENV.get("SSH_HOST")]), src)
    wrapped = ["scp", " ".join(args), target, dst]

    return cij.util.execute(wrapped, shell=True, echo=True)


def wait(timeout=300):
    """Wait util target connected"""

    if env():
        cij.err("cij.ssh.wait: Invalid SSH environment")
        return 1

    timeout_backup = cij.ENV.get("SSH_CMD_TIMEOUT")

    try:
        time_start = time.time()

        cij.ENV["SSH_CMD_TIMEOUT"] = "3"

        while True:
            time_current = time.time()
            if (time_current - time_start) > timeout:
                cij.err("cij.ssh.wait: Timeout")
                return 1

            status, _, _ = command(["exit"], shell=True, echo=False)
            if not status:
                break

        cij.info("cij.ssh.wait: Time elapsed: %d seconds" % (time_current - time_start))

    finally:
        if timeout_backup is None:
            del cij.ENV["SSH_CMD_TIMEOUT"]
        else:
            cij.ENV["SSH_CMD_TIMEOUT"] = timeout_backup

    return 0


def reboot(timeout=300, extra=""):
    """Reboot target"""

    if env():
        cij.err("cij.ssh.reboot: Invalid SSH environment")
        return 1

    timeout_backup = cij.ENV.get("SSH_CMD_TIMEOUT")

    try:
        time_start = time.time()
        status, last_uptime, _ = command(["/usr/bin/uptime -s"], shell=True, echo=False)
        if status:
            return 1

        cij.ENV["SSH_CMD_TIMEOUT"] = "3"
        cij.info("cij.ssh.reboot: Target: %s" % cij.ENV.get("SSH_HOST"))
        command(["reboot %s" % extra], shell=True, echo=False)

        while True:
            time_current = time.time()
            if (time_current - time_start) > timeout:
                cij.err("cij.ssh.reboot: Timeout")
                return 1

            status, current_uptime, _ = command(["/usr/bin/uptime -s"], shell=True, echo=False)
            if not status and current_uptime != last_uptime:
                break

        cij.info("cij.ssh.reboot: Time elapsed: %d seconds" % (time_current - time_start))

    finally:
        if timeout_backup is None:
            del cij.ENV["SSH_CMD_TIMEOUT"]
        else:
            cij.ENV["SSH_CMD_TIMEOUT"] = timeout_backup

    return 0
