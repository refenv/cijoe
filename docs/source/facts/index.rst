.. _sec-resources-facts:

=======
 Facts
=======

A **fact** is something a step found out during a run: the kernel a target
booted, the names a guest gave its devices, whether a host's IOMMU is on. The
:ref:`configuration <sec-resources-configs>` says what a task wants, and a run
never changes it. Facts say what the run observed. A
:ref:`script <sec-resources-scripts>` writes them, and the steps after it read
them.


Motivation
==========

Before facts, a step that found something out had nowhere to put it. A later
step could not read it, so each producer wrote a file of its own, and a later
run loaded that file as one more ``--config``. That has three problems.

* The observation reaches only the next run, never the next step of the same
  run.

* Once loaded, the observation is configuration. It can override what a person
  configured, and nothing says that it did.

* Nothing records which step found what, or when.

Facts keep observations apart from configuration. Steps in the same run read
them, and so can a later run. Every write is saved, the report shows the facts,
and each step's state lists the keys it wrote.


Example
=======

The ``core.facts`` example has a script observe the **target**, and the steps
after it use what the script found. Emit it and run it with:

.. code-block:: bash

   cijoe --example core.facts
   cd cijoe-example-core.facts
   cijoe --monitor

The configuration says what the task wants, at least one CPU:

.. literalinclude:: ../../../src/cijoe/core/configs/example_config_facts.toml
   :language: toml

The script observes the target's kernel release and CPU count, and keeps them
as the facts ``target.kernel`` and ``target.cpus``:

.. literalinclude:: ../../../src/cijoe/core/scripts/example_script_facts.py
   :language: python
   :pyobject: main

The task's second step shows the facts, and its third checks the observation
against what the configuration wants:

.. literalinclude:: ../../../src/cijoe/core/tasks/example_task_facts.yaml
   :language: yaml

After the run, ``cijoe-output/facts.toml`` holds what was observed, here on a
WSL2 workstation:

.. code-block:: toml

   [target]
   kernel = "6.6.87.2-microsoft-standard-WSL2"
   cpus = 16

The report's **Facts** tab lists the same facts, each with the step that last
wrote it, here ``observe`` for both. A step that wrote facts has a **facts**
button, which shows them with their values; ``task.state`` lists, for each
step, the keys it wrote.


Writing and reading facts
=========================

A script writes facts on ``cijoe.facts``, with dotted keys as for
:ref:`getconf() <sec-resources-scripts-getconf>`:

.. code-block:: python

   cijoe.facts.set("guest.kernel", "7.3.0")                 # replace
   cijoe.facts.update("guest.devices.nvme0", {"bdf": bdf})  # merge into a table
   cijoe.facts.delete("guest.devices.gpu0")                 # remove

   kernel = cijoe.facts.get("guest.kernel", "unknown")

A value is anything TOML can hold: strings, numbers, booleans, lists and
tables; a write of anything else, such as ``None``, raises ``TypeError`` and
changes nothing. ``set()`` replaces what was at the key, which is how a script
brings a fact up to date when it observes again, for example after a device is
unplugged. ``get()`` returns a copy, so changing what it returned changes no
fact.

A task reads facts in a step's ``with``, as ``{{ facts.guest.kernel }}`` or in
a block such as ``{% if facts.guest.gpu %}``. Other variables in a task are
substituted when the task is loaded, before any step has run. A string that
refers to facts is substituted when its step starts, so the step sees what the
steps before it wrote; its syntax is still checked when the task is loaded, and
by ``cijoe -i``. A step that names a fact nobody wrote fails; it does not run
with an empty value.

Tests run by ``core.testrunner`` read and write facts like any script, through
the ``cijoe`` fixture. They start with the run's facts, and when they are done,
the step merges the facts they changed into the run's, as written by the
testrunner step. A fact the tests delete stays in the run's.

The facts of a run are one table, shared by all its steps. How they are
organised is up to the scripts that write them, such as ``guest.<name>`` for a
run with several guests.


Across runs
===========

Every write saves the whole set of facts to ``facts.toml`` in the output
directory. A later run starts from them with ``--facts``:

.. code-block:: bash

   cijoe provision.yaml --config machine.toml --output provisioned
   cijoe benchmark.yaml --config machine.toml --facts provisioned/facts.toml

The file given to ``--facts`` is only where the run starts: it is copied into
this run's ``facts.toml``, which every write updates, and is itself never
written. A chain of runs passes each run's ``facts.toml`` to the next.

When the earlier run's configuration differs from this run's, **cijoe** prints a
warning, as the facts may then describe something else, and goes on.


Facts and configuration
=======================

The two are kept apart, so that a run cannot rewrite its own intent:

* ``getconf()`` never returns a fact, and ``cijoe.facts.get()`` never returns
  configuration.

* A configuration file with a ``facts`` table is refused, and one that refers
  to ``{{ facts.* }}`` fails to load, as facts do not exist yet when it does.

* Only scripts write facts. A ``run:`` step reads them, but does not write them.
