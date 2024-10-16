.. _sec-usage-testrunner:

Testrunner
==========

**cijoe** provides a plugin for :pytest:`pytest <>`. This :pytest:`pytest <>`
plugin is usable in multiple, either driven by the execution of the **pytest**
command-line tool, as one would often do, this is described in the following
sections, along with api docs of the plugin.

However, it becomes even more interesting when used via the **cijoe** testrunner
script named ``core.testrunner``. This can be conveniently added to your
**workflow**, facilitating the a workflow of; prep, deploy, test, report.

The **pytest** reporting is integrating into the **cijoe** workflow report,
thereby providing a convenient one-stop-shop.

pytest plugin
-------------

.. automodule:: cijoe.pytest_plugin.hooks_and_fixtures
   :members:
   :undoc-members:
   :inherited-members:
