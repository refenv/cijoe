"""
    fio-wrapper
    ===========

    The intent is to be able to do tie fio into testing infra and to have a means of
    ensuring that "benchmark" can be performed in a reproducible manner.

    It does so by constructing an transforming a dictionary of parameters and
    environment variables. This is done via:

    * fio(cijoe, parameters="", env={}): invoke fio as defined in cijoe.config.options

    Then **chaining** of the parameter construction is done, such that it is possible to
    control certain job-parameters depending on the device, I/O engine, and I/O engine
    options.
    For example, we might wish to run fio with ``--direct=1``, however, when sending
    that same job to e.g. ``/dev/ng0n1`` (the char-device encapsulating an NVMe
    namespace), then ``--direct=1`` is invalid.
    Such a transformation is then done when seeing that the device is an NVMe chardev.

    config
    ------

    fio.bin

    fio.engines

    retargtable: true
    -----------------
"""


def fio(cijoe, parameters="", env={}):
    """
    Invoke 'fio' using binary at `'cijoe.config.options.fio.bin`', with the given
    parameters and environment variables (``env``)

    @returns err, state
    """

    return cijoe.run(f"{cijoe.config.options['fio']['bin']} {parameters}", env=env)
