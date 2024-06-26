.. image:: _static/logo.png
   :alt: CIJOE

==================================================
 cijoe: tools for systems development and testing
==================================================

**cijoe** is a means to collect, and loosely formalize, the bits and pieces
commonly used during systems development in order to obtain an **automated**
and **reproducible** workflow.

Quickstart
==========

The following will install **cijoe**, produce an example configuration and
workflow, and execute the workflow using the configuration.

.. literalinclude:: 200_quickstart.cmd
   :language: bash

**cijoe** is silent by default, as in, does not print out anything unless
errors occur. However, at the end a HTML-report is produced and opened
providing an overview of the workflow invocation.

If you do not want the HTML report, then you can invoke ``cijoe`` with ``-n`` /
``--no-report``.
If you want ``cijoe`` to be more verbose, then increase the log level with
``-l``/``--log-level`` or enable the monitor ``-m``/``--monitor``.

For a thorough description, the rest of the documentation is provided with the
:ref:`sec-introduction` serving as the starting point.

.. toctree::
   :maxdepth: 2
   :includehidden:
   :hidden:

   introduction/index.rst
   prerequisites/index.rst
   installation/index.rst
   usage/index.rst
   resources/index.rst
   packages/index.rst
