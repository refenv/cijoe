
.. _sec-packages-qemu-guest_initialize:

qemu.guest_initialize
~~~~~~~~~~~~~~~~~~~~~

.. automodule:: cijoe.qemu.scripts.guest_initialize
   :members:

CLI arguments
-------------

* ``--guest_name GUEST_NAME``

  Name of the qemu guest. (default: None)

* ``--system_image_name SYSTEM_IMAGE_NAME``

  Name of the system image. This will overwrite any system image name defined in the configuration file. (default: None)

* ``--overlay {true,false}``

  Back the boot image with the disk image, as a qcow2 overlay; with false, copy it. With the overlay, the disk image must stay unchanged while the guest is in use. (default: True)
