.. _sec-quick-start:

=============
 Quick Start
=============

First, install ``pip`` locally using the pip installer.

.. code-block:: bash

    curl https://bootstrap.pypa.io/get-pip.py | python --user

Change your environment to include your Python binaries. This enables your
environment to find the local instance of ``pip`` and the **cijoe** binaries.

.. code-block:: bash

    echo "export PATH=\"$PATH:$(python -m site --user-base)/bin\"" >> ~/.bash_aliases

Install **cijoe** via pip:

.. code-block:: bash

  pip install --user cijoe

The ``--user`` isolates the installation to the current account, instead of
installing it system wide and potentially colliding with system packages.


**cijoe** seeks to be minimally intrusive, however, it does require the
following to operate properly:

* `Python`_ (>= 3.7)
* `Bash`_ (>=4.2)
* `ShellCheck`_
* `Pylint`_
* An **SSH** client and ssh-key pairs setup, more on this in the Usage section

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
      $CIJ_TESTPLANS/example_01_usage.plan \
      target_env.sh \
      --output $RESULTS

  # Create test report
  cij_reporter $RESULTS

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

Python Version
==============

It is recommended that you use **cijoe** with a Python version that is not
end-of-life, as **cijoe** is only tested on active python versions on Travis CI.
See, the build-status for Python version recommendations.

Additionally, some of the libraries which **cijoe** depend on, explicit does
not support certain versions of Python.

.. _Bash: https://www.gnu.org/software/bash/
.. _Pylint: https://www.pylint.org/
.. _Python: https://www.python.org/
.. _ShellCheck: https://www.shellcheck.net/
.. _SshKeys: https://www.digitalocean.com/community/tutorials/how-to-configure-ssh-key-based-authentication-on-a-linux-server
