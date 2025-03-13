
.. _sec-packages-core-put:

core.put
~~~~~~~~

.. automodule:: cijoe.core.scripts.put
   :members:

CLI arguments
-------------
options:

* ``-h, --help``

  show this help message and exit

* ``--src SRC``

  path to the file on initiator

* ``--dst DST``

  path to where the file should be placed on the remote machine

* ``--transport TRANSPORT``

  The name of the transport which should be considered as the remote machine. Use 'initiator' if the commands should be run locally. Defaults to the first transport in the config file ('initiator' if none are defined).