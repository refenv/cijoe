.. _sec-usage:

=======
 Usage
=======

Running workflows, writing worklets, calling **cijoe** from any Python module.
The testrunner worklet and pytest-plugin.

Environment Variables
=====================

There are a couple of environmetn variables which change the behaviour of
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

Workflows
=========

...

Testrunner
==========

The worklet... and the pytest-plugin...

.. automodule:: cijoe.pytest_plugin.hooks_and_fixtures
   :members:
   :undoc-members:
   :inherited-members:
