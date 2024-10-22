.. _sec-resources-templates:

Templates
=========

In **cijoe** templates refer to :jinja:`Jinja <>` templates with the 
``.jinja2`` file extension. Any such file that is reachable by the **automatic
collection** of resources, will be available as a template.

Consider the simple HTML template below with filename ``template.html.jinja2``.

.. literalinclude:: ./template.html.jinja2
   :language: html

See the official Jinja :jinja:`Template Designer Documentation <templates/>` for 
more information on how to construct Jinja templates.

In a **cijoe** :ref:`script <sec-resources-scripts>`, you can access the HTML 
template via the **cijoe** resources. The example script below will populate
the template with the initiator's hostname, generating a new file with the
HTML.

.. literalinclude:: ./template.py
   :language: python