.. _sec-resources-scripts:

=========
 Scripts
=========

There are multiple scripts in the :ref:`resources <sec-resources>` of **cijoe**.
These can be run directly with the cli tool.

.. literalinclude:: ../400_usage_script_all.cmd
   :language: python

You can also create your own **cijoe** scripts locally and run them which can
be run in the same manner. Let's start by running the script produced by 
``cijoe --example``:

.. literalinclude:: ../400_usage_script_local.cmd
   :language: python

When running, an **output** directory is populated with log files, statefiles,
command-output files, and artifacts produced or otherwise collected by the
script.


Content Overview
================

Let's take a look at the example script provided by ``cijoe --example``:

.. literalinclude:: ../../../src/cijoe/core/scripts/example_script_default.py
   :language: Python

As you can see, then it is just a regular Python script making use the
batteries included with Python in the form of the :python_argparse:`argparse <>`
and :python_logging:`logging <>`.

What makes the above a **cijoe** script, is the convention for the ``main()``
function and the use of the **cijoe** module. The following subsections go
through how the **cijoe-isms** are used.


.. _sec-resources-scripts-command-execution:

Command Execution
=================

The following method is available to execute commands.

.. code-block:: python

   cijoe.run(command, evars, ...)

This is similar to the Python builtin **subprocess.run()**, with the major
behavioral differences:

* You **can** change where the **command** is executed!

  - Via the configuration-file; see :ref:`sec-resources-configs-transport`.

* You **cannot** change where the Python code is executing!

  - **cijoe** runs Python / script logic on the **initiator** but not on the
    **target**

You can handle all the logic in Python without requiring Python and its
dependencies on the **target** system. Keep this in mind when writing your
scripts to ensure that your Python code focuses on logic, control flow, and text
processing. Avoid using shell-related helpers like shutil since the Python code
will **not** be **re-targeted** only the **commmand**.


.. _sec-resources-scripts-command-output:

Command Output
==============

The result from ``cijoe.run(...)`` is the tuple:

.. code-block:: python

   (err: int, state: CommandState)

That is, the error / returncode of the command and a command-state object. A
couple of things to take note of:

* **command output** is *always* a combination of the **stdout** and **stderr**
  output streams into a single **command output** stream

* **command output** is always captured and written to file on the
  **initiator**

* You can tell the ``cijoe`` command-line tool to **also** dump the **command
  output** to **stdout** on the **initiator**, in realtime, with the argument
  ``-m / --monitor``

To handle the **command output** in your script, then you can conveniently read
the entire output via a helper on the CommandState object:

.. code-block:: python

   state.output()

It will return the **output** in a **UTF-8** decoded form with errors replaced.
This work well when working with textual output from commands. If you want to
work with non-decoded output from the command, then you can read and process the
command-output file instead of using the ``output()`` helper.


.. _sec-resources-scripts-logging:

Logging
=======

When using the ``cijoe`` command-line tool, then there is a option for logging
``-l / --log-level``. The content of this log comes from calls to the Python
built-in :python_logging:`logging <>` module. Thus, if you want logging in your
scripts, then you can just do as the example does, e.g.:

.. code-block:: python

   import logging as log
   
   ...
   
   log.info("Status information on something")
   log.error("Something went very wrong!")

Log statements are printed to **stdout** in the shell where ``cijoe`` is
running. When writing **cijoe** scripts, it is recommended to use logging
for any printed output. This ensures that **regular** output is reserved for
**command output**, such as when using the ``-m`` or ``--monitor`` options.


.. _sec-resources-scripts-getconf:

Getting Configuration Values
============================

**cijoe** provides a convenient function for retrieving values from the 
configuration file. It can be used as follows:

.. code-block:: python

   value = cijoe.getconf("example.max.value")

   log.info(f"Max value is capped at ({value})")

You can override configuration file values using environment variables. For
example, if the environment variable ``EXAMPLE_MAX_VALUE`` is set, its value
will be used instead of the value specified in the configuration file.


.. _sec-resources-scripts-python-pkgs:

Adding Python packages
======================

Python projects are commonly installed in virtual environments (venv) and it is
recommended that **cijoe** is installed using :pipx:`pipx <>`, since when doing
so then **cijoe** will be installed in a venv, however, it is made available
on your shell / terminal, such that you can simply invoke  the ``cijoe``
command-line tool without first activating a venv or in other ways "enter" the
venv. This is **very** convenient.

However, in case your script requires some Python package which is not readily
available, how to add it? This can be done by **injecting** it into the
**cijoe** venv provided by **pipx**. Here is an example, of adding matplotlib:

.. literalinclude:: ../100_inject.cmd

Running a sequence of **cijoe** scripts
---------------------------------------

If you have created multiple **cijoe** scripts that needs to be run
sequentially, you can do so by adding all scripts as arguments to the **cijoe**
command.

.. code-block:: python

   cijoe path/to/cijoe-script-A.py path/to/script-B.py [...]