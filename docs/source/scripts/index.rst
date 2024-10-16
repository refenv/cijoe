.. _sec-resources-scripts:

Scripts
=======

Let's start by looking at how to run a **cijoe** script, here is how:

.. literalinclude:: ../400_usage_script_all.cmd
   :language: python

To create a **cijoe** Python script, run command ``cijoe --script``, which will
create a python script with the code necessary for running **cijoe**.

Content Overview
----------------

Let's take a look at the example script provided by ``cijoe --example``:

.. literalinclude:: ../../cijoe-script.py
   :language: Python

As you can see, then it is just a regular Python script making use the
batteries included with Python in the form of the :python_argparse:`argparse <>`
and :python_logging:`logging <>`.

What makes the above a **cijoe** script, is the convention for the ``main()``
function and the use of the **cijoe** module. The following subsections go
through how the **cijoe-isms** are used.


.. _sec-resources-scripts-command-execution:

Command Execution
-----------------

The following method is available to execute commands.

.. code-block:: python

   cijoe.run(command, evars, ...)

This is similar to the Python builtin **subprocess.run()**, with the major
behavioral differences:

* You **can** change where the **command** is executed!

  - Via the configuration-file; setup ssh parameters

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
--------------

The result of of ``cijoe.run(...)`` is the tuple:

.. code-block:: python

   (err: int, state: CommandState)

To inspect the output, stdout and stderr is combined, of the command, then use
the method:

.. code-block:: python

   state.output()

It will return the **output** in a **UTF-8** decoded form with errors replaced.
This work well when working with textual output from commands. If you want to
work with non-decoded output from the command, then you can read and process the
command-output file instead of using the ``output()`` helper.


.. _sec-resources-scripts-logging:

Logging
-------

When using the **cijoe** cli, then there is a option for logging
``-l / --log-level``. This content of this log comes from calls to the Python
built-in :python_logging:`logging <>` module. Thus, if you want logging in your
scripts, then you can just do as the example does, e.g.:

.. code-block:: python

   import logging as log
   
   ...
   
   log.info("Status information on something")
   log.error("Something went very wrong!")

When writing your scripts, then it is recommended that you utilize logging if
you want to print anything, by doing so, then **regular** output is reserved to
be coming from **command output** e.g. when using ``-m / --monitor``.


.. _sec-resources-scripts-python-pkgs:

Adding Python packages
----------------------

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