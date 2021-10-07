.. _sec-quickstart:

=============
 Quick Start
=============

Run the following commands in your shell:

.. code-block:: bash

  # Install CIJOE and the CIJOE example package
  pip3 install --user cijoe cijoe-pkg-example

  # Start the CIJOE shell
  cijoe

  # Use the refence environment definition as a template for your environment
  cat $CIJ_ENVS/remote.sh > target_env.sh

  # Modify it to match your *test-target* *environment*
  editor target_env.sh

  # Create directory to store test results aka the *testrun*
  RESULTS=$(mktemp -d)

  # Invoke the CIJOE runner, running a *testplan* in your *environment*
  cij_runner \
      --testplan $CIJ_TESTPLANS/example_01.plan \
      --env target_env.sh \
      --output $RESULTS

  # Create a test report for the resulting testrun
  cij_reporter --output $RESULTS

  # Inspect the report
  xdg-open $RESULTS/report.html

In case the above did not work for you, or you just want to know what went on
above, or you want to know what else you can do with **cijoe**, or whatever
your motivation is, then the rest of the documentation should be able to answer
your questions.

The :ref:`sec-introduction` serves as the starting point, defining some terms
and information which will be used throughout the documentation and providing
an overview of the remaining sections.
