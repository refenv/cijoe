"""
    Definition for distribution of CIJOE
"""
import glob
from setuptools import setup

setup(
    name="cijoe",
    version="0.0.16",
    description="Tools for for development and testing",
    author="Simon A. F. Lund",
    author_email="slund@cnexlabs.com",
    url="http://github.com/safl/cijoe",
    license="BSD-2",
    install_requires=[
        "ansi2html (>=1.5.2)", "jinja2 (>=2.0)", "pyyaml (>=3.10)",
        "xlsxwriter", "matplotlib"
    ],
    zip_safe=False,
    packages=["cij"],
    package_dir={"": "modules"},
    data_files=[
        ("bin", glob.glob("bin/*")),
        ("share/cijoe/hooks", glob.glob("hooks/*")),
        ("share/cijoe/modules", glob.glob("modules/*.sh")),
        ("share/cijoe/templates", glob.glob("templates/*")),

        ("share/cijoe/envs", glob.glob("envs/*")),

        ("share/cijoe/testfiles", glob.glob("testfiles/*")),
        ("share/cijoe/testcases", glob.glob("testcases/*")),
        ("share/cijoe/testsuites", glob.glob("testsuites/*")),
        ("share/cijoe/testplans", glob.glob("testplans/*"))
    ],
    options={'bdist_wheel':{'universal':True}}
)
