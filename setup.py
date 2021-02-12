"""
    Definition of CIJOE distribution package
"""
import codecs
import glob
import os
from setuptools import setup


def read(*parts):
    """Read parts to use a e.g. long_description"""

    here = os.path.abspath(os.path.dirname(__file__))

    # intentionally *not* adding an encoding option to open, See:
    #   https://github.com/pypa/virtualenv/issues/201#issuecomment-3145690
    with codecs.open(os.path.join(here, *parts), 'r') as pfp:
        return pfp.read()


setup(
    name="cijoe",
    version="0.1.42.dev2",
    description="Tools for systems development and testing",
    long_description=read('README.rst'),
    author="Simon A. F. Lund",
    author_email="os@safl.dk",
    url="https://github.com/refenv/cijoe",
    license="Apache License 2.0",
    install_requires=[
        "pyyaml (>=3.10)", "jinja2 (>=2.0)", "kmdo"
    ],
    zip_safe=False,
    packages=["cij", "cij.unittests", "cij.extractors"],
    package_dir={"": "modules"},
    data_files=[
        ("bin", glob.glob("bin/*")),

        ("share/cijoe/hooks", glob.glob("hooks/*")),
        ("share/cijoe/modules", glob.glob("modules/*.sh")),
        ("share/cijoe/templates", glob.glob("templates/*html")),

        ("share/cijoe/envs", glob.glob("envs/*")),

        ("share/cijoe/testfiles", glob.glob("testfiles/*")),
        ("share/cijoe/testcases", glob.glob("testcases/*")),
        ("share/cijoe/testsuites", glob.glob("testsuites/*")),
        ("share/cijoe/testplans", glob.glob("testplans/*"))
    ],
    options={'bdist_wheel': {'universal': True}},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python",
        "Topic :: Text Processing",
        "Topic :: Utilities",
        "Topic :: Software Development",
        "Topic :: Software Development :: Testing"
    ],
)
