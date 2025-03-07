.. _sec-usage:

=======
 Usage
=======

The entry point for **usage** of **cijoe** is the command-line tool ``cijoe``.
Much like :ansible:`Ansible <>` requires playbooks and inventories,
:make:`make <>` needs a ``Makefile``, and GitHub Actions relies on workflows,
then **cijoe** also requires input to function, these are:

- An individual :ref:`script <sec-resources-scripts>` to execute **or** a
  collection of :ref:`scripts <sec-resources-scripts>`, ordered, and documented
  in a  :ref:`workflow <sec-resources-workflows>`
- A :ref:`configuration file <sec-resources-configs>`, providing all the values
  that your :ref:`script(s) <sec-resources-scripts>` need

For guidance on creating these files, refer to the :ref:`sec-resources` section.
For the rest of the :ref:`sec-usage` section, and subsections, we will use the
example script, workflow, and configuration file generated by running:

.. literalinclude:: ../200_quickstart.cmd
   :lines: 4-5

The command above by default produces the example provided by the **core**
**cijoe** package, however, as you can see in section :ref:`sec-packages`, then
there are multiple packages and examples for using them are produced in the same
manner:

* ``cijoe --example qemu``

  - Producing example resources for the qemu package

* ``cijoe --example linux``

  - Producing example resources for the Linux package

The following sections describe the use of :ref:`sec-resources-scripts`,
:ref:`sec-resources-workflows`, the remainder of the current section
provides subsections with information provided for reference on
all :ref:`sec-usage-cli`, :ref:`sec-usage-evars`, and behaverial information
on :ref:`sec-usage-sp`.


.. _sec-usage-cli:

CLI Arguments
=============

When in doubt, then you can always consult the ``cijoe`` command-line arguments:

.. literalinclude:: ../050_usage_help.cmd

Which yields the following output:

.. literalinclude:: ../050_usage_help.out


.. _sec-usage-sp:

Search Paths
============

The :ref:`sec-usage-cli` for the positional argument, and config-files 
(``--c / --config``) and workflows (``-w / --workflow``) by default search for files
named ``cijoe-workflow.yaml`` and ``cijoe-config.toml``, respectfully. These files
are searched for, in order, in the following locations:

``$PWD``
   In your current working directory

``$PWD/.cijoe``
   In the subfolder named ``.cijoe`` of your current working directory

``$HOME/.cijoe``
   In a subfolder of your home-directory named ``.cijoe``

``$HOME/.config/cijoe``
   In a subfolder of of the ``.config`` folder in your home-directory named
   ``cijoe``

In addition to these search paths for the **cijoe** configuration file, then
the :ref:`environment variable <sec-usage-evars>` named ``CIJOE_DEFAULT_CONFIG``
can be utilized to directly set the path to the configuration file instead
providing it via the ``--config`` command-line option.

.. _sec-usage-evars:

Environment Variables
=====================

The following environment variables modify the bahavior of the  ``cijoe``
command-line tool.

CIJOE_DISABLE_SSH_ENV_INJECT
    When this is set, the environment variables passed to 
    ``cijoe.run(..., env={your: vars})`` will not be passed on to the SSH
    transport.

CIJOE_DEFAULT_CONFIG
    When set, the value will be used as the default for the command-line 
    ``-c/--config`` argument.

CIJOE_DEFAULT_WORKFLOW
    When set, the value will be used as the default for the positional
    command-line argument.
