.. _sec-post-processing:

=================
 Post-Processing
=================

The data produced when :ref:`sec-running`, that is, all output produced by
:ref:`sec-packages-hooks`, :ref:`sec-packages-testcases`, and the system
commands these are executing, is collected and organized in a directory
referred to as the **testrun**. In addition to collecting command output, then
**cijoe** can also be instructed to collect **artifacts** produced by tools,
such as log-files, process profiles, results from system-probes etc.

**cijoe** collects **all** of this, nothing is filtered out of hidden. Thus the
data generated can be overwhelming when browsing through a **testrun**.

Thus, to produce a humanly readably representation of a **testrun**, then a
:ref:`sec-post-processing-reporter` is provided which augments the **testrun**
with HTML formatted report.

Similarly, the :ref:`sec-post-processing-extractor`, provides an interfaces to
extract the key metrics of interesting.

The reporter, and the other post-processing tools are, when integrated in a
**CI/CD** pipeline, executed after the ``cij_runner`` is done. However, one can
run the tools while ``cij_runner`` is executing to get a preview of how the
execution is progressing.

.. note:: This section lacks documentation of usage and how to extend the
   post-processing capabilities. Your PR improving this is most welcome.

.. _sec-post-processing-reporter:

Reporter
========

The ``cij_reporter`` command-line tool:

.. literalinclude:: cij_reporter.out
   :language: bash

The reporter uses the `Jinja`_ templating-engine. The jinja-template given to
``cij_reporter`` by default produces a HTML-formatted report. However, you can
provide your own jinja-template to produce a report in the textual format of
your choosing, you could even just produce text-based summary to dump directory
on the command-line.

.. _sec-post-processing-extractor:

Extractor
=========

.. literalinclude:: cij_extractor.out
   :language: bash


.. _sec-post-processing-analyser:

Analyser
========

.. literalinclude:: cij_analyser.out
   :language: bash

.. _sec-post-processing-plotter:

Plotter
=======

.. literalinclude:: cij_plotter.out
   :language: bash

.. _Jinja: https://jinja.palletsprojects.com/en/3.0.x/
