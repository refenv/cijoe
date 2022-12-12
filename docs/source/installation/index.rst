.. _sec-installation:

Installation
============

**cijoe** is distributed as a Python package (named `cijoe
<https://pypi.org/project/cijoe/>`_) via the Python Package Index (`PyPi
<https://pypi.org>`_) and installable via ``pip3``. Extensions to **cijoe** are
referred to as **cijoe packages**, these are conventionally named
``cijoe-pkg-<project_name>``.

Do a **user-local** install of ``cijoe`` and a couple of useful **cijoe
packages** using ``pip``:

.. code-block:: bash

  python3 -m pip install --user \
   cijoe \
   cijoe-pkg-qemu \
   cijoe-pkg-linux

The **user-local** install (``--user``) isolates the installation to the
current user account, instead of installing it **system-wide** and potentially
colliding with system packages.

Check installation
------------------

Check that it installed correctly, by invoking the **cijoe** command-line tool:

.. literalinclude:: joe.cmd
   :language: bash

It should provide a usage page that looks like this:

.. literalinclude:: joe.out
   :language: bash

If this does not produce the help-page as above, then your system is
probably not configured to look for binaries/executables in the location that
``python3 -m pip install --user`` installs them to.

For example, on Linux then the output of ``python3 -m site --user-base`` is not
in your environment-variable ``$PATH``. You can quickly fix this by adding it
to your shell, e.g. for `Bash <https://www.gnu.org/software/bash/>`_ do:

.. code-block:: bash

    echo "export PATH=$PATH:$(python3 -m site --user-base)/bin" >> ~/.bash_profile

When on a Mac, then add it to ZSH instead:

.. code-block:: bash

    echo "export PATH=$PATH:$(python3 -m site --user-base)/bin" >> ~/.zshrc

Once you have verified that **cijoe** is installed correctly and that you can
execute the command-line tool, then procede to :ref:`sec-resources-workflows`.
