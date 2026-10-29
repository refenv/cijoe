
.. _sec-packages-core-wait_for_transport:

core.wait_for_transport
~~~~~~~~~~~~~~~~~~~~~~~

.. automodule:: cijoe.core.scripts.wait_for_transport
   :members:

CLI arguments
-------------

* ``--transport_name TRANSPORT_NAME``

  Name of the target to wait for; default: the step's target. (default: None)

* ``--state {down,up}``

  Desired target state to wait for: 'down' or 'up'. Default: up. (default: up)

* ``--timeout TIMEOUT``

  Maximum seconds to wait for the desired state. (default: 60)
