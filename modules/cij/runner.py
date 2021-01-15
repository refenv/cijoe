"""
    library functions for the CIJOE test runner, `cij_runner`.
"""
from __future__ import print_function, annotations
from subprocess import Popen, STDOUT
from xml.dom import minidom
import dataclasses
import shutil
import copy
import time
import os
import yaml
import cij

HOOK_PATTERNS = {
    "enter": [
        "%s.sh",
        "%s_enter.sh",
        "%s_enter.py",
    ],
    "exit": [
        "%s_exit.sh",
        "%s_exit.py"
    ]
}

@dataclasses.dataclass
class Runnable:
    name: str = "UNNAMED"
    evars: dict = dataclasses.field(default_factory=dict)
    log_fpath: str = None
    fpath: str = None
    res_root: str = None
    rcode: int = None
    wallc: float = None


@dataclasses.dataclass
class Hook(Runnable):
    fname: dict = None
    fpath_orig: dict = None

    @staticmethod
    def hooks_from_dict(hooks_dict) -> dict:
        """
        Deserialize a hook dict containing lists of hook dicts dicts into a hook
        dict containing lists of Hooks
        """
        hook_fields = set(Hook.__dataclass_fields__)

        hooks = {}
        for hook_stage, hooks_entries in hooks_dict.items():
            hooks[hook_stage] = []

            for hook_entry in hooks_entries:
                hook = Hook()
                for key in hook_fields & set(hook_entry):
                    setattr(hook, key, hook_entry[key])
                hooks[hook_stage].append(hook)

        return hooks


@dataclasses.dataclass
class TestCase(Runnable):
    ident: str = "UNDEFINED"
    fname: str = None
    aux_root: str = None
    aux_list: list = dataclasses.field(default_factory=list)

    hooks: dict = dataclasses.field(default_factory=dict)
    hnames: list = dataclasses.field(default_factory=list)

    status: str = "UNKN"
    src_content: str = ""
    descr: str = ""
    descr_long: str = ""
    src_content: str = ""
    log_content: str = ""


    @staticmethod
    def tcases_from_dicts(tcase_dicts) -> list[TestCase]:
        """
        Deserialize a list of tcase dictionaries into a list of TestCases
        """
        complex_keys = {'hooks': Hook.hooks_from_dict} 
        tcase_fields = set(TestCase.__dataclass_fields__)

        tcases = []
        for tcase_dict in tcase_dicts:
            tcase = TestCase()
            for key in tcase_fields & set(tcase_dict):
                deserialize = complex_keys.get(key, lambda x: x)
                setattr(tcase, key, deserialize(tcase_dict[key]))

            tcases.append(tcase)

        return tcases


@dataclasses.dataclass
class TestSuite:
    ident: str = "UNDEFINED"
    name: str = "UNNAMED"
    alias: str = ""
    hooks: dict = dataclasses.field(default_factory=lambda: {
        "enter": [],
        "exit": []
    })
    evars: dict = dataclasses.field(default_factory=dict)

    fpath: str = None
    fname: str = None
    res_root: str = None
    aux_root: str = None
    aux_list: list = dataclasses.field(default_factory=list)

    status: str = "UNKN"
    wallc: float = None

    testcases: list = dataclasses.field(default_factory=list)
    hooks_pr_tcase: list = dataclasses.field(default_factory=list)

    log_content: str = ""
    hnames: list = dataclasses.field(default_factory=list)

    @staticmethod
    def tsuites_from_dicts(tsuites_dicts) -> list[TestSuite]:
        """
        Deserialize a list of tsuite dicts into a list of TestSuites
        """
        complex_keys = {
            'testcases': TestCase.tcases_from_dicts,
            'hooks': Hook.hooks_from_dict,
        }
        tsuite_fields = set(TestSuite.__dataclass_fields__)

        tsuites = []
        for tsuite_dict in tsuites_dicts:
            tsuite = TestSuite()
            for key in tsuite_fields & set(tsuite_dict):
                deserialize = complex_keys.get(key, lambda x: x)
                setattr(tsuite, key, deserialize(tsuite_dict[key]))

            tsuites.append(tsuite)

        return tsuites


@dataclasses.dataclass
class TestRun:
    ver: str = None
    conf: dict = None
    evars: dict = dataclasses.field(default_factory=dict)
    progress: dict = dataclasses.field(default_factory=lambda: {
        "PASS": 0,
        "FAIL": 0,
        "UNKN": 0
    })
    stamp: dict = dataclasses.field(default_factory=lambda: {
        "begin": None,
        "end": None
    })
    hooks: dict = dataclasses.field(default_factory=lambda: {
        "enter": [],
        "exit": []
    })
    res_root: str = None
    aux_root: str = None
    aux_list: list = dataclasses.field(default_factory=list)

    testsuites: list = dataclasses.field(default_factory=list)

    status: str = "UNKN"
    wallc: float = None
    log_content: str = ""
    hnames: list = dataclasses.field(default_factory=list)


    @staticmethod
    def from_dict(trun_dict) -> TestRun:
        """
        Deserialize a trun dict into TestRun
        """
        complex_keys = {
            'testsuites': TestSuite.tsuites_from_dicts,
            'hooks': Hook.hooks_from_dict,
        }

        trun = TestRun()

        fields = set(TestRun.__dataclass_fields__) & set(trun_dict)
        for key in fields:
            deserialize = complex_keys.get(key, lambda x: x)
            setattr(trun, key, deserialize(trun_dict[key]))

        return trun


def yml_fpath(output_path):
    """Returns the path to the trun YAML-file"""

    return os.sep.join([output_path, "trun.yml"])

def junit_fpath(output_path):
    """Returns the path to the jUNIT XML-file"""

    return os.sep.join([output_path, "trun.xml"])

def script_run(trun, script: Runnable):
    """Execute a script or testcase"""

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:script:run { script: %s }" % script)
        cij.emph("rnr:script:run:evars: %s" % script.evars)

    launchers = {
        ".py": "python",
        ".sh": "source"
    }

    ext = os.path.splitext(script.fpath)[-1]
    if not ext in launchers.keys():
        cij.err("rnr:script:run { invalid script.fpath: %r }" % script.fpath)
        return 1

    launch = launchers[ext]

    with open(script.log_fpath, "a") as log_fd:
        log_fd.write("# script_fpath: %r\n" % script.fpath)
        log_fd.flush()

        bgn = time.time()
        cmd = [
            'bash', '-c',
            'CIJ_ROOT=$(cij_root) && '
            'source $CIJ_ROOT/modules/cijoe.sh && '
            'source %s && '
            'CIJ_TEST_RES_ROOT="%s" %s %s ' % (
                trun.conf["ENV_FPATH"],
                script.res_root,
                launch,
                script.fpath
            )
        ]
        if trun.conf["VERBOSE"] > 1:
            cij.emph("rnr:script:run { cmd: %r }" % " ".join(cmd))

        evars = os.environ.copy()
        evars.update({k: str(script.evars[k]) for k in script.evars})

        process = Popen(
            cmd,
            stdout=log_fd,
            stderr=STDOUT,
            cwd=script.res_root,
            env=evars
        )
        process.wait()

        script.rcode = process.returncode
        script.wallc = time.time() - bgn

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:script:run { wallc: %02f }" % script.wallc)
        cij.emph(
            "rnr:script:run { rcode: %r } " % script.rcode,
            script.rcode
        )

    return script.rcode

def hook_setup(parent, hook_fpath) -> Hook:
    """Setup hook"""

    hook = Hook()
    hook.name = os.path.splitext(os.path.basename(hook_fpath))[0]
    hook.name = hook.name.replace("_enter", "").replace("_exit", "")
    hook.res_root = parent.res_root
    hook.fpath_orig = hook_fpath
    hook.fname = "hook_%s" % os.path.basename(hook.fpath_orig)
    hook.fpath = os.sep.join([hook.res_root, hook.fname])
    hook.log_fpath = os.sep.join([
        hook.res_root,
        "%s.log" % hook.fname
    ])

    hook.evars.update(copy.deepcopy(parent.evars))

    shutil.copyfile(hook.fpath_orig, hook.fpath)

    return hook

def hooks_setup(trun, parent, hnames=None) -> dict:
    """
    Setup test-hooks
    @returns dict of hook filepaths {"enter": [], "exit": []}
    """

    hooks = {
        "enter": [],
        "exit": []
    }

    if hnames is None:       # Nothing to do, just return the struct
        return hooks

    for hname in hnames:      # Fill out paths
        for med in HOOK_PATTERNS:
            for ptn in HOOK_PATTERNS[med]:
                fpath = os.sep.join([trun.conf["HOOKS"], ptn % hname])
                if not os.path.exists(fpath):
                    continue

                hook = hook_setup(parent, fpath)
                if not hook:
                    continue

                hooks[med].append(hook)

        if not hooks["enter"] + hooks["exit"]:
            cij.err("rnr:hooks_setup:FAIL { hname: %r has no files }" % hname)
            return None

    return hooks


def trun_to_file(trun, fpath=None):
    """Dump the given trun to file"""

    if fpath is None:
        fpath = yml_fpath(trun.conf["OUTPUT"])

    trun_dict = dataclasses.asdict(trun)
    with open(fpath, 'w') as yml_file:
        data = yaml.dump(trun_dict, explicit_start=True, default_flow_style=False)
        yml_file.write(data)

def trun_to_junitfile(trun, fpath=None):
    """Generate jUNIT XML from testrun YML"""

    try:
        if fpath is None:
            fpath = junit_fpath(trun.conf["OUTPUT"])

        doc = minidom.Document()

        doc_testsuites = doc.createElement('testsuites')

        duration = 0
        stamp = trun.stamp
        if stamp:
            stamp_begin = stamp.get("begin", None)
            if not stamp_begin:
                stamp_begin = time.time()

            stamp_end = stamp.get("end", None)
            if not stamp_end:
                stamp_end = time.time()

            if stamp_end > stamp_begin:
                duration = stamp_end - stamp_begin

        doc_testsuites.setAttribute("duration", str(duration))

        doc.appendChild(doc_testsuites)

        for ts_id, tsuite in enumerate(trun.testsuites):

            doc_tsuite = doc.createElement("testsuite")
            doc_tsuite.setAttribute("name", tsuite.name)
            doc_tsuite.setAttribute("package", tsuite.ident)
            doc_tsuite.setAttribute(
                "tests",
                str(len(tsuite.testcases))
            )

            nfailures = 0
            wallc_total = 0.0

            for tcase in tsuite.testcases:
                wallc = tcase.wallc
                if not wallc:
                    wallc = 0.0

                wallc_total += wallc

                doc_tcase = doc.createElement("testcase")
                doc_tcase.setAttribute(
                    "name", str(tcase.name)
                )
                doc_tcase.setAttribute(
                    "classname", str(tcase.ident)
                )
                doc_tcase.setAttribute("time", "%0.3f" % wallc)

                rcode = tcase.rcode
                if rcode != 0:
                    nfailures += 1

                    doc_failure = doc.createElement("failure")
                    doc_failure.setAttribute(
                        "message",
                        "not executed" if rcode is None else "test failed"
                    )

                    doc_tcase.appendChild(doc_failure)

                doc_tsuite.appendChild(doc_tcase)

            doc_tsuite.setAttribute("failures", str(nfailures))
            doc_tsuite.setAttribute("time", "%0.3f" % wallc_total)

            doc_testsuites.appendChild(doc_tsuite)

        with open(fpath, "w") as f:
            f.write(doc.toprettyxml(indent="  "))

    except Exception as ex:
        cij.err("Failed persisting testrun as jUNIT XML, ex(%r)" % ex)
        return 1

    return 0


def trun_from_file(fpath):
    """Returns trun from the given fpath"""

    with open(fpath, 'r') as yml_file:
        trun_dict = yaml.safe_load(yml_file)
        return TestRun.from_dict(trun_dict)
    

def trun_emph(trun):
    """Print essential info on"""

    if trun.conf["VERBOSE"] > 1:               # Print environment variables
        cij.emph("rnr:CONF {")
        for cvar in sorted(trun.conf.keys()):
            cij.emph("  % 16s: %r" % (cvar, trun.conf[cvar]))
        cij.emph("}")

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:INFO {")
        cij.emph("  OUTPUT: %r" % trun.conf["OUTPUT"])
        cij.emph("  yml_fpath: %r" % yml_fpath(trun.conf["OUTPUT"]))
        cij.emph("}")


def tcase_setup(trun, parent, tcase_fname) -> TestCase:
    """
    Create and initialize a testcase
    """
    #pylint: disable=locally-disabled, unused-argument

    case = TestCase()

    case.fname = tcase_fname
    case.fpath_orig = os.sep.join([trun.conf["TESTCASES"], case.fname])

    if not os.path.exists(case.fpath_orig):
        cij.err('rnr:tcase_setup: !case.fpath_orig: %r' % case.fpath_orig)
        return None

    case.name = os.path.splitext(case.fname)[0]
    case.ident = "/".join([parent.ident, case.fname])

    case.res_root = os.sep.join([parent.res_root, case.fname])
    case.aux_root = os.sep.join([case.res_root, "_aux"])
    case.log_fpath = os.sep.join([case.res_root, "run.log"])

    case.fpath = os.sep.join([case.res_root, case.fname])

    case.evars.update(copy.deepcopy(parent.evars))

    # Initalize
    os.makedirs(case.res_root)                       # Create DIRS
    os.makedirs(case.aux_root)
    shutil.copyfile(case.fpath_orig, case.fpath)  # Copy testcase

    # Initialize hooks
    case.hooks = hooks_setup(trun, case, parent.hooks_pr_tcase)

    return case


def tsuite_exit(trun, tsuite):
    """Triggers when exiting the given testsuite"""

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:tsuite:exit")

    rcode = 0
    for hook in reversed(tsuite.hooks["exit"]):      # EXIT-hooks
        rcode = script_run(trun, hook)
        if rcode:
            break

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:tsuite:exit { rcode: %r } " % rcode, rcode)

    return rcode


def tsuite_enter(trun, tsuite):
    """Triggers when entering the given testsuite"""

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:tsuite:enter { name: %r }" % tsuite.name)

    rcode = 0
    for hook in tsuite.hooks["enter"]:     # ENTER-hooks
        rcode = script_run(trun, hook)
        if rcode:
            break

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:tsuite:enter { rcode: %r } " % rcode, rcode)

    return rcode

def tsuite_setup(trun, declr, enum) -> TestSuite:
    """
    Creates and initialized a TESTSUITE struct and site-effects such as creating
    output directories and forwarding initialization of testcases
    """

    suite = TestSuite()  # Setup the test-suite

    suite.name = declr.get("name")
    if suite.name is None:
        cij.err("rnr:tsuite_setup: no testsuite is given")
        return None

    suite.alias = declr.get("alias")
    suite.ident = "%s_%d" % (suite.name, enum)

    suite.res_root = os.sep.join([trun.conf["OUTPUT"], suite.ident])
    suite.aux_root = os.sep.join([suite.res_root, "_aux"])

    suite.evars.update(copy.deepcopy(trun.evars))
    suite.evars.update(copy.deepcopy(declr.get("evars", {})))

    # Initialize
    os.makedirs(suite.res_root)
    os.makedirs(suite.aux_root)

    # Setup testsuite-hooks
    suite.hooks = hooks_setup(trun, suite, declr.get("hooks"))

    # Forward from declaration
    suite.hooks_pr_tcase = declr.get("hooks_pr_tcase", [])

    suite.fname = "%s.suite" % suite.name
    suite.fpath = os.sep.join([trun.conf["TESTSUITES"], suite.fname])

    #
    # Load testcases from .suite file OR from declaration
    #
    tcase_fpaths = []                               # Load testcase fpaths
    if os.path.exists(suite.fpath):              # From suite-file
        suite_lines = (
            l.strip() for l in open(suite.fpath).read().splitlines()
        )
        tcase_fpaths.extend(
            (l for l in suite_lines if len(l) > 1 and l[0] != "#")
        )
    else:                                           # From declaration
        tcase_fpaths.extend(declr.get("testcases", []))

    # NOTE: fix duplicates; allow them
    # NOTE: Currently hot-fixed here
    if len(set(tcase_fpaths)) != len(tcase_fpaths):
        cij.err("rnr:suite: failed: duplicate tcase in suite not supported")
        return None

    for tcase_fname in tcase_fpaths:                # Setup testcases
        tcase = tcase_setup(trun, suite, tcase_fname)
        if not tcase:
            cij.err("rnr:suite: failed: tcase_setup")
            return None

        suite.testcases.append(tcase)

    return suite


def tcase_exit(trun, tsuite, tcase):
    """..."""
    #pylint: disable=locally-disabled, unused-argument

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:tcase:exit { fname: %r }" % tcase.fname)

    rcode = 0
    for hook in reversed(tcase.hooks["exit"]):    # tcase EXIT-hooks
        rcode = script_run(trun, hook)
        if rcode:
            break

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:tcase:exit { rcode: %r }" % rcode, rcode)

    return rcode


def tcase_enter(trun, tsuite, tcase):
    """
    setup res_root and aux_root, log info and run tcase-enter-hooks

    @returns 0 when all hooks succeed, some value othervise
    """
    #pylint: disable=locally-disabled, unused-argument

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:tcase:enter")
        cij.emph("rnr:tcase:enter { fname: %r }" % tcase.fname)
        cij.emph("rnr:tcase:enter { log_fpath: %r }" % tcase.log_fpath)

    rcode = 0
    for hook in tcase.hooks["enter"]:    # tcase ENTER-hooks
        rcode = script_run(trun, hook)
        if rcode:
            break

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:tcase:exit: { rcode: %r }" % rcode, rcode)

    return rcode

def trun_exit(trun):
    """Triggers when exiting the given testrun"""

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:trun:exit")

    rcode = 0
    for hook in reversed(trun.hooks["exit"]):    # EXIT-hooks
        rcode = script_run(trun, hook)
        if rcode:
            break

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:trun::exit { rcode: %r }" % rcode, rcode)

    return rcode


def trun_enter(trun):
    """Triggers when entering the given testrun"""

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:trun::enter")

    trun.stamp["begin"] = int(time.time())     # Record start timestamp

    rcode = 0
    for hook in trun.hooks["enter"]:     # ENTER-hooks
        rcode = script_run(trun, hook)
        if rcode:
            break

    if trun.conf["VERBOSE"]:
        cij.emph("rnr:trun::enter { rcode: %r }" % rcode, rcode)

    return rcode


def trun_setup(conf) -> TestRun:
    """
    Setup the testrunner data-structure, embedding the parsed environment
    variables and command-line arguments and continues with setup for testplans,
    testsuites, and testcases
    """

    declr = None
    try:
        with open(conf["TESTPLAN_FPATH"]) as declr_fd:
            declr = yaml.safe_load(declr_fd)
    except AttributeError as exc:
        cij.err("rnr: %r" % exc)

    if not declr:
        return None

    trun = TestRun()
    trun.ver = cij.VERSION

    trun.conf = copy.deepcopy(conf)
    trun.res_root = conf["OUTPUT"]
    trun.aux_root = os.sep.join([trun.res_root, "_aux"])
    trun.evars.update(copy.deepcopy(declr.get("evars", {})))

    os.makedirs(trun.aux_root)

    # Setup top-level hooks
    trun.hooks = hooks_setup(trun, trun, declr.get("hooks", []))

    for enum, declr in enumerate(declr["testsuites"]):  # Setup testsuites
        tsuite = tsuite_setup(trun, declr, enum)
        if tsuite is None:
            cij.err("main::FAILED: setting up tsuite: %r" % tsuite)
            return 1

        trun.testsuites.append(tsuite)
        trun.progress["UNKN"] += len(tsuite.testcases)

    return trun


def main(conf):
    """CIJ Test Runner main entry point"""

    fpath = yml_fpath(conf["OUTPUT"])
    if os.path.exists(fpath):   # YAML exists, we exit, it might be RUNNING!
        cij.err("main:FAILED { fpath: %r }, exists" % fpath)
        return 1

    trun = trun_setup(conf)         # Construct 'trun' from 'conf'
    if not trun:
        return 1

    trun_to_file(trun)              # Persist trun
    trun_to_junitfile(trun)         # Persist as jUNIT XML
    trun_emph(trun)                 # Print trun before run

    tr_err = 0
    tr_ent_err = trun_enter(trun)
    for tsuite in (ts for ts in trun.testsuites if not tr_ent_err):

        ts_err = 0
        ts_ent_err = tsuite_enter(trun, tsuite)
        for tcase in (tc for tc in tsuite.testcases if not ts_ent_err):

            tc_err = 0

            tcase_match = conf.get("TESTCASE_MATCH", None)
            if not (tcase_match and tcase_match not in tcase.name):
                tc_err = tcase_enter(trun, tsuite, tcase)
                if not tc_err:
                    tc_err += script_run(trun, tcase)
                    tc_err += tcase_exit(trun, tsuite, tcase)

                tcase.status = "FAIL" if tc_err else "PASS"
                trun.progress["UNKN"] -= 1

            trun.progress[tcase.status] += 1  # Update progress

            ts_err += tc_err                        # Accumulate errors

            trun_to_file(trun)                      # Persist trun
            trun_to_junitfile(trun)                 # Persist as jUNIT XML

        if not ts_ent_err:
            ts_err += tsuite_exit(trun, tsuite)

        ts_err += ts_ent_err                        # Accumulate errors
        tr_err += ts_err

        tsuite.status = "FAIL" if ts_err else "PASS"

        cij.emph("rnr:tsuite %r" % tsuite.status, tsuite.status != "PASS")

    if not tr_ent_err:
        trun_exit(trun)

    tr_err += tr_ent_err
    trun.status = "FAIL" if tr_err else "PASS"

    trun.stamp["end"] = int(time.time()) + 1         # END STAMP
    trun_to_file(trun)                                  # PERSIST
    trun_to_junitfile(trun)                             # Persist as jUNIT XML

    cij.emph("rnr:main:progress %r" % trun.progress)
    cij.emph("rnr:main:trun %r" % trun.status, trun.status != "PASS")

    return trun.progress["FAIL"]
