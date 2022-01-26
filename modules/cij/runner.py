"""
    library functions for the CIJOE test runner, `cij_runner`.
"""
from __future__ import print_function, annotations
from subprocess import Popen, STDOUT
from xml.dom import minidom
import dataclasses
from typing import List, Optional, Dict, Set
import argparse
import shutil
import copy
import time
import os
import yaml
import cij.conf
import cij
from cij.errors import CIJError, InitializationError
# pylint:disable=unsubscriptable-object

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
class Status:
    """ Valid test statuses """
    # pylint: disable=invalid-name

    Pass: str = "PASS"
    Fail: str = "FAIL"
    Unkn: str = "UNKN"


@dataclasses.dataclass
class Runnable:
    """
    Runnable contains the common attributes of testplans, testsuites,
    testcases, and hooks as these are in different way "run".
    """
    # pylint: disable=too-many-instance-attributes
    # There are alot of attributes, which for this class is fine.

    entered: bool = False

    ident: str = "ANON"
    name: str = "UNNAMED"

    fpath_orig: str = ""            # Abs. path to script / suite /  plan
    fpath: str = ""                 # Abs. path to script / suite /  plan
    fname: str = ""                 # Filename without path

    evars: dict = dataclasses.field(default_factory=dict)
    hooks: dict = dataclasses.field(default_factory=lambda: {
        "enter": [],
        "exit": []
    })
    hnames: list = dataclasses.field(default_factory=list)

    res_root: str = ""              # Abs. path to result directory
    aux_root: str = ""              # Abs. path to auxiliary directory
    aux_list: list = dataclasses.field(default_factory=list)

    log_fpath: str = ""             # Abs. path to run.log

    status: str = Status.Unkn
    rcode: Optional[int] = None
    stamp: dict = dataclasses.field(default_factory=lambda: {
        "begin": None,
        "end": None
    })
    wallc: Optional[float] = None

    def enter(self, trun):
        """Called by runner before invoking the runnable"""

        if trun.args.verbose:
            cij.emph("rnr:enter { ident: %r }" % self.ident)

        self.stamp["begin"] = time.time()

        rcode = 0
        for hook in self.hooks["enter"]:  # ENTER-hooks
            rcode = script_run(trun, hook)
            if rcode:
                break

        self.entered = not rcode

        if trun.args.verbose:
            cij.emph("rnr:enter { ident: %r, rcode: %r } " % (
                self.ident, rcode
            ))

        return rcode

    def exit(self, trun):
        """Called by runner after invoking the runnable"""

        if trun.args.verbose:
            cij.emph("rnr:exit: { ident: %r }" % self.ident)

        rcode = 0
        if self.entered:
            for hook in reversed(self.hooks["exit"]):      # EXIT-hooks
                rcode = script_run(trun, hook)
                if rcode:
                    break

        self.stamp["end"] = time.time()
        if self.wallc is None:
            self.wallc = self.stamp["end"] - self.stamp["begin"]

        if trun.args.verbose:
            cij.emph("rnr:exit: { ident: %r, rcode: %r }" % (
                self.ident, rcode
            ))

        return 0


@dataclasses.dataclass
class Hook(Runnable):
    """
    Hooks are user-defined scripts that can be run before and/or after
    TestRuns, TestSuites, and TestCases.
    """

    @staticmethod
    def hooks_from_dict(hooks_dict) -> dict:
        """
        Deserialize a hook dict containing lists of hook dicts dicts into a
        hook dict containing lists of Hooks
        """
        hook_fields = _get_dataclass_fields(Hook)

        hooks: Dict[str, List[Hook]] = {}
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
    """
    TestCases are user-defined scripts used to verify functionality of external
    programs.
    """
    # pylint: disable=too-many-instance-attributes

    status_preq: str = Status.Unkn

    descr: str = ""
    descr_long: str = ""
    src_content: str = ""
    log_content: str = ""
    analysis_log_fpath: str = ""
    analysis_content: str = ""

    @staticmethod
    def tcases_from_dicts(tcase_dicts) -> List[TestCase]:
        """
        Deserialize a list of tcase dictionaries into a list of TestCases
        """
        complex_keys = {'hooks': Hook.hooks_from_dict}
        tcase_fields = _get_dataclass_fields(TestCase)

        tcases = []
        for tcase_dict in tcase_dicts:
            tcase = TestCase()
            for key in tcase_fields & set(tcase_dict):
                deserialize = complex_keys.get(key, lambda x: x)
                setattr(tcase, key, deserialize(tcase_dict[key]))

            tcases.append(tcase)

        return tcases


@dataclasses.dataclass
class TestSuite(Runnable):
    """
    TestSuites are used for grouping TestCases, allowing them to share
    configurations, e.g. environment variables and hooks.
    """
    # pylint: disable=too-many-instance-attributes

    alias: str = ""

    progress: dict = dataclasses.field(default_factory=lambda: {
        Status.Pass: 0,
        Status.Fail: 0,
        Status.Unkn: 0
    })
    status_preq: str = Status.Unkn

    hooks_pr_tcase: list = dataclasses.field(default_factory=list)
    testcases: List[TestCase] = dataclasses.field(default_factory=list)

    log_content: str = ""

    @staticmethod
    def tsuites_from_dicts(tsuites_dicts) -> List[TestSuite]:
        """
        Deserialize a list of tsuite dicts into a list of TestSuites
        """
        complex_keys = {
            'testcases': TestCase.tcases_from_dicts,
            'hooks': Hook.hooks_from_dict,
        }
        tsuite_fields = _get_dataclass_fields(TestSuite)

        tsuites = []
        for tsuite_dict in tsuites_dicts:
            tsuite = TestSuite()
            for key in tsuite_fields & set(tsuite_dict):
                deserialize = complex_keys.get(key, lambda x: x)
                setattr(tsuite, key, deserialize(tsuite_dict[key]))

            tsuites.append(tsuite)

        return tsuites


@dataclasses.dataclass
class TestPlan(Runnable):
    """
    TestPlans contain information required to execute a testplan.
    """
    # pylint: disable=too-many-instance-attributes

    progress: dict = dataclasses.field(default_factory=lambda: {
        Status.Pass: 0,
        Status.Fail: 0,
        Status.Unkn: 0
    })

    status_preq: str = Status.Unkn
    log_content: str = ""

    testsuites: List[TestSuite] = dataclasses.field(default_factory=list)

    @staticmethod
    def from_dict(tplan_dict) -> TestPlan:
        """
        Deserialize a tplan dict into TestPlan
        """
        complex_keys = {
            'testsuites': TestSuite.tsuites_from_dicts,
            'hooks': Hook.hooks_from_dict,
        }

        tplan = TestPlan()

        fields = _get_dataclass_fields(TestPlan) & set(tplan_dict)
        for key in fields:
            deserialize = complex_keys.get(key, lambda x: x)
            setattr(tplan, key, deserialize(tplan_dict[key]))

        return tplan

    @staticmethod
    def tplans_from_dicts(lod) -> List[TestPlan]:
        """
        Transform a list of testplan dicts to a list of TestPlan
        """

        return [TestPlan.from_dict(tpd) for tpd in lod]


@dataclasses.dataclass
class TestRun(Runnable):
    """
    TestRuns contain information required to execute a testplan.
    """
    # pylint: disable=too-many-instance-attributes

    ver: str = ""
    args: argparse.Namespace = dataclasses.field(
        default_factory=argparse.Namespace
    )
    conf: cij.conf.Config = dataclasses.field(
        default_factory=cij.conf.Config
    )
    counter: int = 0
    progress: dict = dataclasses.field(default_factory=lambda: {
        Status.Pass: 0,
        Status.Fail: 0,
        Status.Unkn: 0
    })

    testplans: List[TestPlan] = dataclasses.field(default_factory=list)

    status_preq: str = Status.Unkn
    log_content: str = ""

    def inc(self):
        """Increment and return counter"""

        self.counter += 1

        return self.counter

    @staticmethod
    def from_dict(trun_dict) -> TestRun:
        """
        Deserialize a trun dict into TestRun
        """

        def args_from_dict(adict: dict) -> argparse.Namespace:
            """Construct argparse.Namespace from dict"""

            namespace = argparse.Namespace()
            namespace.__dict__.update(adict)

            return namespace

        complex_keys = {
            'testplans': TestPlan.tplans_from_dicts,
            'args': args_from_dict
        }

        trun = TestRun()

        fields = _get_dataclass_fields(TestRun) & set(trun_dict)
        for key in fields:
            deserialize = complex_keys.get(key, lambda x: x)
            setattr(trun, key, deserialize(trun_dict[key]))

        return trun


def _get_dataclass_fields(dclass) -> Set[str]:
    return set(getattr(dclass, "__dataclass_fields__"))


def yml_fpath(output_path):
    """Returns the path to the trun YAML-file"""

    return os.path.join(output_path, "trun.yml")


def junit_fpath(output_path):
    """Returns the path to the jUNIT XML-file"""

    return os.path.join(output_path, "trun.xml")


def script_run(trun: TestRun, script: Runnable):
    """Execute a script or testcase"""

    if trun.args.verbose:
        cij.emph("rnr:script:run { script: %s }" % script)
        cij.emph("rnr:script:run:evars: %s" % script.evars)

    launchers = {
        ".py": "python",
        ".sh": "source"
    }

    ext = os.path.splitext(script.fpath)[-1]
    if ext not in launchers:
        cij.err("rnr:script:run { invalid script.fpath: %r }" % script.fpath)
        return 1

    launch = launchers[ext]

    with open(script.log_fpath, "a", encoding="UTF-8") as log_fd:
        log_fd.write("# script_fpath: %r\n" % script.fpath)
        log_fd.flush()

        script.stamp["begin"] = time.time()

        cmd = [
            'bash', '-c',
            'CIJ_ROOT=$(cij_root) && '
            'source $CIJ_ROOT/modules/cijoe.sh && '
            'source %s && '
            'CIJ_TEST_RES_ROOT="%s" %s %s ' % (
                trun.args.env_fpath,
                script.res_root,
                launch,
                script.fpath
            )
        ]
        if trun.args.verbose > 1:
            cij.emph("rnr:script:run { cmd: %r }" % " ".join(cmd))

        evars = os.environ.copy()
        evars.update({k: str(script.evars[k]) for k in script.evars})

        with Popen(
                cmd,
                stdout=log_fd,
                stderr=STDOUT,
                cwd=script.res_root,
                env=evars
        ) as process:
            process.wait()

            script.rcode = process.returncode
            script.stamp["end"] = time.time()
            script.wallc = script.stamp["end"] - script.stamp["begin"]

    if trun.args.verbose:
        cij.emph("rnr:script:run { wallc: %02f }" % (
            script.wallc if script.wallc is not None else 0.0
        ))
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
    hook.fpath = os.path.join(hook.res_root, hook.fname)
    hook.log_fpath = os.path.join(hook.res_root, "%s.log" % hook.fname)

    hook.evars.update(copy.deepcopy(parent.evars))

    shutil.copyfile(hook.fpath_orig, hook.fpath)

    return hook


def hooks_setup(trun: TestRun, instance: Runnable, hnames=None):
    """
    Setup hooks on the given 'instance' on the form:

      .hooks: {"enter": [], "exit": []}
      .hnames: ["hook1", "hook2"]

    """
    hooks: Dict[str, List[Hook]] = {
        "enter": [],
        "exit": []
    }

    if hnames is None:          # Setup empty hooks
        instance.hnames = []
        instance.hooks = hooks
        return

    for hname in hnames:        # Fill out paths
        for med, patterns in HOOK_PATTERNS.items():
            for ptn in patterns:
                fpath = os.path.join(trun.conf.hooks, ptn % hname)
                if not os.path.exists(fpath):
                    continue

                hook = hook_setup(instance, fpath)
                hooks[med].append(hook)

        if not hooks["enter"] + hooks["exit"]:
            msg = "rnr:hooks_setup:FAIL { hname: %r has no files }" % hname
            cij.err(msg)
            raise InitializationError(msg)

    instance.hooks = hooks
    instance.hnames = hnames


def trun_to_file(trun: TestRun, fpath=None):
    """Dump the given trun to file"""

    def dict_factory(instance):
        """Special handling of 'args' using vars() to emit dict"""

        return dict(
            (x[0], vars(x[1])) if x[0] == "args" else x for x in instance
        )

    if fpath is None:
        fpath = yml_fpath(trun.args.output)

    trun_dict = dataclasses.asdict(trun, dict_factory=dict_factory)
    with open(fpath, 'w', encoding="UTF-8") as yml_file:
        data = yaml.dump(
            trun_dict, explicit_start=True, default_flow_style=False
        )
        yml_file.write(data)


def trun_to_junitfile(trun: TestRun, fpath=None) -> int:
    """Generate jUNIT XML from testrun YML"""

    try:
        if fpath is None:
            fpath = junit_fpath(trun.args.output)

        doc = minidom.Document()
        doc_testsuites = doc.createElement('testsuites')

        duration = max(
            0,
            (trun.stamp["end"] or time.time()) -
            (trun.stamp["begin"] or time.time())
        )

        doc_testsuites.setAttribute("duration", str(duration))

        doc.appendChild(doc_testsuites)

        for tplan in trun.testplans:
            for tsuite in tplan.testsuites:
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
                    if not tcase.wallc:
                        tcase.wallc = 0.0

                    wallc_total += tcase.wallc

                    doc_tcase = doc.createElement("testcase")
                    doc_tcase.setAttribute(
                        "name", str(tcase.name)
                    )
                    doc_tcase.setAttribute(
                        "classname", str(tcase.ident)
                    )
                    doc_tcase.setAttribute("time", "%0.3f" % tcase.wallc)

                    if tcase.rcode != 0:
                        nfailures += 1

                        doc_failure = doc.createElement("failure")
                        doc_failure.setAttribute(
                            "message",
                            "not executed" if tcase.rcode is None else
                            "test failed"
                        )

                        doc_tcase.appendChild(doc_failure)

                    doc_tsuite.appendChild(doc_tcase)

                doc_tsuite.setAttribute("failures", str(nfailures))
                doc_tsuite.setAttribute("time", "%0.3f" % wallc_total)

                doc_testsuites.appendChild(doc_tsuite)

        with open(fpath, "w", encoding="UTF-8") as junitf:
            junitf.write(doc.toprettyxml(indent="  "))

    except Exception as ex:     # pylint: disable=broad-except
        cij.err("Failed persisting testrun as jUNIT XML, ex(%r)" % ex)
        return 1

    return 0


def trun_from_file(fpath) -> TestRun:
    """Returns trun from the given fpath"""

    with open(fpath, 'r', encoding="UTF-8") as yml_file:
        trun_dict = yaml.safe_load(yml_file)
        return TestRun.from_dict(trun_dict)


def trun_emph(trun: TestRun):
    """Print essential info on"""

    if trun.args.verbose > 1:               # Print environment variables
        cij.emph("rnr:conf {")
        conf_dict = dataclasses.asdict(trun.conf)
        for var in sorted(conf_dict.keys()):
            cij.emph("  % 16s: %r" % (var, conf_dict[var]))
        cij.emph("}")

        cij.emph("rnr:args {")
        args_dict = vars(trun.args)
        for var in sorted(args_dict.keys()):
            cij.emph("  % 16s: %r" % (var, args_dict[var]))
        cij.emph("}")

    if trun.args.verbose:
        cij.emph("rnr:INFO {")
        cij.emph("  output: %r" % trun.args.output)
        cij.emph("  yml_fpath: %r" % yml_fpath(trun.args.output))
        cij.emph("}")


def tcase_setup(trun: TestRun, parent, tcase_fname) -> TestCase:
    """
    Create and initialize a testcase
    """
    # pylint: disable=locally-disabled, unused-argument

    case = TestCase()

    case.fname = tcase_fname
    case.fpath_orig = os.path.join(trun.conf.testcases, case.fname)

    if not os.path.exists(case.fpath_orig):
        msg = ("rnr:tcase_setup: file case.fpath_orig does not exist: "
               "%r" % case.fpath_orig)
        cij.err(msg)
        raise InitializationError(msg)

    case.name = os.path.splitext(case.fname)[0]
    case.ident = "/".join([parent.ident, case.fname])

    case.res_root = os.path.join(parent.res_root, case.fname)
    case.aux_root = os.path.join(case.res_root, "_aux")
    case.log_fpath = os.path.join(case.res_root, "run.log")
    case.analysis_log_fpath = os.path.join(case.res_root, "analysis.log")

    case.fpath = os.path.join(case.res_root, case.fname)

    case.evars.update(copy.deepcopy(parent.evars))

    # Initalize
    os.makedirs(case.res_root)                       # Create DIRS
    os.makedirs(case.aux_root)
    shutil.copyfile(case.fpath_orig, case.fpath)  # Copy testcase

    # Initialize hooks
    hooks_setup(trun, case, parent.hooks_pr_tcase)

    return case


def tsuite_setup(trun: TestRun, tplan: TestPlan, declr, enum) -> TestSuite:
    """
    Creates and initialized a TESTSUITE struct and site-effects such as
    creating output directories and forwarding initialization of testcases
    """

    suite = TestSuite()  # Setup the test-suite

    suite.name = declr.get("name")
    if suite.name is None:
        cij.err("rnr:tsuite_setup: no testsuite is given")
        return None

    suite.alias = declr.get("alias")
    suite.ident = "%s_%d" % (suite.name, enum)

    suite.res_root = os.path.join(tplan.res_root, suite.ident)
    suite.aux_root = os.path.join(suite.res_root, "_aux")

    suite.evars.update(copy.deepcopy(tplan.evars))
    suite.evars.update(copy.deepcopy(declr.get("evars", {})))

    # Initialize
    os.makedirs(suite.res_root)
    os.makedirs(suite.aux_root)

    # Setup testsuite-hooks
    hooks_setup(trun, suite, declr.get("hooks"))

    # Forward from declaration
    suite.hooks_pr_tcase = declr.get("hooks_pr_tcase", [])

    suite.fname = "%s.suite" % suite.name
    suite.fpath = os.path.join(trun.conf.testsuites, suite.fname)

    #
    # Load testcases from .suite file OR from declaration
    #
    tcase_fpaths: List[str] = []                 # Load testcase fpaths
    if os.path.exists(suite.fpath):              # From suite-file
        with open(suite.fpath, encoding="UTF-8") as sfd:
            suite_lines = (
                line.strip() for line in sfd.read().splitlines()
            )
            tcase_fpaths.extend((
                line for line in suite_lines
                if len(line) > 1 and line[0] != "#"
            ))
    else:                                           # From declaration
        tcase_fpaths.extend(declr.get("testcases", []))

    # NOTE: fix duplicates; allow them
    # NOTE: Currently hot-fixed here
    if len(set(tcase_fpaths)) != len(tcase_fpaths):
        msg = "rnr:suite: failed: duplicate tcase in suite not supported"
        cij.err(msg)
        raise InitializationError(msg)

    for tcase_fname in tcase_fpaths:                # Setup testcases
        tcase = tcase_setup(trun, suite, tcase_fname)
        suite.testcases.append(tcase)

        suite.progress[Status.Unkn] += len(suite.testcases)

    return suite


def tplan_setup(trun: TestRun, tplan_fpath) -> TestPlan:
    """
    Setup the testplan data-structure, embedding the parsed environment
    variables and command-line arguments and continues with setup for
    testsuites, and testcases
    """

    tplan = TestPlan()

    tplan.fpath_orig = tplan_fpath
    tplan.fpath = tplan.fpath_orig
    tplan.fname = os.path.basename(tplan.fpath)
    tplan.name = ".".join(tplan.fname.split(".")[:-1])
    tplan.ident = "%s_%d" % (tplan.name, trun.inc())

    tplan.res_root = os.path.join(trun.args.output, tplan.ident)
    tplan.aux_root = os.path.join(tplan.res_root, "_aux")

    declr = None
    try:
        with open(tplan.fpath, encoding="UTF-8") as declr_fd:
            declr = yaml.safe_load(declr_fd)
    except AttributeError as exc:
        cij.err("rnr: %r" % exc)

    if not declr:
        msg = "rnr:tplan_setup: failed to read declaration"
        cij.err(msg)
        raise InitializationError(msg)

    tplan.evars.update(copy.deepcopy(declr.get("evars", {})))

    os.makedirs(tplan.aux_root)

    # Setup top-level hooks
    hooks_setup(trun, tplan, declr.get("hooks", []))

    for enum, declr in enumerate(declr["testsuites"]):  # Setup testsuites
        tsuite = tsuite_setup(trun, tplan, declr, enum)
        tplan.testsuites.append(tsuite)

        trun.progress[Status.Unkn] += len(tsuite.testcases)
        tplan.progress[Status.Unkn] += len(tsuite.testcases)

    return tplan


def trun_setup(args: argparse.Namespace, conf: cij.conf.Config) -> TestRun:
    """
    Setup the testrunner data-structure, embedding the parsed environment
    variables and command-line arguments and continues with setup for
    testplans, testsuites, and testcases
    """

    trun = TestRun()
    trun.ver = cij.VERSION
    trun.args = args
    trun.conf = conf

    trun.fpath_orig = args.output
    trun.fpath = trun.fpath_orig
    trun.fname = os.path.basename(trun.fpath)
    trun.name = trun.fname
    trun.ident = trun.name

    trun.res_root = args.output
    trun.aux_root = os.path.join(trun.res_root, "_aux")

    os.makedirs(trun.aux_root)

    trun.testplans = [
        tplan_setup(trun, tp_fpath) for tp_fpath in args.testplans
    ]

    return trun


def main(args, conf):
    """CIJ Test Runner main entry point"""
    # pylint: disable=too-many-branches
    # pylint: disable=too-many-statements
    # There are a lot of branches and statements here... but that is fine.

    fpath = yml_fpath(args.output)
    if os.path.exists(fpath):   # YAML exists, we exit, it might be RUNNING!
        cij.err("main:FAILED { fpath: %r }, exists" % fpath)
        return 1

    trun: TestRun
    try:
        trun = trun_setup(args, conf)   # Construct 'trun' from args and conf
    except CIJError as ex:
        cij.err("main:FAILED to start testrun: %s" % ex)

    trun_to_file(trun)              # Persist trun
    trun_to_junitfile(trun)         # Persist as jUNIT XML

    trun.enter(trun)

    for tplan in (tp for tp in trun.testplans if trun.entered):
        tplan.enter(trun)

        for tsuite in (ts for ts in tplan.testsuites if tplan.entered):
            tsuite.enter(trun)

            for tcase in (tc for tc in tsuite.testcases if tsuite.entered):
                if (args.testcase_match is None
                        or args.testcase_match in tcase.name):
                    tcase.enter(trun)
                    if tcase.entered:
                        script_run(trun, tcase)
                    tcase.exit(trun)

                    tcase.status = Status.Pass
                    if tcase.rcode is None or tcase.rcode:
                        tcase.status = Status.Fail
                        cij.err(f"main:{tcase.ident} failed.")
                        cij.err(f"See log: `less {tcase.log_fpath}`")

                    tsuite.progress[Status.Unkn] -= 1   # Update progress
                    tplan.progress[Status.Unkn] -= 1
                    trun.progress[Status.Unkn] -= 1

                tsuite.progress[tcase.status] += 1      # Update progress
                tplan.progress[tcase.status] += 1
                trun.progress[tcase.status] += 1

                if tcase.status == Status.Fail:         # Propagate failure
                    trun.status = tplan.status = tsuite.status = tcase.status

                trun_to_file(trun)                      # Persist trun
                trun_to_junitfile(trun)                 # Persist as jUNIT XML

            if tsuite.exit(trun) or not tsuite.entered:
                trun.status = tplan.status = tsuite.status = Status.Fail
            if tsuite.status == Status.Unkn and tsuite.entered:
                tsuite.status = Status.Pass

            trun_to_file(trun)                      # Persist trun
            trun_to_junitfile(trun)                 # Persist as jUNIT XML

        if tplan.exit(trun) or not tplan.entered:
            trun.status = tplan.status = Status.Fail
        if tplan.status == Status.Unkn and tplan.entered:
            tplan.status = Status.Pass

        trun_to_file(trun)                      # Persist trun
        trun_to_junitfile(trun)                 # Persist as jUNIT XML

    if trun.exit(trun) or not trun.entered:
        trun.status = Status.Fail
    if trun.status == Status.Unkn and trun.entered:
        trun.status = Status.Pass

    trun_to_file(trun)                                  # PERSIST
    trun_to_junitfile(trun)                             # Persist as jUNIT XML

    cij.emph("rnr:main:progress %r" % trun.progress)
    cij.emph("rnr:main:trun %r" % trun.status, trun.status != Status.Pass)

    return trun.progress[Status.Fail]
