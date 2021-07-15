.. _sec-prerequisites:

Prerequisites
=============

**cijoe** seeks to be minimally intrusive, however, it does require the
following to operate.

On your **dev box**, ensure that you have:

* `Python 3`_ (>= 3.7)
* `pip3` (matching Python >= 3.7)
* The location emitted by ``python3 -m site --user-base`` in your ``$PATH``
  environment variable
* `Bash`_ (>=4.2)
* An **SSH** client, and **key-based** **authorization** providing unprompted login
  from your **dev box** into your **test-target**.

Check that you have the required versions by running the following on your
**dev box**:

.. code-block:: bash

  python3 --version
  pip3 --version
  bash --version

On your **test-target(s)** you need:

* An **account** to log into
* A running **SSH** server; providing remote login using your **account** from
  your **dev box**
* The **SSH** server configured to allow **key-based** **authorization** for
  your **account** and keys setup to provide unprompted login

**cijoe** relies on **SSH** in order to use a remote **test-target**. To assist
with the **SSH** setup then :ref:`sec-ssh` provides a setup guide for
unprompted login and verifying that the setup is ready to use with **cijoe**.

.. note:: **cjioe** can run "locally", that is, your **dev box** and
   **test-target** is the same machine. However, since most system
   development involves fiddling with the OS kernel, drivers, running
   destructive tests, and in general affect the **test-target** in ways
   that cause system panics and data-loss then the default assumption is that
   the **test-target** is another box accessible remotely via **SSH**.

.. _Bash: https://www.gnu.org/software/bash/
.. _Python 3: https://www.python.org/
