.. _sec-resources-workflows:

===========
 Workflows
===========

Workflows enable the organized execution of commands and scripts. After
execution, a report is generated, containing the status and embedded
documentation of the workflow and scripts in a self-contained format. To run the
workflow produced by ``cijoe --example``, use the following command:

.. literalinclude:: ../420_usage_workflow_all.cmd
   :language: bash

The command will execute **all** the
:ref:`steps <sec-resources-workflows-steps>` in the workflow. To run a subset of
steps, you can specify the step name(s) as arguments to the ``cijoe`` tool,
similar to how targets are specified in a :make:`Makefile <>`:

.. literalinclude:: ../450_usage_workflow_subset.cmd
   :language: bash

With the above, only the step named **builtin_script** will be executed. This
becomes even more useful when utilizing **cijoe** bash completions.


.. _sec-resources-workflows-content:

Content Overview
================

Let's take a look at what the workflow file produced by ``cijoe --example``
looks like:

.. literalinclude:: ../../cijoe-workflow.yaml
   :language: yaml


At a first glance, then it might feel a bit similar to GitHub Actions workflow,
but dramatically simpler since:

* There are **no** logic operators

* There **is** simple variable substitution using

  - Values from configuration file
  - Values from environment variables on **initiator**

* Minimal amount of "magic" keys

  - ``doc``: Describe what the workflow does using multi-line plain-text
  - ``steps``: Ordered list of scripts, to inline-commands, to run

Descriptions of the content is provided in the following subsections.

.. _sec-resources-workflows-steps:

Steps
=====

Although **cijoe** aims to be simple, with minimal "magic" and a low learning
curve, there is some **yaml-magic** involved in the workflow steps. A step can
take one of two forms: either as :ref:`sec-resources-workflows-inline-commands`
or as :ref:`sec-resources-workflows-step-scripts`.

Both forms require that a step **must** have a **name**. This allows subsets
of steps to be executed via the ``cijoe`` command-line tool. When naming steps,
follow these conventions:

* Letters: a-z
* Numbers: 0-9
* Special characters: `-` and `_`
* Must be lowercase
* Must **not** start with a number

In short, use the typical lowercase identifier convention.

.. _sec-resources-workflows-inline-commands:

Inline Commands
---------------

A step with **inline commands** take the form:

.. code-block:: yaml

   steps:
   - name: commands_inline
     run: |
       cat /proc/cpuinfo
       hostname

Each line in a multi-line string is executed. It is implemented as a call to
``cijoe.run(command)``. Thus, the above notation for **inline commands** turn
into execution of functions in the **cijoe** Python module:

.. code-block:: python

   cijoe.run("cat /proc/cpuinfo")
   cijoe.run("hostname")

.. note::
   This is implemented in **cijoe** as "syntactic-sugar" for
   running the built-in script **core.cmdrunner**. Thus, have a look
   at :ref:`sec-resources-workflows-step-scripts` to see what this **unfolds**
   as.


.. _sec-resources-workflows-step-scripts:

Steps with Scripts
------------------

When a step runs a script, then you give it a **name** and you tell it

.. code-block:: yaml

   steps:
   - name: commands_via_script
     uses: core.cmdrunner
     with:
       commands: |
         cat /proc/cpuinfo
         hostname

Take note of the "magic" keys:

uses
  Name of the script to run, without the ``.py`` extension. Packaged scripts
  include a prefix, such as ``core.``, ``linux.``, or ``gha.``. As in the
  example above where the script ``cmdrunner.py`` from the ``core`` package
  is used.

with
  Everything under this key is passed to the script's entry function:
  ``main(args, cijoe, step)`` as the ``step`` argument.


.. _sec-resources-workflows-linting:

Linting
-------

When you write a workflow yourself it can be nice to check whether it is valid
without running it. You can do so by running:

.. literalinclude:: ../300_lint.cmd
   :language: bash
