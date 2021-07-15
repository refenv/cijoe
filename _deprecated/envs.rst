.. _sec-environments:

=====================
 Target Environments
=====================

When running testcases a target-environment script is sourced, it provides a
collection of environment variables defining the target-environment. These
variable definitions provide input to testcases and to **cijoe**.

Input for testcases
===================

The variable-definitions you will find in target-environment scripts are along
the lines of:

.. code-block:: bash

  # on this system, fio is located here
  : "${FIO_BIN:=/one/this/system/the/bin/is/here/fio}"

  # we want to use this device for testing
  : "${NVME_DEV:=/dev/nvme0n1}"

The above are just examples of a common need to provide  non-default location
of a binary, in this example, the location of fio. Such a definition is
generally useful to avoid hardcoding the location inside the test-script
itself.

Also, a testcase may need to run some tests on an NVMe device, to avoid
hardcoding the path to the device in the script, then the path is provided in
the environment file.

The above are examples of providing **input** variables to testcases, such that
the testcases themselves can easily be retargeted in a different environment.
That is, as in the example, where the fio-binary is located elsewhere or a
different NVMe device is used for testing.

Input for cijoe
===============

Another set of variables defined in the target-environment script provide input
to **cijoe** itself. Specifically, to the Bash-modules used in the testcases.

The most essential are the **cijoe** Helper functions:

* ``cij::pass`` | ``cij::fail``, providing a convention for when a test passed or
  failed
* ``cij::cmd``, a re-targetable command-executation

The latter is guided by environment variables, by default **cijoe** executes
commands locally. However, if the target-environment script defines SSH
transport for **cijoe**, then the commands will execute remotely.

For remote execution, a target-environment could contain:

.. code-block:: bash

  # This is the remote system that we want to test on
  : "${SSH_HOST:=testbox}"; export SSH_HOST
  : "${SSH_PORT:=22}"; export SSH_PORT
  : "${SSH_USER:=root}"; export SSH_USER

Used interactively
==================

**cijoe** provides a test-runner, a test-reporter, a metric-extractor,
analyser and plotter. These tools are great for automating testing, and
post-processing for performance evaluation and visualization.

But that is not all, for interactive usage, then ``cijoe`` provides an
interactive shell ``cijoe``. When invoking it with a target-environment as
argument, like so:

.. code-block:: bash

  cijoe my_target.sh

Then you will be dropped in a bash-shell, clearly indicating that you are now
in **cijoe** and which target-environment is avaiable. When doing so, then all
the **cijoe** Bash modules are loaded, and you can invoke:

.. code-block:: bash

  cij::cmd "cat /etc/os-release"

Then the command will be executed according the the environment definition. So,
if you have defined the SSH environment, then it will run remotely. And, if you
want to jump to the remote machine, then invoke::

  ssh::shell


