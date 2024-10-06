==================================================
 cijoe: tools for systems development and testing
==================================================

**cijoe** is a tool designed to collect and formalize the common elements used
during systems development, enabling an **automated** and **reproducible**
workflow.

When using **cijoe**, the first step involves creating :ref:`scripts
<sec-resources-scripts>` for automating repetitive tasks. As these :ref:`scripts
<sec-resources-scripts>` are developed, all input values are stored in
and passed through :ref:`configuration files <sec-resources-configs>` and
environment variables.
By keeping input values separate from the script itself, tasks can be easily
replicated across different environments, ensuring flexibility and consistency
in execution.

As your script collection grows, **cijoe** allows you to organize them
into :ref:`workflows <sec-resources-workflows>`.
A :ref:`workflow <sec-resources-workflows>` consolidates the
:ref:`script <sec-resources-scripts>` execution sequence, documents their
combined purpose, and provides usage instructions. This clarity makes it easier
for others to understand and consistently execute the workflow in their own
environments.

After execution, **cijoe** generates a report that includes command output,
script documentation, auxiliary collected artifacts, and a workflow summary.
This report facilitates collaboration by providing results transparently, making
them easy to **review** and **reproduce**.

Quickstart
==========

**Try it yourself!** The commands below install **cijoe** and then invoke
``cijoe --example`` which generates an example
:ref:`script <sec-resources-scripts>`,
:ref:`configuration file <sec-resources-configs>`, and a 
:ref:`workflow <sec-resources-workflows>` in your current working directory.
Finally, when ``cijoe`` is executed, it picks up the example
:ref:`workflow <sec-resources-workflows>` and
:ref:`configuration file <sec-resources-configs>`, runs them, captures output,
produces an HTML report, and opens it using your preferred browser if one is
available.

.. literalinclude:: 200_quickstart.cmd
   :language: bash

**cijoe** operates silently by default, as in, it does not print output unless
errors occur. Options for customizing the behavior include:

- ``-n`` / ``--no-report``: Disable the generation and display of the HTML report.
- ``-l`` / ``--log-level``: Increase verbosity by setting a higher log level.
- ``-m`` / ``--monitor``: Enable real-time monitoring of the workflow.

For a detailed description of usage see ``cijoe --help`` and refer to the rest
of the documentation, and good place to continue is with :ref:`sec-usage`.

.. toctree::
   :maxdepth: 2
   :includehidden:
   :hidden:

   introduction/index.rst
   usage/index.rst
   resources/index.rst
   packages/index.rst
   prerequisites/index.rst
