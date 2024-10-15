# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
from cijoe.core import __version__

project = "cijoe"
copyright = "2024, Simon A. F. Lund"
author = "Simon A. F. Lund"
release = __version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "pydata_sphinx_theme",
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx.ext.coverage",
    "sphinx.ext.extlinks",
    "sphinx.ext.imgmath",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx_tabs.tabs",
]

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

numfig = True

html_theme = "pydata_sphinx_theme"
html_static_path = ["_static"]
html_logo = "_static/logo.png"
html_sidebars = {"introduction**": [], "usage**": [], "prereq**": []}

extlinks = {
    "ansible": ("https://www.ansible.com/%s", None),
    "chef": ("https://www.chef.io/%s", None),
    "expect": ("https://en.wikipedia.org/wiki/Expect%s", None),
    "fabric": ("https://www.fabfile.org/%s", None),
    "github": ("https://github.com/%s", None),
    "gitlab": ("https://gitlab.com/%s", None),
    "invocations": ("https://invocations.readthedocs.io/en/latest/%s", None),
    "invoke": ("https://www.pyinvoke.org/%s", None),
    "jenkins": ("https://www.jenkins.io/%s", None),
    "paramiko": ("https://www.paramiko.org/%s", None),
    "pep668": ("https://peps.python.org/pep-0668/%s", None),
    "pipx": ("https://pypa.github.io/pipx/%s", None),
    "puppet": ("https://puppet.com/%s", None),
    "python": ("https://www.python.org/%s", None),
    "travis": ("https://travis-ci.org/%s", None),
    "windows_ssh": (
        "https://learn.microsoft.com/en-us/windows-server/administration/openssh/"
        "openssh-overview%s",
        None,
    ),
}
