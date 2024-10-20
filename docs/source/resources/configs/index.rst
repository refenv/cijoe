.. _sec-resources-configs:

=========
 Configs
=========

However, the default is for the **initator** and the **target** to be the same
system, unless configured otherwise. However, to avoid accidents like invocing a
destructive workflow and forgetting to supply a configuration-file then

**cijoe** configuration files are plain-text files written in :toml:`TOML <>`
and with suffix ``.toml``. **cijoe** itself has few configurable items, thus,
the content of a **cijoe** configuration file is often filled with with items
used by :ref:`sec-resources-scripts`.

However, there are a couple of **cijoe** specific keys:

* SSH Configuration
* Shell Configuration

**cijoe** abides by the convention that configuration values are grouped under
a relevant key. Thus, the those for **cijoe** itself are all stored under the
**cijoe** key, such as:

.. code-block:: toml

   [cijoe.transport]
   ssh.username = foo
   ssh.password = bar

Providing a configuation file to the ``cijoe`` command-line tool is required**.
**The file can be empty, however, one must be provided. The reason being is
**that with **cijoe** then the core interface of ``run(), put(), and get()``
**is **re-targetable**.
That is, when configured to do so, then ``run()`` execute commands on a target**
**machine that is not the **initiator**. And often, then the tasks performed can
**be if not destructive, then modifying the system in one way of the other.

Regardles, lets move onto what you can put into your configuration file that
changes the behavior of **cijoe** itself.


Transport Configuration
=======================

**cijoe** uses :paramiko:`paramiko <>` as the **ssh** implementation.
Consequently, your current **ssh** client configuration (e.g., ``.ssh/config``)
and your **ssh-agent** are not in effect. This is by design to ensure complete
separation of keys and the agent, avoiding clashes with system SSL libraries.

Authentication setup is straightforward and supports only username and password
login at this time. You can configure it as follows:

.. code-block:: ini

   cijoe.transport.ssh.username = foo
   cijoe.transport.ssh.password = bar

.. note::
   Support for key-based login is expected soon.


Command Runner
==============

``cijoe.run.env``
-----------------

It is possible to set up environment variables for the **target** system. All
calls to ``cijoe.run(...)`` will be given the environment variables defined by
this configuration option.

Example:

.. code-block:: ini

   cijoe.run.env = PATH=/usr/local/bin:/usr/bin, LANG=en_US.UTF-8

In this example, any command run through ``cijoe.run(...)`` will use the
specified ``PATH`` and ``LANG`` variables.


.. _sec-resources-configs-api:

API
---

Represented in the code as a :ref:`sec-resources`.

.. autoclass:: cijoe.core.resources.Config
   :members:
   :undoc-members:
   :inherited-members:
