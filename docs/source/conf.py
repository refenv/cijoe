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
html_sidebars = {
    "configs**": [],
    "introduction**": [],
    "prereq**": [],
    "scripts**": [],
    "testrunner**": [],
    "usage**": [],
    "workflows**": [],
}
html_theme_options = {
    "header_links_before_dropdown": 8,
    "collapse_navigation": False,
    "navigation_depth": 4,
    "navigation_with_keys": False,
    "navbar_align": "left",
    "show_version_warning_banner": True,
}
html_context = {
    "default_mode": "dark",
}


extlinks = {
    "ansible": ("https://www.ansible.com/%s", None),
    "argparse": ("https://docs.python.org/3/library/argparse.html%s", None),
    "chef": ("https://www.chef.io/%s", None),
    "expect": ("https://en.wikipedia.org/wiki/Expect%s", None),
    "fabric": ("https://www.fabfile.org/%s", None),
    "github": ("https://github.com/%s", None),
    "gitlab": ("https://gitlab.com/%s", None),
    "invocations": ("https://invocations.readthedocs.io/en/latest/%s", None),
    "invoke": ("https://www.pyinvoke.org/%s", None),
    "jenkins": ("https://www.jenkins.io/%s", None),
    "jinja": ("https://jinja.palletsprojects.com/en/3.1.x/%s", None),
    "just": ("https://github.com/casey/just%s", None),
    "make": ("https://en.wikipedia.org/wiki/Make_(software)%s", None),
    "paramiko": ("https://www.paramiko.org/%s", None),
    "paramiko_client": ("https://docs.paramiko.org/en/latest/api/client.html%s", None),
    "pep668": ("https://peps.python.org/pep-0668/%s", None),
    "pipx": ("https://pypa.github.io/pipx/%s", None),
    "posix_sh": (
        "https://pubs.opengroup.org/onlinepubs/009695399/utilities/xcu_chap02.html%s",
        None,
    ),
    "puppet": ("https://puppet.com/%s", None),
    "pytest": ("https://docs.pytest.org/%s", None),
    "python_argparse": ("https://docs.python.org/3/library/argparse.html%s", None),
    "python": ("https://www.python.org/%s", None),
    "python_logging": ("https://docs.python.org/3/library/logging.html%s", None),
    "toml": ("https://toml.io/en/%s", None),
    "travis": ("https://travis-ci.org/%s", None),
    "yaml": ("https://yaml.org/%s", None),
    "windows_ssh": (
        "https://learn.microsoft.com/en-us/windows-server/administration/openssh/"
        "openssh-overview%s",
        None,
    ),
}
