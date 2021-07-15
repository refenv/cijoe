.. _sec-shell:

===================
 Interactive Shell
===================

You can use **cijoe** interactively via the **cijoe shell**. When running the
command:

.. code-block:: bash

  cijoe

Invoking the above command starts a Bash subprocess/Shell with all the
**cijoe** modules loaded. You can use Bash-completion to see what is available
and play around.

.. _sec-shell-introspection:

Introspection
=============

and inspect the default environment used by **cijoe** while in the Shell run:

.. literalinclude:: printenv.cmd
   :language: bash
   :lines: 2-

Which will yield outout similar to:

.. literalinclude:: printenv.out
   :language: bash
   :lines: 3-

Testcases without runner
========================

When 1 out of 40.000 tests fail, you might want to zoom in and run that
testcase manually, here is how you would do that:

.. code-block:: bash

  # Start cijoe interactively with your test-environment
  cijoe box01_env.sh

  # Define the test-result root
  export CIJ_TEST_RES_ROOT=/tmp/manual

  # Then just run the bash-script!
  bash "$CIJ_TESTCASES/example_01_minimal.sh"

.. note:: If your testplan uses hooks, evars, or other target-modifying things,
   then the state of your target will of course not match the state of your
   target when the testcase is executed via the runner.
