.. _sec-resources-configs:

=========
 Configs
=========

**cijoe** configuration files are plain-text files written in :toml:`TOML <>`
and with suffix ``.toml``. **cijoe** itself has few configurable items, thus,
the content of a **cijoe** configuration file is often mostly filled with with 
items used by :ref:`sec-resources-scripts`.

Providing a configuation file to the ``cijoe`` command-line tool is 
**required**. The configuration file can be empty, nevertheless, one must be 
provided, the reason being that with **cijoe**, the core interface of 
``run()``, ``put()``, and ``get()`` is **re-targetable**. That is, when 
configured to do so, ``run()`` executes commands on a **target** machine that 
is not the **initiator**.

Often, tasks performed by **cijoe** can be, if not destructive, modifying 
the **target** system in one way of the other. The default is for the 
**initator** and the **target** to be the same system, and therefore, to avoid 
accidents like invoking a destructive workflow and forgetting to supply a 
configuration file, providing a configuration file in the command line tool
is required. 

**cijoe** specific keys
=======================

You can put whatever information about the target machine that you need in the 
configuration file. However, there are a couple of **cijoe** specific keys that
you should avoid using for other things than the intended purpose:

* SSH Transport Configuration
* Shell Configuration

**cijoe** abides by the convention that configuration values are grouped under
a relevant key. Thus, the those for **cijoe** itself are all stored under the
**cijoe** key, such as:

.. code-block:: toml

   [cijoe.transport]
   ...

   [cijoe.run]
   ...


.. _sec-resources-configs-transport:

Transport Configuration
-----------------------

**cijoe** uses :paramiko:`paramiko <>` as the **ssh** implementation.
Consequently, your current **ssh** client configuration (e.g., ``.ssh/config``)
and your **ssh-agent** are not in effect. This is by design to ensure complete
separation of keys and the agent, avoiding clashes with system SSL libraries.

Authentication setup is straightforward and supports only username and password
login at this time. You can configure it as follows:

.. code-block:: toml

   cijoe.transport.ssh.hostname = jazz
   cijoe.transport.ssh.port     = 22
   cijoe.transport.ssh.username = foo
   cijoe.transport.ssh.password = bar

.. note::
   Support for key-based login is expected soon.


Shell Configuration
-------------------

``cijoe.run.env``
~~~~~~~~~~~~~~~~~

It is possible to set up environment variables for the **target** system. All
calls to ``cijoe.run(...)`` will be given the environment variables defined by
this configuration option.

Example:

.. code-block:: ini

   cijoe.run.env = PATH=/usr/local/bin:/usr/bin, LANG=en_US.UTF-8

In this example, any command run through ``cijoe.run(...)`` will use the
specified ``PATH`` and ``LANG`` variables.


``cijoe.run.shell``
~~~~~~~~~~~~~~~~~~~~~

**cijoe** assumes that the default shell of the **target** machine follows the
POSIX standard for the :posix_sh:`Shell Command Language <>`. If not, for 
example if the target machine is a Windows machine using PowerShell, you can
set the default shell of the **target** with the ``cijoe.run.shell`` key.

Defining the shell is important in cases where environment variables are
declared through **cijoe** as the syntax for this is different in various
shell languages.

In the table below, you can see the keys associated with different shells in 
**cijoe**.

.. list-table::
   :widths: 50 50

   * - Windows PowerShell
     - ``pwsh``
   * - Windows Command Shell
     - ``cmd``
   * - C Shell
     - ``csh``


.. _sec-resources-configs-api:

API
====

Represented in the code as a :ref:`sec-resources`.

.. autoclass:: cijoe.core.resources.Config
   :members:
   :undoc-members:
   :inherited-members:
