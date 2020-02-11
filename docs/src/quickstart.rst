.. _sec-quick-start:

=============
 Quick Start
=============

First, install ``pip`` locally using the pip installer.

.. code-block:: bash

    curl https://bootstrap.pypa.io/get-pip.py | python --user

Change your environment to include :code:`PATH="$PATH:$HOME/.local/bin"`. This
enables your environment to find the local instance of ``pip``.

.. code-block:: bash

    echo "PATH=\"$PATH:$HOME/.local/bin\"" >> ~/.bash_aliases

Install **cijoe** via pip:

.. code-block:: bash

  pip install --user cijoe

The ``--user`` isolates the installation to the current account, instead of
installing it system wide, which is less secure.

Usage
=====

Run **cijoe** interactively and define the target environment:

.. code-block:: bash

  # Start cijoe
  cijoe

  # Use refence definitions as a template for defining your environment
  cat $CIJ_ENVS/refenv-u1604.sh > target_env.sh

  # Open up your favorite editor and modify accordingly
  editor target_env.sh

Invoke the test runner, generate report and inspect the result:

.. code-block:: bash

  # Create directory to store results
  RESULTS=$(mktemp -d trun.XXXXXX -p /tmp)

  # Run the testplan example
  cij_runner \
      $CIJ_TESTPLANS/example_01_usage.plan \
      target_env.sh \
      --output $RESULTS

  # Create test report
  cij_reporter $RESULTS

  # Inspect the test-report
  xdg-open $RESULTS/report.html

Python Version
==============

It is recommended that you use **cijoe** with a Python version that is not
end-of-life, as **cijoe** is only tested on active python versions on Travis CI.
See, the build-status for Python version recommendations.

Additionally, some of the libraries which **cijoe** depend on, explicit does
not support certain versions of Python.
