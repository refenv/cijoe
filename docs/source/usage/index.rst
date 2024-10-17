.. _sec-usage:

=======
 Usage
=======

Running workflows, writing scripts, calling **cijoe** from any Python module.
The testrunner script and pytest-plugin.

Environment Variables
=====================

There are a couple of environment variables which change the behaviour of
**cijoe**. Primarily the behavior of the ``cijoe`` command-line tool.

* ``CIJOE_DISABLE_SSH_ENV_INJECT``, when this is set, then environment
  variables passed to ``cijoe.run(..., env={your: vars})`` won't be pased on to
  the SSH transport.

* ``CIJOE_DEFAULT_CONFIG``,, when set, the value will be used as default value
  for the command-line ``-c/--config`` argument.

* ``CIJOE_DEFAULT_WORKFLOW``, when set, the value will be used as default value
  for the command-line ``-w/--workflow`` argument.

Command-line
============

The command-line tool is aptly named ``cijoe``.

**cijoe** scripts
=================

To create a **cijoe** Python script, run command ``cijoe --script``, which
will create a python script with the code necessary for running **cijoe**.

The script is executed by running ``cijoe ./cijoe-script.py --config
path/to/config.toml``.

.. literalinclude:: ../../../src/cijoe/core/scripts/example.py
   :language: python

Workflows
=========

...

Testrunner
==========

The script... and the pytest-plugin...

.. automodule:: cijoe.pytest_plugin.hooks_and_fixtures
   :members:
   :undoc-members:
   :inherited-members:

...