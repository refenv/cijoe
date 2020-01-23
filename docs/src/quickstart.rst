.. _sec-quick-start:

=============
 Quick Start
=============

First, install pip, in your home directory, to avoid messing with Python and
Python packages installed via the system package manager.

.. code-block:: bash

  curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
  python get-pip.py --user

Setup your environment to include :code:`PATH="$PATH:$HOME/.local/bin"`. This
enables running commands such as the ``pip`` installed above, without messing
with your system.

Then install **cijoe** via pip:

.. code-block:: bash

  pip install --user cijoe

Please, always use ``--user`` with pip unless you **really** know what you are
doing.

 Usage
=======

Run **cijoe** interactively and define the target environment:

.. code-block:: bash

  # Start cijoe
  cijoe

  # Use refence definitions as a template for defining your environment
  cat $CIJ_ENVS/refenv-u1604.sh > target_env.sh

  # Open up your favorite editor and modify accordingly
  vim target_env.sh

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
end-of-life. See, the build-status for Python version recommendations.

Why? Well, **cijoe** works with most versions of Python, however, the Travis CI
which is used for testing **cijoe**, deprecates use of Python as they go
end-of-life. Consequently, end-of-line versions of Python are not tested.

Additionally, some of the libraries which **cijoe** depend on, explicit does
not support certain versions of Python.
