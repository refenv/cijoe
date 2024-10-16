.. _sec-resources-workflows:

Workflows
=========

Workflows provide the means to collect the execution of a commands and scripts,
in an ordered fashion, with a required doc-section. You can then "run" the
workflow by invocing:

.. literalinclude:: ../420_usage_workflow_all.cmd
   :language: bash


.. _sec-resources-workflows-content:

Content Overview
----------------

As to the content of a workflow, then at first glance, then it might feel a bit
similar to GitHub Actions workflow, but dramatically simpler since:

* There are **no** logic operators

* There **is** simple variable substitution using

  - Values from configuration file
  - Values from environment variables on **initiator**

* Minimal amount of "magic" keys

  - ``doc``: Describe what the workflow does using multi-line plain-text
  - ``steps``: Ordered list of scripts, to inline-commands, to run

Let's take a look at what the workflow file produced by ``cijoe --example``
looks like:

.. literalinclude:: ../../cijoe-workflow.yaml
   :language: yaml


.. _sec-resources-workflows-inline-commands:

Inline Commands
---------------

...


.. _sec-resources-workflows-step-arguments:

Step Arguments
--------------

...


.. _sec-resources-workflows-linting:

Linting
-------

When you write a workflow yourself it can be nice to check whether it is valid
without running it. You can do so by running:

.. literalinclude:: ../300_lint.cmd
   :language: bash
