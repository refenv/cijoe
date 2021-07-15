.. _sec-packages:

===================
 Creating Packages
===================

Here you will find directions on creating a **cijoe package** for your project.

**cijoe packages** abide by the naming convention ``cijoe-pkg-<project_name>``,
additionally, a certain directory-layout is expected, along with helper-scripts
and utilities aka `boilerplate
<https://en.wikipedia.org/wiki/Boilerplate_code>`_.
To get the **boiler-plate** right, then the **cijoe package**
`cijoe-pkg-example`_ is provided; use it as a **template** for your own
package-creation, see the following details on how to do just that, along with
:ref:`sec-packages-conventions` information.

If you are not looking to create package, then skip that section and read the
remaining sections for an overview of what a package contains and the
requirements for each entity.

.. _sec-packages-template:

Package Template
================

The following will go through how to utilize the example to create a package
for your project. Start by downloading and unpacking the `zip-file
<https://github.com/refenv/cijoe-pkg-example/archive/refs/heads/main.zip>`_, if
you have ``wget`` and ``unzip`` then run:

.. literalinclude:: fetch.cmd
   :language: bash
   :lines: 3-

Once retrieved then modify the following files::

  setup.py
  Makefile
  README.rst

Go through the files, replacing all instances of "**example**" with the name of
your project, make certain you modify ``setup.py`` appropriately, providing the
correct author information, license, version, email, and all the other Python
package properties.

.. tip:: To easily match your **cijoe** package version to your project, then
   use the same version number. For example, if you were creating a **cijoe**
   package for **fio** version 3.14, then set ``version=3.14.0`` in
   ``setup.py``. Then use the **patch-version** of the version number to
   indicate changes to the **cijoe package** itself.

.. tip:: ``pip`` distinguishes between release and pre-release versions. A
   pre-release is created by adding ``.devN`` version number where ``N`` is a
   number, e.g. ``version=3.14.dev1``.
   By doing so then ``pip install --user cijoe-pkg-fio`` will install version
   **3.14**, and ``pip install --user --pre cijoe-pkg-fio`` will install
   version **3.14.dev1**.

Once you have done so, then run the **selftest** to see
that things are plumbed up correctly::

  make
  make selftest-view

.. note:: This will build and install your package as a user-local package. The
   installation method of ``pip install --user`` is the preferred means of
   installing **cijoe** and **cijoe** packages, thus the **Makefile** does so
   by default.

Repositories for **cijoe** and **cijoe packages** live on GitHUB, it thus makes
use of GitHUB workflows to automatically run the above-mentioned **selftest**
and deploy to PyPi.

.. _sec-packages-conventions:

Conventions and Style
---------------------

The portion of a **cijoe package** which consists of Bash-scripts, namely,
:ref:`sec-packages-testcases`, :ref:`sec-packages-hooks`, and
:ref:`sec-packages-modules`, and :ref:`sec-packages-refenvs`, should aim at
following `Google Shell Style Guide`_, with the following additions and
exceptions.

File-names
~~~~~~~~~~

To avoid overwriting files from other packages, then follow the rule/convention
below.

1. Prefix filenames with the package name followed by an underscope. This
   applies to reference environments, modules, hooks, testplans, testsuites,
   and testplans.

E.g. testcases in the ``cijoe-pkg-example`` are all prefixed with ``example_``.
Resulting in names such as ``example_01_minimal.sh``,
``example_02_output_annotation.sh``, ``example_03_filetransfer.sh`` etc.

Module-separator
~~~~~~~~~~~~~~~~

The `Google Shell Style Guide`_ defines ``::`` as a package/module separator.
This is an exceptionally poor choice of separator for Bash-scripts as it breaks
Bash-auto-completion. Thus following the exception to the style guide:

1. Use ``.`` as module-separator.

E.g. for a module named **example** create functions as in the following::

  example.foo() {

  }

  example.bar() {

  }

By using ``.`` we allow for proper Bash-auto-completion and readability making
Bash scripts look more like Python and less like C++ and PHP.

.. note:: The ``::`` was used by **cijoe**, as it was adheering to the `Google
   Shell Style Guide`_, up until version version **v0.2.0**. From that version
   and onwards the module-separator is ``.``. However, to avoid breaking
   existing package modules, hooks, and testcases, then a "legacy" module was
   added. At some point this will also be removed.

.. _sec-packages-refenvs:

Reference Environment(s)
========================

The main instrumental entity in **cijoe** is the :ref:`sec-environment`. To
assist in the creation of these, then a **cijoe package** provide examples aka
**reference environments**. These serve as the name suggests, as a reference
for the user of a given **cijoe package** when creating an
:ref:`sec-environment` using a what a given package provides.

This includes the variables required by :ref:`sec-packages-testcases`,
:ref:`sec-packages-hooks`, and :ref:`sec-packages-modules`. Reference
environments double as light documentation of your package, by providing
helpful comments on-top of the exported variable declarations.

.. note:: Reference environments are installed into the ``$CIJ_ENVS``
   directory, jump to the :ref:`sec-shell`, to see how to inspect the variables
   defining **cijoe**. Since all **cijoe packages** install modules into the
   same directory, this is why :ref:`sec-packages-conventions` are needed.

Example
-------

An example is provided with the `cijoe-pkg-example`_ it looks like this:

.. literalinclude:: cijoe-pkg-example-main/envs/example_env.sh
   :caption: cijoe-pkg-example/envs/example_env.sh
   :language: bash

.. _sec-packages-modules:

Modules
=======

Modules are Bash-scripts providing functions for common tasks. With **cijoe**
the following core Bash modules are included:

* `ssh <https://github.com/refenv/cijoe/blob/master/modules/ssh.sh>`_, wrapping
  ssh for remote command execution, file-transfer etc.
* `test <https://github.com/refenv/cijoe/blob/master/modules/test.sh>`_,
  conventions for testcases pass/fail status etc.
* `cij <https://github.com/refenv/cijoe/blob/master/modules/cij.sh>`_, output
  annotation, command execution mapped to **ssh** when defined in the
  environment and locally when explicitly configured to

A Bash module must have a name and a matching namespace, e.g. the following
module named ``example`` is defined in the file named ``example.sh``, the
functions defined in the module must be prefixed with ``example.func_name``.

A Bash module **must** have an **environment-verification** function and it
**must** be named ``<module_name>.env``.

Each other function defined in the Module should call this function as the
first thing it does.

.. tip:: Only create a module once you find that your
   :ref:`sec-packages-testcases` are repeating the same commands, and
   maintaining differences is error-prone. The ``env`` comes in handy here as
   it ensures that the required variables are well-defined in the
   :ref:`sec-environment`. The **env-verification** might be the only function
   you need in your module.

.. note:: Modules are installed into the ``$CIJ_MODULES`` directory, jump to
   the :ref:`sec-shell`, to see how to inspect the variables defining
   **cijoe**. Since all **cijoe packages** install modules into the same
   directory, this is why :ref:`sec-packages-conventions` are needed.

Example
-------

An example is provided with the `cijoe-pkg-example`_ it looks like this:

.. literalinclude:: cijoe-pkg-example-main/modules/example.sh
   :caption: cijoe-pkg-example/modules/example.sh
   :language: bash

For additional examples look at x, y, and z.

.. _sec-packages-hooks:

Hooks
=====

**Hooks** are Bash-scripts which are intended to be executed in a manner
similar to ``setup``/``teardown`` in a **unittest** framework.  The
:ref:`sec-packages-testplans` control which entities the **hooks** are executed
**before/after**, such as individual :ref:`sec-packages-testcases`, entire
:ref:`sec-packages-testsuites`, and/or everything in defined in
:ref:`sec-packages-testplans`.

**Hooks** come in handy for different use-cases:

* Probing the **test-target** for information, collecting HW information,
  operating system Kernel version, tool and library version etc. All the
  information that potentially have an impact on the thing you are doing.
* Measuring **test-target** side-effects, e.g. how much have been read/written
  to a storage device, by retrieving Smart Logs before and after running
  IO-intensive :ref:`sec-packages-testcases`
* Manipulating the **test-target**, such as loading/unloading drivers,
  mounting/unmounting file-systems, resetting operating system page-caches etc.

The above are just to name a few, for an example see the following section.

.. note:: Hooks are installed into the ``$CIJ_HOOKS`` directory, jump to the
   :ref:`sec-shell`, to see how to inspect the variables defining **cijoe**.
   Since all **cijoe packages** install hooks into the same directory, this is
   why :ref:`sec-packages-conventions` are needed.

.. _sec-packages-hooks-example:

Example
-------

Defining the **before/after** portion is handled by naming the hook
accordingly. That is, for a hook named ``example_probe``, create the files:
``example_probe_enter.sh`` and ``example_probe_exit.sh`` as in the following
example.

.. literalinclude:: cijoe-pkg-example-main/hooks/example_probe_enter.sh
   :caption: cijoe-pkg-example/hooks/example_probe_enter.sh
   :language: bash

.. literalinclude:: cijoe-pkg-example-main/hooks/example_probe_exit.sh
   :caption: cijoe-pkg-example/hooks/example_probe_exit.sh
   :language: bash

.. _sec-packages-testcases:

Testcases
=========

Testcases are Bash-scripts which utilize **cijoe** to invoke commands on a
**test-target** and check whether they provide the expected return codes when
doing so.

* Invoke commands by running ``cij.cmd``
* Transfer files using ``cij.push``/``cij.pull``
* Indicate success via ``test.pass``/``test.fail``

.. note:: Testcases are installed into the ``$CIJ_TESTCASES`` directory, jump
   to the :ref:`sec-shell`, to see how to inspect the variables defining
   **cijoe**. Since all **cijoe packages** install testcases into the same
   directory, this is why :ref:`sec-packages-conventions` are needed.

.. _sec-packages-testcases-example:

Example
-------

A minimal **testcase** contains the following:

.. literalinclude:: cijoe-pkg-example-main/testcases/example_01_minimal.sh
   :caption: cijoe-pkg-example/testcases/example_01_minimal.sh
   :language: bash

Addional examples are provided with 

.. _sec-packages-testsuites:

Testsuites
==========

A testsuites is a collection of :ref:`sec-packages-testcases`. By convention
then each file ending with ``.suite`` in the ``testsuites`` directory is a
**testsuite**. A ``.suite`` file is a text-file consisting of a list of
**testcase** filenames separated by a newline.

For a **testsuite** to be valid then it must contain only names of files that
exists in the ``$CIJ_TESTCASES`` directory. The introspection tool
``cij_tlint`` checks this, and it is executed when you run the **selftest**.

Testsuites are used in :ref:`sec-packages-testplans` to avoid repetition when
declaring the :ref:`sec-packages-testcases` to run.

.. note:: Testsuites are installed into the ``$CIJ_TESTSUITES`` directory, jump
   to the :ref:`sec-shell`, to see how to inspect the variables defining
   **cijoe**. Since all **cijoe packages** install testsuites into the same
   directory, this is why :ref:`sec-packages-conventions` are needed.

.. _sec-packages-testsuites-example:

Example
-------

 Here is an example:

.. literalinclude:: cijoe-pkg-example-main/testsuites/example_all.suite
   :caption: cijoe-pkg-example/testsuites/example_all.suite
   :language: bash

.. _sec-packages-testplans:

Testplans
=========

A **testplan** describes **what** to run. Specifically, which
:ref:`sec-packages-testcases`/:ref:`sec-packages-testsuites` to run, along with
:ref:`sec-packages-hooks` and the option to provide default-values for
environment variables otherwise defined in the **environment definition**.

.. note:: Testplans are installed into the ``$CIJ_TESTPLANS`` directory, jump
   to the :ref:`sec-shell`, to see how to inspect the variables defining
   **cijoe**. Since all **cijoe packages** install testplans into the same
   directory, this is why :ref:`sec-packages-conventions` are needed.

.. _sec-packages-testplans-example:

Example
-------

Here is an example:

.. literalinclude:: cijoe-pkg-example-main/testplans/example_01.plan
   :caption: cijoe-pkg-example/testplans/example_01.plan
   :language: bash

For additional examples see x, y, and z.

.. _sec-packages-testfiles:

Testfiles
=========

Testfiles are **auxilary** files that a **cijoe package** can provide to the
user.  These should be small in terms of size and primarily text-based formats.
Things such as configuration-files, examples of data-formats, inputs to tools,
performance requirements for known devices, device properties to verify and
check for.

.. note:: Testfiles are installed into the ``$CIJ_TESTFILES`` directory, jump
   to the :ref:`sec-shell`, to see how to inspect the variables defining
   **cijoe**. Since all **cijoe packages** install testplans into the same
   directory, this is why :ref:`sec-packages-conventions` are needed.


.. _Google Shell Style Guide: https://google.github.io/styleguide/shellguide.html
.. _cijoe-pkg-example: https://github.com/safl/cijoe-pkg-example
