.. _sec-testcases:

===========
 Testcases
===========

Testcases in **cijoe** are plain Bash scripts. These scripts utilize a handful
of Bash-modules to assist writing testcases and to provide setup for the
testcase such as output directories and environment variables pointing to these
directories e.g.

.. code-block:: bash

  echo $CIJ_TEST_RES_ROOT
  /home/safl/git/cijoe/selftest_results/cijoe_1/Linters_0/cijoe_pylint.sh/_aux
