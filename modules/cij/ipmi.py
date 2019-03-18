"""
    ipmi.py - Script providing convenience functions for invoking ipmi

    Functions:

    ipmi.env        - Sets default vars for IPMI wrapping
    ipmi.cmd <CMD>  - Execute ipmitool command <CMD>
    ipmi.pwr_on     - Power on system
    ipmi.pwr_off    - Power off system
    ipmi.pwr_reset  - Power reset system

    Variables:

    IPMI_USER - login on server
    IPMI_PASS - password to server
    IPMI_HOST - server host
    IPMI_PORT - server port
"""
import cij.util
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


def cmd(command):
    """Send IPMI 'command' via ipmitool"""

    env()

    ipmi = cij.env_to_dict(PREFIX, EXPORTED + REQUIRED)

    command = "ipmitool -U %s -P %s -H %s -p %s %s" % (
        ipmi["USER"], ipmi["PASS"], ipmi["HOST"], ipmi["PORT"], command)
    cij.info("ipmi.command: %s" % command)

    return cij.util.execute(command, shell=True, echo=True)


def pwr_on():
    """Target On"""

    cmd("power on")


def pwr_off():
    """Target Off"""

    cmd("power off")


def pwr_reset():
    """Target reset"""

    cmd("power reset")
