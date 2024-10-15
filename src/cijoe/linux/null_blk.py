"""
    null_blk module, helpers to load/unload null block instances

    To use it, one must have permissions to modprobe, rmmod and modify the /syscfg

    NOTE: This is **fully** re-targetable, that is, changing transport changes where it
    is running.

    For reference, see: https://docs.kernel.org/block/null_blk.html

    TODO
    - Implement initialization of nullblk instances via /sys/kernel, this allows for
      different device instances instead of N instances with the same configuration.
      For example, one can instantiate a regular block-device as well as a zoned
      block-device.

    retargetable: True
"""

NULLBLK_MODULE_NAME = "null_blk"
NULLBLK_SYSPATH = "/sys/kernel/config/nullb"


def insert(cijoe, config=None):
    """Load the 'null_blk' kernel module using parameters defined in the config"""

    if config is None:
        config = cijoe.config.options.get("null_blk")

    nullblk_params = (
        " ".join([f"{k}={v}" for k, v in config.items()])
        if config.get("nr_devices")
        else ""
    )

    return cijoe.run(f"modprobe {NULLBLK_MODULE_NAME} {nullblk_params}")


def remove(cijoe):
    """Remove the null_blk kernel module"""

    # This can be used when instanttation via SYSPATH, however, commented out as it is
    # not useful yet.
    # cijoe.run(f"rmdir {NULLBLK_SYSPATH}/nullb*")

    return cijoe.run(f"modprobe -r {NULLBLK_MODULE_NAME}")
