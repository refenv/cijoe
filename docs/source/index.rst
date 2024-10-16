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

.. _sec-introduction:

Introduction
============

If you're familiar with tools like :chef:`Chef <>`, :puppet:`Puppet <>`, 
and :ansible:`Ansible <>`, it's important to note that **cijoe** is not 
meant to replace or compete with them. Instead, **cijoe** is more closely 
aligned with Python projects such as :paramiko:`Paramiko <>`, 
:fabric:`Fabric <>`, :invoke:`Invoke <>`, and :invocations:`Invocations <>`. 
In some cases, its usage also resembles tools like :just:`just <>` and 
:make:`make <>`.

While **cijoe** shares some similarities with these tools, it differs by
prioritizing minimalism. This approach applies to system requirements, the
codebase, and the concepts users need to learn.

In terms of functionality, **cijoe** may feel familiar to users
of :ansible:`Ansible <>` or :invocations:`Invocations <>`, or a combination of
both, but its focus is distinct.

Unlike configuration management tools, **cijoe** is a minimal, open-ended
scripting tool that emphasizes maintainability, reusability, and built-in
reporting for sharing results, including command output and artifacts.

**cijoe** is designed to execute commands, scripts, or workflows
within continuous integration (CI) environments such as
:github:`GitHub <>`, :gitlab:`GitLab <>`, :travis:`Travis CI <>`,
and  :jenkins:`Jenkins <>`.
It also allows for seamless execution of the same scripts on local systems,
enabling developers to switch between CI providers while maintaining the ability
to run automated tasks locally.

.. figure:: _static/cijoe-networked.drawio.png
   :alt: Development Environment
   :align: center

   The "core" agentless functionality of **cijoe**; run commands and tranfer
   files


Terminology
-----------

For reference, then a bit of terminalogy used by **cijoe** is defined here.
The intent here is to reduce confusion for readers with prior experience and
knowledge for these terms in other contexts.

command
  This is a string describing either the invokation of a command-line tool, this  	
  can be with or without arguments e.g. ``hostname`` and	``lspci -v``. Or a 	 	
  shell-expression ``[ -f /tmp/ jazz ] && echo "Hello!"``.

initiator
  This is the system on which **cijoe** is installed and where the ``cijoe``
  command-line and scripts are executed

target
  This is where **commands** are executed, and data (files/folders) is transferred
  to and from.

Key Features
------------

- **Simplicity**:

  - **cijoe** is designed to be easy to use and does not require extensive
    learning. It avoids the need to master YAML-based scripting languages, as is
    common with other systems. Instead, it relies on Python and offers a helper
    class for the core scripting interface.
  
- **Agentless**:

  - When used with remote systems, **cijoe** operates in an agentless fashion.
    It relies on SSH for executing commands on target systems. Unlike Ansible,
    **cijoe** does not require Python to be installed on the target node.
  - For data transfer, **SSH** and **SCP** are similarly used.

- **Realtime Output**:

  - Whether **cijoe** is executing scripts of workflows, then it **can**
    provide you with realtime command output, directly in your console.
  - When running in cloud environments e.g. GitHub Actions, GitLab, Azure,
    Travis, etc. then it is very convient to immediately observe execution
    progress

- **Postprocessing**:

  - All command output is collected in output logs without **any** form
    of filtering. By doing so, then post-processing, of artifacts and
    command-output is always possible

- **Reporting**:

  - All data from **runs**, script and workflow executions, is collected in a
    **HTML** report. Conveniently viewable even when running on remote systems

In summary, **cijoe** aims to be a simple yet powerful tool that integrates
well within your CI workflows, whether on a remote CI provider or local systems,
without adding complexity.

Once you have ensured that the system prerequisites (:ref:`sec-prerequisites`)
are met, proceed to the :ref:`sec-usage` section to run an example
script and workflow. For documentation on how to create your own scripts,
see :ref:`sec-resources`. Finally, refer to :ref:`sec-packages` for descriptions
of existing script collections and related packages.

.. toctree::
   :maxdepth: 2
   :includehidden:
   :hidden:

   usage/index.rst
   scripts/index.rst
   workflows/index.rst
   testrunner/index.rst
   resources/index.rst
   packages/index.rst
   prerequisites/index.rst
