.. _sec-resources-facts:

=======
 Facts
=======

A **fact** is something a step found out during a run: the kernel a target
booted, the names it gave its devices, the version a build produced. The
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

The ``core.facts`` example gathers facts about the **target**, and the steps
after it use what was found. Emit it and run it with:

.. code-block:: bash

   cijoe --example core.facts
   cd cijoe-example-core.facts
   cijoe --monitor

The configuration says what the task wants, at least one CPU:

.. literalinclude:: ../../../src/cijoe/core/configs/example_config_facts.toml
   :language: toml

The task's first step runs ``core.facts_gather``, which records the target's
OS, kernel, CPUs, memory, PCI functions and NVMe controllers. The second shows
some of them, and the third checks the observation against what the
configuration wants:

.. literalinclude:: ../../../src/cijoe/core/tasks/example_task_facts.yaml
   :language: yaml

After the run, ``cijoe-output/facts.toml`` holds what was observed. Here it was
run on a WSL2 workstation, whose only target is the initiator; its ``pci`` list
is cut from this excerpt, and its ``nvme`` table is empty, as it has no NVMe
controllers:

.. code-block:: toml

   [targets.initiator.os]
   family = "linux"
   id = "ubuntu"
   version_id = "26.04"
   name = "Ubuntu"
   pretty_name = "Ubuntu 26.04 LTS"

   [targets.initiator.kernel]
   name = "Linux"
   release = "6.6.87.2-microsoft-standard-WSL2"
   machine = "x86_64"

   [targets.initiator.system]
   cpus = 16
   memory_kib = 31733944

The report's **Facts** tab lists the same facts, each with the step that last
wrote it, here ``gather`` for all. A step that wrote facts has a **facts**
button, which shows them with their values; ``task.state`` lists, for each
step, the keys it wrote.


Facts about targets
===================

Facts about a machine are kept under ``targets.<name>``, where the name is the
one the configuration gives it as ``[cijoe.transport.<name>]``, or
``initiator``. A QEMU guest and a machine on the bench are alike: what is known
about either is under its name, whoever wrote it. The **default target** is the
one ``cijoe.run()`` reaches when given no ``transport_name``: the first
transport in the configuration, or the initiator when there is none, and
``cijoe.default_target`` names it.

A task reads the default target's facts as ``{{ target.* }}``, short for
``{{ facts.targets.<default target>.* }}``, and another target's in full:

.. code-block:: yaml

   - name: show
     run: |
       echo "{{ target.os.pretty_name }} on {{ target.kernel.machine }}"
       echo "{{ facts.targets.machineB.os.id }}"

A script reads and writes them with ``cijoe.facts.target()``, which takes a
target's name and defaults to the default target, and has the calls of
``cijoe.facts`` on keys within the target:

.. code-block:: python

   cijoe.facts.target().set("gpu", {"vendor": "0x1002"})   # targets.<default>.gpu
   release = cijoe.facts.target("machineB").get("kernel.release")

``core.facts_gather`` writes these sections for its ``--target``, by default the
default target, or those named with ``--sections``. It finds the target's OS
family by asking it, ``uname -s``, or PowerShell where there is no ``uname``,
and leaves out a section it has no way of gathering on that family:

.. list-table::
   :header-rows: 1
   :widths: 15 45 40

   * - Section
     - Keys
     - Gathered on
   * - ``os``
     - ``family``, ``id``, ``version_id``, ``name``, ``pretty_name``
     - Linux, FreeBSD, macOS, Windows
   * - ``kernel``
     - ``name``, ``release``, ``machine``
     - Linux, FreeBSD, macOS, Windows
   * - ``system``
     - ``cpus``, ``memory_kib``
     - Linux, FreeBSD, macOS, Windows
   * - ``pci``
     - a list, by BDF, of ``bdf``, ``vendor``, ``device``, ``class``,
       ``driver``
     - Linux, FreeBSD
   * - ``nvme``
     - ``<controller>``: ``bdf``, ``serial``, ``namespaces``, each with
       ``nsid``, ``bdev``, ``cdev``
     - Linux, FreeBSD, Windows, by ``PhysicalDrive<n>``

A package gathers sections of its own the same way, with
``cijoe.facts.target().set()``, under the same target.


Writing and reading facts
=========================

A script writes facts on ``cijoe.facts``, with dotted keys as for
:ref:`getconf() <sec-resources-scripts-getconf>`:

.. code-block:: python

   cijoe.facts.set("build.version", "1.2.3")                # replace
   cijoe.facts.update("build", {"commit": "c0ffee"})        # merge into a table
   cijoe.facts.delete("build.commit")                       # remove

   version = cijoe.facts.get("build.version", "unknown")

A key is names separated by dots, so a name cannot hold a dot itself; a fact
whose natural name has one, such as a PCI function's BDF, goes in a list of
tables instead. A value is anything TOML can hold: strings, numbers, booleans,
lists and tables; a write of anything else, such as ``None``, raises ``TypeError`` and
changes nothing. ``set()`` replaces what was at the key, which is how a script
brings a fact up to date when it observes again, for example after a device is
unplugged. ``get()`` returns a copy, so changing what it returned changes no
fact.

A task reads facts in a step's ``with``, as ``{{ facts.build.version }}``, as
``{{ target.os.id }}`` for the default target, or in a block such as
``{% if target.gpu %}``. Other variables in a task are
substituted when the task is loaded, before any step has run. A string that
refers to facts is substituted when its step starts, so the step sees what the
steps before it wrote; its syntax is still checked when the task is loaded, and
by ``cijoe -i``. A step that names a fact nobody wrote fails; it does not run
with an empty value.

Tests run by ``core.testrunner`` read and write facts like any script, through
the ``cijoe`` fixture. They start with the run's facts, and when they are done,
the step merges the facts they changed into the run's, as written by the
testrunner step. A fact the tests delete stays in the run's.

The facts of a run are one table, shared by all its steps. Facts about a machine
belong under its target, as above; others are organised by the scripts that
write them, under a key of their own, such as ``build``.


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
