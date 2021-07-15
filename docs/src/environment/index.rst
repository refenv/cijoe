.. _sec-environment:

Environment Definition
======================

An **environment definition** is a Bash-script consisting of **exported**
variables defining the various properties of a **test-target**.

The **environment definition** describes **where** to run, specifically by
defining the variables needed for accessing your **test-target** via **SSH**.
Have a look at the reference environment (``remote.sh``) provided with
**cijoe** either in your installation at ``$CIJ_ENVS/remote.sh`` or in the
`cijoe repository`_.

.. note:: This is all that you need to provide in the **environment
   definition** for **cijoe** itself. However, each **cijoe** package provide
   one or more **reference environment definition(s)**. These serve, as the
   name suggest, as a reference for the **exported variables** that a given
   **cijoe package** needs.  Consult these for setting up your environment for
   the functionality provided by a specific package.

.. _sec-environment-example:

Example: remote
---------------

As an example, we create an **environment definition** for the **test-target**
named ``box01`` with a login-account accessible with the username ``odus``. To
easily distingush different environment definitions then we name
``box01_env.sh``:

.. literalinclude:: box01_env.sh
   :language: bash
   :caption: box01_env.sh

Adjust this to match your development environment, that is, the hostname of
your **test-target** box and the username of your **account** on that system.
In case you missed it, then ensure that you have :ref:`sec-ssh` appropriatly.

We can now use this **environment definition** for :ref:`sec-running` and
interactively in the :ref:`sec-shell`.

.. _sec-environment-example-local:

Example: local
--------------

In case your **dev box** and **test-target** are one and the same machine, then
you can either setup your **SSH** configuration to access localhost, or you can
use configure **cijoe** to not use **SSH** for command-transport.

An example of the latter is provided with **cijoe** in the ``envs/local.sh``
file, it looks like this:

.. literalinclude:: ../../../envs/local.sh
   :language: bash
   :caption: envs/local.sh

.. _cijoe repository: https://github.com/refenv/cijoe/
