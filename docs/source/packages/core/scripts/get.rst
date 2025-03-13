
.. _sec-packages-core-get:

core.get
~~~~~~~~

.. automodule:: cijoe.core.scripts.get
   :members:

CLI arguments
-------------
options:

* ``-h, --help``

  show this help message and exit

* ``--src SRC``

  path to the file on remote machine

* ``--dst DST``

  path to where the file should be placed on the initiator

* ``--transport TRANSPORT``

  The name of the transport which should be considered as the remote machine. Use 'initiator' if the commands should be run locally. Defaults to the first transport in the config file ('initiator' if none are defined).