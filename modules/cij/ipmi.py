#
# ipmi.py - Script providing convenience functions for invoking ipmi
#
# Functions:
#
# ipmi.env - Sets default vars for ipmi wrapping
# ipmi.cmd <CMD> - Execute ipmitool command <CMD>
# ipmi.on    - Power on system
# ipmi.off - Power off system
# ipmi.reset - Power reset system
#
# Variables:
#
# IPMI_USER - login on server
# IPMI_PASS - password to server
# IPMI_HOST - server host
# IPMI_PORT - server port
#
import cij.util
import cij.ssh
import cij

PREFIX = "IMPI"
REQUIRED = ["USER", "PASS", "HOST", "PORT"]
EXPORTED = []


def env():
    """Verify IPMI environment"""

    ipmi = cij.env_to_dict(PREFIX, REQUIRED)

    if ipmi is None:
        ipmi["USER"] = "admin"
        ipmi["PASS"] = "admin"
        ipmi["HOST"] = "localhost"
        ipmi["PORT"] = "623"
        cij.info("ipmi.env: USER: %s, PASS: %s, HOST: %s, PORT: %s" % (
            ipmi["USER"], ipmi["PASS"], ipmi["HOST"], ipmi["PORT"]
        ))

    cij.env_export(PREFIX, EXPORTED, ipmi)

    return 0


def command(cmd):
    """Send command to ipmi"""

    env()

    ipmi = cij.env_to_dict(PREFIX, EXPORTED + REQUIRED)

    cmd = "ipmitool -U %s -P %s -H %s -p %s %s" % (
        ipmi["USER"], ipmi["PASS"], ipmi["HOST"], ipmi["PORT"], cmd)
    cij.info("ipmi.command: %s" % cmd)

    return cij.util.execute(cmd, shell=True, echo=True)


def on():
    """Target On"""

    command("power on")


def off():
    """Target Off"""

    command("power off")


def reset():
    """Target reset"""

    command("power reset")
