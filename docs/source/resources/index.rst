.. _sec-resources:

===========
 Resources
===========

In **cijoe** all of :ref:`sec-resources-auxiliary`,
:ref:`sec-resources-workflows`, :ref:`sec-resources-scripts`,
:ref:`sec-resources-configs`, :ref:`sec-resources-templates`, and
:ref:`sec-resources-perfreqs` are all considered dynamically loadable
resources.

They are automatically collected from installed **cijoe** packages, as well as
the current working directory of the command-line tool.

Via Python the resources are accessbile like so::

  from cijoe.core.resources import get_resources

  resources = get_resources()

The command-line, provides a quick way to lookup all available resources:

.. literalinclude:: command.cmd
   :language: bash


.. literalinclude:: command.out
   :language: bash


.. toctree::
   :maxdepth: 2
   :includehidden:
   :hidden:

   configs/index.rst
   workflows/index.rst
   scripts/index.rst
   templates/index.rst
   perfreqs/index.rst
   auxiliary/index.rst
