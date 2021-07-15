.. _sec-installation:

Installation
============

**cijoe** is distributed as a Python package (named `cijoe
<https://pypi.org/project/cijoe/>`_) via the Python Package Index (`PyPi
<https://pypi.org>`_) and installable via ``pip3``. Extensions to **cijoe** are
referred to as **cijoe packages**, these are conventionally named
``cijoe-pkg-<project_name>``.

Do a **user-local** install of ``cijoe`` and the **cijoe package** named
``cijoe-pkg-example`` using ``pip3``:

.. code-block:: bash

  pip3 install --user cijoe cijoe-pkg-example

The **user-local** install (``--user``) isolates the installation to the
current user account, instead of installing it **system-wide** and potentially
colliding with system packages. The **cijoe package** ``cijoe-pkg-example`` is
not strictly needed, however, the resources provided with the package will be
used through the documentation.

.. warning:: Take care installing **cijoe** and **cijoe packages** using the
   same installation method. That is, do **not** mix installation-methods of
   **user-local**, **system-wide**, and **virtual-env**  as that will mess up
   how **cijoe** resolves paths to the resources provided by a package.

.. tip:: To create your own **cijoe package**, have a look at the
   :ref:`sec-packages` section.

====

Check that it installed correctly, by invoking one of **cijoe** command-line
tools:

.. literalinclude:: cij_runner.cmd
   :language: bash

It should provide a usage page that looks like this:

.. literalinclude:: cij_runner.out
   :language: bash

If this does not produce the usage-page of the runner, then your system is
probably not configured to look for binaries in the location that ``pip3
install --user`` installs them to.

For example, on Linux then the output of ``python3 -m site --user-base`` is not
in your environment-variable ``$PATH``. You can quickly fix this by adding it
to your shell, e.g. for Bash do:

.. code-block:: bash

    echo "export PATH=\"$PATH:$(python3 -m site --user-base)/bin\"" >> ~/.bash_profile

Once you have verified that **cijoe** is installed correctly and that you can
execute the command-line tools, then procede to :ref:`sec-running`.

.. _Bash: https://www.gnu.org/software/bash/
.. _Python 3: https://www.python.org/
