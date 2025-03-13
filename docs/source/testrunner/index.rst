.. _sec-usage-testrunner:

============
Testrunner
============

**cijoe** provides a test runner implemented as a :pytest:`pytest <>` plugin,
wrapped in a **cijoe** script named :ref:`core.testrunner <sec-packages-core-testrunner>`. 
The plugin is included with the **cijoe** package, but to use it, you must ensure 
that :pytest:`pytest<>` has access to the rest of the **cijoe** virtual
environment (venv) and that the ``pytest`` command-line tool is available.

This can be easily achieved by using **pipx** to install **cijoe** with its
dependencies:

.. code-block:: bash

   pipx install cijoe --include-deps

The test runner can be used in two main ways:

1. Directly via the :pytest:`pytest <>` command-line: ``pytest --config cijoe-config.toml``

2. Via a **cijoe** workflow, with a step using the :ref:`core.testrunner 
   <sec-packages-core-testrunner>`, executed through the ``cijoe`` command-line tool.

While the first method may be more familiar and require no further explanation,
the test runner was specifically designed to be used within a **cijoe**
workflow and command-line interface.

The intent of using :pytest:`pytest <>` in this context is based on the
assumption that, since **cijoe** is a Python project and the :ref:`scripts
<sec-resources-scripts>` are also Python-based, the users of **cijoe** are
likely to be familiar with writing tests using :pytest:`pytest <>`. They are
presumed to be aware of general pytest usage and capabilities, allowing them to
leverage that prior knowledge.

However, there are key differences in how :pytest:`pytest <>` is applied here,
which may seem unfamiliar or awkward to experienced :pytest:`pytest <>` users.
The focus of the following subsections is to highlight and clarify these
essential differences.

Usage
=====

In a :ref:`workflow <sec-resources-workflows>` the :ref:`core.testrunner
<sec-packages-core-testrunner>` is inserted as a step with arguments like below:

.. code-block:: yaml

   - name: run_tests
     uses: core.testrunner
     with:
       args: '-k "filtering" my_tests'
       random_order: false
       run_local: false

Here you see three "special" arguments to the testrunner:

args
  These arguments are passed verbatim to **pytest**, resulting in the following
  invocation:

  .. code-block:: bash

    pytest \
      --config cijoe-config.toml \
      --output output \
      -k "filtering" my_tests

  The key difference between invoking the ``pytest`` command-line tool directly
  and using the **cijoe** script :ref:`core.testrunner <sec-packages-core-testrunner>`
  in the **cijoe** workflow is that the latter integrates the **pytest** report into 
  **cijoe**, producing a cohesive and standalone report.

random_order
  This option **scrambles** the order in which tests are executed. It is
  generally recommended, as it helps reduce inter-test dependencies and
  assumptions about the environment's state.

run_local
  This option can take some time to understand fully. It controls where
  **pytest** is executed.

  - When ``run_local: false``, the behavior is "normal" — the
    **pytest** command-line tool is executed on the **initiator**, and
    the :ref:`configuration-file <sec-resources-configs>` provided to the
    **cijoe** command-line tool is passed verbatim to **pytest**.

  - When ``run_local: true``, this behavior changes. The **pytest**
    command-line tool is executed on the **target** instead. Before execution,
    the provided :ref:`configuration-file <sec-resources-configs>` is cloned,
    modified by removing the transport section, and then transferred to the
    **target**. Once transferred, **pytest** is executed on the **target** using
    the modified configuration file. Finally, the **pytest** report generated on
    the **target** is transferred back to the **initiator** for integration into
    the **cijoe** report.
