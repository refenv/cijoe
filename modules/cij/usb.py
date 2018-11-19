"""
usb.py      - Script providing operation for USB-RELAY

Classes:
    Relay.power_on  - 230v power on
    Relay.power_off - 230v power off
    Relay.power_btn - Target's power button

Require:
    USB_RELAY           - USB-RELAY is connect to workstation or not
    USB_RELAY_POWER_ON  - USB-RELAY port of 230v power on
    USB_RELAY_POWER_OFF - USB-RELAY port of 230v power off
    USB_RELAY_POWER_BTN - USB-RELAY port of target's power button
"""
import os
import time
from collections import OrderedDict
import cij.util
import cij


class Relay(object):
    """USB-RELAY operation"""

    def __init__(self):
        if os.environ.get("USB_RELAY") != "1":
            raise RuntimeError("cij.usb.relay: Invalid USB_RELAY")

        self.__power_on_port = os.environ.get("USB_RELAY_POWER_ON")
        self.__power_off_port = os.environ.get("USB_RELAY_POWER_OFF")
        self.__power_btn_port = os.environ.get("USB_RELAY_POWER_BTN")

        self.__field = OrderedDict()
        self.__device = None

        if self.__refresh():
            raise RuntimeError("cij.usb.relay: Error refresh status")

        if self.__reset():
            raise RuntimeError("cij.usb.relay: Error reset status")

    def __refresh(self):
        status, stdout, _ = cij.util.execute(["usbrelay"])
        if status:
            cij.err("cij.usb.relay: Error run usbrelay")
            return 1

        for line in stdout.strip().split("\n"):
            name, value = line.split("=")
            self.__field[name] = value

            if self.__device is None:
                self.__device = name.split("_")[0]
                cij.info("Device: %s" % self.__device)

            cij.info("%s: %s" % (name, value))

        if self.__field is None:
            cij.err("cij.usb.relay: Error usbrelay field")
            return 1

        return 0

    def __reset(self):
        if self.__field is None:
            cij.err("cij.usb.relay: Error usbrelay field")
            return 1

        for name, value in self.__field.items():
            if value == "1":
                if self.__set(name, 0):
                    return 1
        return 0

    def __set(self, name, state):
        if name not in self.__field.keys():
            cij.err("cij.usb.relay: Unknown name: %s" % name)
            return 1

        status, _, _ = cij.util.execute(["usbrelay %s=%s" % (name, state)])
        if status:
            return 1
        return 0

    def __press(self, port, interval=200):
        name = "%s_%s" % (self.__device, port)

        if self.__set(name, 1):
            return 1

        time.sleep(float(interval) / 1000)

        if self.__set(name, 0):
            return 1

        return 0

    def power_on(self, interval=200):
        """230v power on"""
        if self.__power_on_port is None:
            cij.err("cij.usb.relay: Invalid USB_RELAY_POWER_ON")
            return 1

        return self.__press(self.__power_on_port, interval=interval)

    def power_off(self, interval=200):
        """230v power off"""
        if self.__power_off_port is None:
            cij.err("cij.usb.relay: Invalid USB_RELAY_POWER_OFF")
            return 1

        return self.__press(self.__power_off_port, interval=interval)

    def power_btn(self, interval=200):
        """TARGET power button"""
        if self.__power_btn_port is None:
            cij.err("cij.usb.relay: Invalid USB_RELAY_POWER_BTN")
            return 1

        return self.__press(self.__power_btn_port, interval=interval)
