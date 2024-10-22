.. _sec-resources-auxiliary:

Auxiliary
=========

Auxiliary files are files which do not fall under any of the other kinds of 
resources. These are useful for providing things like scripts for ``fio``, 
configuration files for some system, hardware specifications, and other means
of data.

For the **automatic collection** of resources to find auxiliary files, they 
must either:

a. be located in sub directory of the current working directory (``cwd``) 
   called ``auxiliary``, or
b. be a :python:`Python <>` script that is **not** considered a **cijoe**
   :ref:`script <sec-resources-scripts>`.

Auxiliary files can be accessed in the ``auxiliary`` resources.

.. code-block:: python

   resources = get_resources()
   template_path = resources["auxiliary"]