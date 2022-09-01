.. _sec-introduction:

==============
 Introduction
==============

A network-connected **development environment**, as illustrated in
:numref:`devenv`, typically consists of a box on which **changes** are created
using editors/IDEs/Toolchains for the task at hand, we refer to such a machine
as the **dev box**.

Said **changes** are then **tested** on one or more boxes/VMs/systems, we refer
to the latter as **test-targets**.

With **cijoe** you create an :ref:`sec-resources-configs` for each of available
**test-target**.

.. _devenv:
.. figure:: ../_static/environment.png
   :alt: Development Environment
   :align: center

   Development environment containing a **dev box**, and multiple **test-targets**.

The sections :ref:`sec-prerequisites` and :ref:`sec-installation`  describe
what is needed on your **dev box** and your **test-target(s)**.

Once you have ensured that :ref:`sec-prerequisites` are met, have gone through
the :ref:`sec-installation`, then go ahead with the :ref:`sec-usage`.

.. _GitHUB: https://github.com/refenv/cijoe
