.. _sec-resources-tasks:

=======
 Tasks
=======

Tasks enable the organized execution of commands and scripts. After
execution, a report is generated, containing the status and embedded
documentation of the task and scripts in a self-contained format. To run the
task produced by ``cijoe --example``, use the following command:

.. literalinclude:: ../420_usage_task_all.cmd
   :language: bash

The command will execute **all** the
:ref:`steps <sec-resources-tasks-steps>` in the task. To run a subset of
steps, you can specify the step name(s) as arguments to the ``cijoe`` tool,
similar to how targets are specified in a :make:`Makefile <>`:

.. literalinclude:: ../450_usage_task_subset.cmd
   :language: bash

With the above, only the step named **inline_commands** will be executed. This
becomes even more useful when utilizing **cijoe** bash completions.

There are a couple of task-specific options. See the
:ref:`sec-resources-configs-task` section for reference.


.. _sec-resources-tasks-content:

Content Overview
================

Let's take a look at what the task file produced by ``cijoe --example core.default``
looks like:

.. literalinclude:: ../../../src/cijoe/core/tasks/example_task_default.yaml
   :language: yaml

At a first glance, then it might feel a bit similar to GitHub Actions workflow,
but dramatically simpler since:

* There are **no** logic operators

* There **is** simple variable substitution using

  - Values from configuration file
  - Values from environment variables on **initiator**

* Minimal amount of "magic" keys

  - ``doc``: Describe what the task does using multi-line plain-text
  - ``steps``: Ordered list of scripts, to inline-commands, to run

Descriptions of the content are provided in the following subsections.

.. _sec-resources-tasks-steps:

Steps
=====

Although **cijoe** aims to be simple, with minimal "magic" and a low learning
curve, there is some **yaml-magic** involved in the task steps. A step can
take one of two forms: either as :ref:`sec-resources-tasks-inline-commands`
or as :ref:`sec-resources-tasks-step-scripts`.

Both forms require that a step **must** have a **name**. This allows subsets
of steps to be executed via the ``cijoe`` command-line tool. When naming steps,
follow these conventions:

* Letters: a-z
* Numbers: 0-9
* Special characters: `-` and `_`
* Must be lowercase
* Must **not** start with a number

In short, use the typical lowercase identifier convention.

.. _sec-resources-tasks-inline-commands:

Inline Commands
---------------

A step with **inline commands** take the form:

.. literalinclude:: ../../../src/cijoe/core/tasks/example_task_default.yaml
   :language: yaml
   :lines: 24-27

Each line in a multi-line string is executed. It is implemented as a call to
``cijoe.run(command)``. Thus, the above notation for **inline commands** turns
into execution of functions in the **cijoe** Python module:

.. code-block:: python

   cijoe.run("cat /proc/cpuinfo")
   cijoe.run("hostname")

.. note::
   This is implemented in **cijoe** as "syntactic-sugar" for
   running the built-in script :ref:`core.cmdrunner <sec-packages-core-cmdrunner>`.
   Thus, have a look at :ref:`sec-resources-tasks-step-scripts` to see what
   this **unfolds** as.

Because ``run:`` is sugar for ``core.cmdrunner``, you can pass any of its
arguments alongside ``run:`` using a ``with:`` block. The most common use is
selecting which transport executes the commands:

.. code-block:: yaml

   - name: on_remote
     run: |
       hostname
       uname -a
     with:
       transport: ssh

Without ``transport``, commands run on the first transport defined in the
configuration file (``initiator`` if none are defined). See
:ref:`core.cmdrunner <sec-packages-core-cmdrunner>` for the full set of
arguments.


.. _sec-resources-tasks-step-scripts:

Steps with Scripts
------------------

When a step runs a script, you give it a **name** and tell it which script to
run, like so:

.. literalinclude:: ../../../src/cijoe/core/tasks/example_task_default.yaml
   :language: yaml
   :lines: 29-34

Take note of the "magic" keys:

uses
  Name of the script to run, without the ``.py`` extension. Packaged scripts
  include a prefix, such as ``core.`` or ``linux.``. As in the
  example above where the script ``cmdrunner.py`` from the ``core`` package
  is used (:ref:`core.cmdrunner <sec-packages-core-cmdrunner>`).

with
  Everything under this key is passed to the script's entry function:
  ``main(args, cijoe)`` in the ``args`` argument.


.. _sec-resources-tasks-linting:

Linting
-------

When you write a task yourself it can be nice to check whether it is valid
without running it. You can do so by running:

.. literalinclude:: ../300_lint.cmd
   :language: bash
