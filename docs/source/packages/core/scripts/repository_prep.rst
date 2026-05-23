
.. _sec-packages-core-repository_prep:

core.repository_prep
~~~~~~~~~~~~~~~~~~~~

.. automodule:: cijoe.core.scripts.repository_prep
   :members:

CLI arguments
-------------

* ``--depth DEPTH``

  Argument for git: Create a shallow clone with a history truncated to the specified number or revisions. The minimum possible value is 1, otherwise ignored. (default: None)

* ``--single_branch {true,false}``

  Argument for git: Clone only the history leading to the tip of the specified revision. (default: False)
