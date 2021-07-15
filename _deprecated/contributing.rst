.. _sec-contributing:

==============
 Contributing
==============

Installation
------------

When modifying **cijoe** or a **cijoe** package, utilize the following
workflow:

* ``pip install --user -r requirements.dev.txt``

Once the prerequisites are installed, then development 

1. Run: ``make install``
2. Run: ``make selftest-view``
3. Use **cijoe** or the feature you adding / changing / fixing
4. Modify **cijoe** or the **cijoe** package
5. GOTO 1

This will install using ``pip install --user`` and utilize ``cijoe`` itself to
do some basic verification of the testplans, testsuites, the Python code and
Bash scripts.
