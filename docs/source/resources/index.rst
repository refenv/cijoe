.. _sec-resources:

===========
 Resources
===========

In **cijoe** the most essential **resources** are :ref:`sec-resources-scripts`,
:ref:`sec-resources-workflows`, and :ref:`sec-resources-configs`.
In addition to these are :ref:`Auxiliary files <sec-resources-auxiliary>`, and
:ref:`sec-resources-templates`.

Resources are **automatically collected** from installed
**cijoe** :ref:`sec-packages` as well as the current working directory
(``cwd``) and any sub-directory with a max depth of 2.

When writing a :ref:`script <sec-resources-scripts>` then resources are accessed
as follows::

  from cijoe.core.resources import get_resources

  resources = get_resources()


This is convenient as you don't need to worry about the location of
your :ref:`sec-resources-auxiliary` files -- they are readily available.

On the command-line a quick way to list all available resources:


.. literalinclude:: ../150_cijoe_resources.cmd
   :language: bash


.. literalinclude:: ../150_cijoe_resources.out
   :language: bash


This is useful when you want to create a modified version of a script, review
its details, or verify that all expected resources are available in your
installation.

There are gold hidden in the **resources** for the example, **cijoe** provides a
bash-completion script. 

The following sections describe the different types of resources.

.. toctree::
   :maxdepth: 2
   :includehidden:
   :hidden:

   templates/index.rst
   auxiliary/index.rst
