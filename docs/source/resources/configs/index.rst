.. _sec-resources-configs:

Configs
=======

**cijoe** configuration files are plain-text files written in :toml:`TOML <>`
and with suffix ``.toml``. **cijoe** itself has few configurable items, thus,
the content of a **cijoe** configuration file is often filled with with items
used by :ref:`sec-resources-scripts`.

However, there are a couple of **cijoe** specific keys:

* SSH Configuration
* Shell Configuration

.. _sec-resources-configs-api:

API
---

Represented in the code as a :ref:`sec-resources`.

.. autoclass:: cijoe.core.resources.Config
   :members:
   :undoc-members:
   :inherited-members:
