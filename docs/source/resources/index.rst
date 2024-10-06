.. _sec-resources:

===========
 Resources
===========

In **cijoe** the most essential **resources** are :ref:`sec-resources-scripts`,
:ref:`sec-resources-configs`, and :ref:`sec-resources-workflows`.
In addition to these are :ref:`auxiliary files <sec-resources-auxiliary>`,
:ref:`sec-resources-templates`, and :ref:`sec-resources-perfreqs`.

Resources are **automatically collected** from installed
**cijoe** :ref:`sec-packages` as well as the current working directory
(``cwd``).

In a :ref:`script <sec-resources-scripts>`, resources can be accessed as
follows::

  from cijoe.core.resources import get_resources

  resources = get_resources()


This is convenient as you don't need to worry about the location of
your :ref:`sec-resources-auxiliary` files -- they are readily available.

On the command-line a quick way to list all available resources:


.. literalinclude:: command.cmd
   :language: bash


.. literalinclude:: command.out
   :language: bash


This is useful when you want to create a modified version of a script, review
its details, or verify that all expected resources are available in your
installation.

The following sections describe the different types of resources.

.. toctree::
   :maxdepth: 2
   :includehidden:
   :hidden:

   scripts/index.rst
   configs/index.rst
   workflows/index.rst
   templates/index.rst
   perfreqs/index.rst
   auxiliary/index.rst
