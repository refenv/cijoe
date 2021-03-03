.. _sec-quick-start:

=============
 Quick Start
=============

**cijoe** seeks to be minimally intrusive, however, it does require the
following to operate properly:

* `Python`_ (>= 3.7)
* `pip` (matching Python >= 3.7)
* `Bash`_ (>=4.2)
* An **SSH** client, and keybased auth. configured for your test-target.

You can inspect the output of the commands commands:

.. code-block:: bash

  python3 --version
  pip3 --version
  bash --version

To check that you have the required versions. If not, then install them via
your systems package manager or however software is best installed on your
system.

For the SSH setup, see the xyz section.

Installation
------------

Install **cijoe** via pip:

.. code-block:: bash

  pip3 install --user cijoe

The ``--user`` isolates the installation to the current user account, instead
of installing it system wide and potentially colliding with system packages.

Check that it installed correctly, by running:

.. code-block:: bash

  cij_runner --help

If this does not produce the usage-page of the runner, then your system is
probably not configured to look for binaries in the location that ``pip3``
installs them to.

For example, on Linux then the output of ``python -m site --user-base`` is not
in your environment-variable ``$PATH``. You can quickly fix this by adding it
to your shell, e.g. for Bash do:

.. code-block:: bash

    echo "export PATH=\"$PATH:$(python -m site --user-base)/bin\"" >> ~/.bash_profile

Usage
=====

Run **cijoe** interactively and define the target environment:

.. code-block:: bash

  # Start cijoe
  cijoe

  # Use refence definitions as a template for defining your environment
  cat $CIJ_ENVS/remote.sh > target_env.sh

  # Open up your favorite editor and modify accordingly
  editor target_env.sh

.. note:: Ensure that you have setup key-based SSH authentification matching
  the ``SSH_HOST`` and ``SSH_USER`` in your environment configuration e.g. in
  ``target_env.sh``. Have a look at `SshKeys`_ for setting up key-based auth.

Using runner and report
-----------------------

Invoke the test runner, generate report and inspect the result:

.. code-block:: bash

  # Create directory to store results
  RESULTS=$(mktemp -d)

  # Run the testplan example
  cij_runner \
      --testplan $CIJ_TESTPLANS/example_01_usage.plan \
      --env target_env.sh \
      --output $RESULTS

  # Create test report
  cij_reporter --output $RESULTS

  # Inspect the test-report
  xdg-open $RESULTS/report.html

Using testcases directly
------------------------

When 1 out of 40.000 tests fail, you might want to zoom in and run that
testcase manually, here is how you would do that:

.. code-block:: bash

  # Start cijoe interactively with your test-environment
  cijoe target_env.sh

  # Define the test-result root
  export CIJ_TEST_RES_ROOT=/tmp/manual

  # Then just run the bash-script!
  bash mytestcase.sh

However, if your testplan uses hooks, evars, or other target-modifying things,
then the state of your target will of course not match the state of your target
when the testcase is executed via the runner.

Often, it is simpler to just copy the testplan and change it to only hold the
single testcase of interest.

.. _Bash: https://www.gnu.org/software/bash/
.. _Python: https://www.python.org/
