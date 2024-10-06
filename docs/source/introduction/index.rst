.. _sec-introduction:

==============
 Introduction
==============

If you're familiar with tools like :chef:`Chef <>`, :puppet:`Puppet <>`,
and :ansible:`Ansible <>`, note that **cijoe** is not designed to replace or
compete with them. Instead, **cijoe** aligns more closely with Python
projects like :paramiko:`Paramiko <>`, :fabric:`Fabric <>`,
:invoke:`Invoke <>`, and :invocations:`Invocations <>`.

While **cijoe** shares some similarities with these tools, it differs by
prioritizing minimalism. This approach applies to system requirements, the
codebase, and the concepts users need to learn.

In terms of functionality, **cijoe** may feel familiar to users
of :ansible:`Ansible <>` or :invocations:`Invocations <>`, or a combination of
both, but its focus is distinct.

Unlike configuration management tools, **cijoe** is a minimal, open-ended
scripting tool that emphasizes maintainability, reusability, and built-in
reporting for sharing results, including command output and artifacts.

**cijoe** is designed to execute commands, scripts, or workflows
within continuous integration (CI) environments such as
:github:`GitHub <>`, :gitlab:`GitLab <>`, :travis:`Travis CI <>`,
and  :jenkins:`Jenkins <>`.
It also allows for seamless execution of the same scripts on local systems,
enabling developers to switch between CI providers while maintaining the ability
to run automated tasks locally.

.. figure:: ../_static/cijoe-networked.drawio.png
   :alt: Development Environment
   :align: center

   The "core" agentless functionality of **cijoe**; run commands and tranfer
   files


Terminology
-----------

For reference, then a bit of terminalogy used by **cijoe** is defined here.
The intent here is to reduce confusion for readers with prior experience and
knowledge for these terms in other contexts.

command
	This is a string describing either the invokation of a command-line tool, this  	
	can be with or without arguments e.g. ``hostname`` and	``lspci -v``. Or a 	 	
	shell-expression ``[ -f /tmp/ jazz ] && echo "Hello!"``.

initiator
	This is the system on which **cijoe** is installed, where the ``cijoe`` cli-tool
	is executed.

target
	This is where **commands** and executed, and files transferred to and from.

Key Features
------------

- **Simplicity**:

  - **cijoe** is designed to be easy to use and does not require extensive
    learning. It avoids the need to master YAML-based scripting languages, as is
    common with other systems. Instead, it relies on Python and offers a helper
    class for the core scripting interface.
  
- **Agentless**:

  - When used with remote systems, **cijoe** operates in an agentless fashion.
    It relies on SSH for executing commands on target systems. Unlike Ansible,
    **cijoe** does not require Python to be installed on the target node.
  - For data transfer, **SSH** and **SCP** are similarly used.

In summary, **cijoe** aims to be a simple yet powerful tool that integrates
well within your CI workflows, whether on a remote CI provider or local systems,
without adding complexity.

Once you have ensured that the system prerequisites (:ref:`sec-prerequisites`)
are met, proceed to the :ref:`sec-usage` section to run an example
script and workflow. For documentation on how to create your own scripts,
see :ref:`sec-resources`. Finally, refer to :ref:`sec-packages` for descriptions
of existing script collections and related packages.
