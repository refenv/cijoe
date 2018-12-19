.. _sec-quick-start:

=============
 Quick Start
=============

Install **cijoe** system-wide via the pip:

.. code-block:: bash

  sudo pip install cijoe

Or install it user-level:

.. code-block:: bash

  pip install cijoe

.. note:: When doing user-level install, then include the :code:`pip` binary
  install path in your :code:`PATH` definition. For example
  :code:`PATH="$PATH:$HOME/.local/bin"`

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
