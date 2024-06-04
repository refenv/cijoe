"""
    kmemleak module, providing helpers to: "clear", "scan" and "cat" kmemleak

    For details on kmemleak, have a look at the Linux Kernel Documentation at

    https://www.kernel.org/doc/html/latest/dev-tools/kmemleak.html

    retargetable: True
"""


def cat(cijoe):
    """Dump the contents of kmemleak"""

    return cijoe.run("cat /sys/kernel/debug/kmemleak")


def scan(cijoe):
    """Scan the kernel"""

    return cijoe.run("echo scan > /sys/kernel/debug/kmemleak")


def clear(cijoe):
    """Clear the kmemleak"""

    return cijoe.run("echo clear > /sys/kernel/debug/kmemleak")
