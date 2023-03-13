.. _sec-installation:

Installation
============

**cijoe** is distributed as a Python package (named `cijoe
<https://pypi.org/project/cijoe/>`_) via the Python Package Index (`PyPi
<https://pypi.org>`_). Extensions to **cijoe** are referred to as **cijoe
packages**, these are conventionally named ``cijoe-pkg-<project_name>``.

Install ``cijoe``, in a virtual-environment via ``pipx``, along with a couple
of useful **cijoe packages**:

.. code-block:: bash

  python3 -m pipx install cijoe --include-deps
  python3 -m pipx inject cijoe-pkg-qemu
  python3 -m pipx inject cijoe-pkg-linux

.. note:: Make sure that you follow the recommendation above. The
   ``--include-deps`` ensure that the ``pytest`` CLI is made available
   alongside ``cijoe``. And by having both in the same virtual environment,
   then **pytest** can use the **cijoe** pytest-plugin and **cijoe** can invoke
   the ``pytest`` CLI.

Installation of Python packages via ``pip`` should be done in a virtual
environment. For command-line utilities such as ``cijoe`` then ``pipx``
provides a convenient means, designed for exactly this usecase, to setup the
virtual environment and make the command-line utilities provided within available
as any other command-line utility. It is thus the recommended approach for
``cijoe``.

Check installation
------------------

Check that it installed correctly, by invoking the **cijoe** command-line tool:

.. literalinclude:: joe.cmd
   :language: bash

It should provide a usage page that looks like this:

.. literalinclude:: joe.out
   :language: bash

If this does not produce the help-page as above, then ensure that ``pipx`` is
installed and your ``PATH`` setup correctly. For example, by running the
following:

.. code-block:: bash

  python3 -m pip install --user pipx
  python3 -m pipx ensurepath

And then reload your shell.

Once you have verified that **cijoe** is installed correctly and that you can
execute the command-line tool, then procede to :ref:`sec-resources-workflows`.
