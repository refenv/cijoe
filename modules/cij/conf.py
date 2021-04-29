"""
   CIJOE Configuration
"""
from subprocess import Popen, PIPE
from typing import Optional
import dataclasses
import os
import cij


CFG_FIELDS = [
    "root", "envs", "modules", "hooks", "testfiles",
    "templates", "testplans", "testsuites", "testcases"
]


@dataclasses.dataclass
class Config:
    """Contains absolute paths to CIJOE entities"""
    # pylint: disable=too-many-instance-attributes
    # This is a dataclass, many instance attributes are expected.

    root: str = ""          # Path to root of CIJOE installation
    envs: str = ""          # Path to environment-definitions
    hooks: str = ""         # Path to hooks
    modules: str = ""       # Path to Bash modules
    templates: str = ""     # Path to reporter-templates
    testcases: str = ""     # Path to testcase scripts (.sh)
    testfiles: str = ""     # Path to testfiles e.g. fio scripts etc.
    testplans: str = ""     # Path to testplans definitions (.plan)
    testsuites: str = ""    # Path to testsuite definitions (.suite)


# pylint: disable=unsubscriptable-object
def from_system() -> Optional[Config]:
    """
    Config-factory; producing a Config based on environment variables and when
    environment variables aren't set, fall back to the ``cij_root`` helper.
    """

    conf = Config()

    # Setup configuration using environment variable definitions
    paths_from_evars = cij.paths_from_env(
        "CIJ",
        [f.upper() for f in CFG_FIELDS]
    )

    missing = False
    for key, value in paths_from_evars.items():
        if value is None:
            missing = True
            break
        setattr(conf, key.lower(), value)

    if not missing:
        return conf

    # Setup configuration using 'cij_root'
    with Popen(["cij_root"], stdout=PIPE) as proc:
        out, _ = proc.communicate()
        if proc.returncode:
            return None

        cij_root = out.decode("utf-8").strip()
        if not os.path.exists(cij_root):
            return None

        for field in CFG_FIELDS:
            setattr(conf, field, os.path.join(cij_root, field))

    return conf
