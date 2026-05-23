
.. _sec-packages-core-testrunner:

core.testrunner
~~~~~~~~~~~~~~~

.. automodule:: cijoe.core.scripts.testrunner
   :members:

CLI arguments
-------------

* ``--run_local {true,false}``

  Whether 'pytest' should be executed in same environment as 'cijoe' (default: True)

* ``--random_order {true,false}``

  Whether the tests should be run in random order. This is generally recommended, as it helps reduce inter-test dependencies and assumptions about the environment's state (default: True)

* ``--args ARGS``

  Additional arguments passed verbatim to 'pytest'. (default: None)
