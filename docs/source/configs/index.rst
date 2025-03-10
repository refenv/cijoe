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
* Workflow Configuration

**cijoe** abides by the convention that configuration values are grouped under
a relevant key. Thus, the those for **cijoe** itself are all stored under the
**cijoe** key, such as:

.. code-block:: toml

   [cijoe.transport]
   ...

   [cijoe.run]
   ...

   [cijoe.workflow]
   ...


.. _sec-resources-configs-transport:

Transport Configuration
-----------------------

**cijoe** uses :paramiko:`paramiko <>` as the **ssh** implementation.
Consequently, the values you set here are the ones used for the call to
:paramiko_client:`connect() <#paramiko.client.SSHClient.connect>`.

Authentication setup is straightforward and supports either username and
password login or key-based login. You can configure it as follows:

.. code-block:: toml

   [cijoe.transport.ssh]
   hostname     = "foo"
   port         = 22
   username     = "bar"

   # either
   password     = "baz"

   # or
   key_filename = "path/to/private_key"
   passphrase   = "baz"


Configuring multiple transports
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When executing scripts over an **ssh** connection, **cijoe** connects to the
first transport defined under the ``cijoe.transport`` key. If you need to 
connect to multiple different transports, you can define them under different
keys, for example:

.. code-block:: toml
   
   [cijoe.transport.machineA]
   hostname = "machineA"
   port = 22
   username = "foo"
   password = "bar"

   [cijoe.transport.machineB]
   hostname = "machineB"
   port = 22
   username = "foo"
   key_filename = "path/to/private_key"

To execute commands on a specific transport, use the ``transport_name`` 
parameter of ``cijoe.run(...)``, for example:

.. code-block:: python

   cijoe.run("hostname")                             # will run on machineA
   cijoe.run("hostname", transport_name="machineB")  # will run on machineB


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
~~~~~~~~~~~~~~~~~~~

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


.. _sec-resources-configs-workflow:

Workflow Configuration
----------------------

When a workflow is processed, each step is executed in sequence. It can be
advantageous to *fail fast*, meaning the workflow stops processing further steps
once a failure occurs in any step.

This is possible via the **cijoe** configuration option:
``cijoe.workflow.fail_fast`` which you can set in your
:ref:`configuration-file <sec-resources-configs>`:

.. literalinclude:: ../../../src/cijoe/core/configs/example_config_default.toml

By default **cijoe** functionality, then this can also be controlled environment
variable:

.. code-block:: bash

   CIJOE_WORKFLOW_FAIL_FAST=true


.. _sec-resources-configs-evar-override:

Environment Variable Override
=============================

Any configuration option specified in a configuration file can be overridden by
an environment variable. This behavior follows a specific naming convention for
environment variables, as outlined below.

For a configuration file entry such as:

.. code-block:: toml

   [foo.bar]
   baz = false

You can override this option with an environment variable named:

.. code-block:: bash

   FOO_BAR_BAZ=true

In summary:

- Convert the configuration path and name to uppercase.

- Replace any dots (``.``) with underscores (``_``).


.. _sec-resources-configs-multiple:

Defining Multiple Configuration Files
=====================================

You can run cijoe with multiple configuration files by specifying the
``--config``/``-c`` argument multiple times to the CLI.

.. code-block:: bash

   cijoe -c path/to/config1.toml -c path/to/config2.toml ...

This allows you to reuse parts of your configuration across runs, reducing 
redundancy.

Although the :toml:`TOML <v1.0.0#keys>` specification states that defining the 
same key multiple times is invalid, **cijoe** permits it across configuration 
files. Files are processed in the order they appear in the command, so later
files override conflicting keys from earlier ones.