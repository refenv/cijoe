
.. _sec-packages-core-cmdrunner:

core.cmdrunner
~~~~~~~~~~~~~~

.. automodule:: cijoe.core.scripts.cmdrunner
   :members:

CLI arguments
-------------
options:

* ``-h, --help``

  show this help message and exit

* ``--commands COMMANDS [COMMANDS ...]``

  The commands to be run

* ``--transport TRANSPORT``

  The key of the transport from the cijoe config file on which the commands should be run. Use 'initiator' if the commands should be run locally. Defaults to the first transport in the config file ('initiator' if none are defined).