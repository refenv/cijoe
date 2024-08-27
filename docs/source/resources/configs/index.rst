.. _sec-resources-configs:

Configs
=======

**cijoe** configuration files are formated using `YAML`_ and named with suffix
``.config``. In the core functionality of provided by cijoe, only the keys
``cijoe.transport`` and ``cijoe.run`` have special meaning.

Keys are otherwise granted meaning by their use of
:ref:`sec-resources-scripts`, tests, and regular Python modules.

.. _sec-resources-configs-example:

Example
~~~~~~~

...

.. _sec-resources-configs-objects:

Objects
-------

Represented in the code as a :ref:`sec-resources`.

.. autoclass:: cijoe.core.resources.Config
   :members:
   :undoc-members:
   :inherited-members:

.. _YAML: https://yaml.org/
