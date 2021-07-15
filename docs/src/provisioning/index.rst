.. _sec-provisioning:

========================
Provisioning using CIJOE
========================

**cijoe** does not have a pre-defined pattern or setup for provisioning your
**test-target(s)**. However, since **cijoe** already knows about your
**test-target** via the :ref:`sec-environment` and it has Bash-modules for
common tasks, then one can conviently write a script taking take of
provisioning tasks before :ref:`sec-running`.

That is, to do things like following examples.

.. _sec-provisioning-commands:

Command Example(s)
==================

Build your project, producing a deb-package, on your **dev box**, then transfer
it to your **test-target** for installation::

  # Build on your *dev box*
  make deb

  # Transfer and install on your *test-target**
  cij.push "my_project.deb"
  cij.cmd "dpkg -i my_project.deb"

Transfer project-source to **test-target**, in order to build and install on
the **test-target** itself::

  cij.push "my_project_source.tgz"
  cij.cmd "tar xzf my_project_source.tgz"
  cij.cmd "cd my_project_source && make && make install"

You can do the above by running the commands in the :ref:`sec-shell` as the
**cijoe shell** as it has access to the **cijoe** modules and the **environment
definition**. However, to avoid having to retype the same commands over and
over, then you can it a small script to your workflow doing the above instead.

.. _sec-provisioning-snippet:

Scripting Snippet
=================

Use the following snippet to give your script access to **cijoe** and the
**test-target** described by the :ref:`sec-environment` named
``target_env.sh``:

.. literalinclude:: scripting_snippet.cmd
   :language: bash

.. note:: This snippet is mostly useful when adding **cijoe** to a
   build-system, or **CI/CD** pipelines, that is, in situations where you just
   want to run a command or two within the confines of the **CI/CD** system.
   For a more elaborate approach, see the :ref:`sec-provisioning-script`.

.. _sec-provisioning-script:

Scripting Example
=================

The following is an example of the common tasks one might be doing, during a
regular development workflow/cycle: **build**, **deploy**, **run**,
**postprocess**, and **analyze** the results.

In case your development **tools** can be instrumented from the command-line,
then you can glue them together in a looks something like this:

.. literalinclude:: custom_script.sh
   :language: bash
   :emphasize-lines: 7,60

Here is what usage of such as script would look like:

.. literalinclude:: custom_script.cmd
   :language: bash

.. literalinclude:: custom_script.out
   :language: bash
   :lines: 3-

The above is just an example of separating your workflow into tasks and using
basic scripted commands to glue the tasks from different toolchains together.
And adding to that, tying these tasks together for your project and utilization
of **test-targets**. An infinite amount of ways of doing these sort of things
exists, do whatever fits you and your projects.
