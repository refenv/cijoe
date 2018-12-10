QEMU and Virtual Open-Channel SSDs
==================================

QEMU is an amazing piece of software, in CIJOE it is used as a means to emulate
an Open-Channel SSD. The module providing convenient access to this in CIJOE is
called `qemu::` and relies on a fork of QEMU with NVMe/Open-Channel 2.0
support.

This section describes how to install the QEMU-fork, prerequisites and how to
use it with CIJOE both interactively, in testcases and as a testplan hook.

The following environment vars are the primary requirements for defining you
qemu environment:

.. code-block:: bash

  export QEMU_HOME=/opt/qemu-nvme
  export QEMU_GUESTS=/opt/qemu-guest

Install
-------

Follow these steps:

.. code-block:: bash

  # Prereqs
  sudo apt-get install \
    build-essential \
    gcc \
    pkg-config \
    glib-2.0 \
    libglib2.0-dev \
    libsdl1.2-dev \
    libaio-dev \
    libcap-dev \
    libattr1-dev \
    libpixman-1-dev \
    qemu-kvm \
    libvirt-bin \
    virtinst \
    bridge-utils \
    cpu-checker

  # Grab the qemu-nvme source repository
  pushd /tmp
  git clone https://github.com/CNEX-Labs/qemu-nvme.git
  cd qemu-nvme

  # Configure qemu-nvme for installation in /opt/qemu-nvme
  ./configure \
    --enable-kvm \
    --target-list=x86_64-softmmu \
    --enable-linux-aio \
    --disable-xen \
    --enable-vnc \
    --prefix=/opt/qemu-nvme

  # Install it
  sudo make install -j$(nproc)
  popd

Setting up a QEMU Guest
-----------------------

Setting up a guest requires the following:

* Operating System kernel image (e.g. Linux packed in a bzImage)
* Operating System boot image (e.g. Ubuntu installation in a qcow2 image)
* Backing-files for the Virtual OCSSD
  - These should all be generated

And a placing them in a sub-folder of `$QEMU_GUESTS`. The following is an
example of setting up a guest named `emujoe` using a reference Ubuntu image:

.. code-block:: bash

  # Define where guests are stored
  export QEMU_GUESTS=/opt/qemu-guests
  export QEMU_GUEST_NAME=emujoe
  export QEMU_GUEST_PATH="$QEMU_GUESTS/$QEMU_GUEST_NAME"

  # Create a home for the guests
  sudo mkdir -p "$QEMU_GUEST_PATH"
  sudo chown -R "$USER":"$USER" "$QEMU_GUEST_PATH"

  # Download the Ubuntu 16.04 QATD reference boot image
  pushd $QEMU_GUEST_PATH
  wget https://app.vagrantup.com/safl/boxes/u1604-qatd/versions/1.8.36/providers/libvirt.box -O u1604-qatd.box

  # Extract the qcow2 image from the Vagrant Box
  tar xzvf u1604-qatd.box box.img

  # Rename it
  mv box.img boot.qcow2

Usage
-----

...


Environment
~~~~~~~~~~~

Create an environment description based on the refenv and qemu skeletons:

.. code-block:: bash

  cat $CIJ_ENVS/refenv-u1604.sh > target_env.sh
  tail -n +2 $CIJ_ENVS/qemu.sh >> target_env.sh
  vim target_env.sh


Interactively
~~~~~~~~~~~~~

...

Testcase
~~~~~~~~

...

Testplan Hook
~~~~~~~~~~~~~

...
