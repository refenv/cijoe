"""
    library functions for the CIJOE test runner, `cij_runner`.
"""
from __future__ import print_function
from subprocess import Popen, STDOUT
import shutil
import copy
import time
import os
import yaml
import cij.test
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

HOOK = {
    "evars": {},

    "name": None,
    "fname": None,
    "fpath": None,
    "fpath_orig": None,

    "res_root": None,
    "log_fpath": None,
    "rcode": None,
    "wallc": None,
}

TESTSUITE = {
    "ident": None,
    "name": None,
    "alias": None,
    "hooks": {
        "enter": [],
        "exit": []
    },
    "evars": {},

    "fpath": None,
    "fname": None,
    "res_root": None,
    "aux_root": None,
    "aux_list": [],

    "status": "UNKN",
    "wallc": None,

    "testcases": [],
    "hooks_pr_tcase": [],
}

TESTCASE = {
    "ident": None,
    "fpath": None,
    "fname": None,
    "name": None,
    "res_root": None,
    "aux_root": None,
    "aux_list": [],
    "log_fpath": None,

    "hooks": None,
    "evars": {},

    "status": "UNKN",
    "rcode": None,
    "wallc": None,
}

TRUN = {
    "ver": None,
    "conf": None,
    "evars": {},
    "progress": {
        "PASS": 0,
        "FAIL": 0,
        "UNKN": 0
    },
    "stamp": {
        "begin": None,
        "end": None
    },
    "hooks": {
        "enter": [],
        "exit": []
    },
    "res_root": None,
    "aux_root": None,
    "aux_list": [],

    "testsuites": [],

    "status": "UNKN",
    "wallc": None,
}


def yml_fpath(output_path):
    """Returns the path to the trun-file"""

    return os.sep.join([output_path, "trun.yml"])


def script_run(trun, script):
    """Execute a script or testcase"""

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:script:run { script: %s }" % script)
        cij.emph("rnr:script:run:evars: %s" % script["evars"])

    launchers = {
        ".py": "python",
        ".sh": "source"
    }

    ext = os.path.splitext(script["fpath"])[-1]
    if not ext in launchers.keys():
        cij.err("rnr:script:run { invalid script[\"fpath\"]: %r }" % script["fpath"])
        return 1

    launch = launchers[ext]

    with open(script["log_fpath"], "a") as log_fd:
        log_fd.write("# script_fpath: %r\n" % script["fpath"])
        log_fd.flush()

        bgn = time.time()
        cmd = [
            'bash', '-c',
            'CIJ_ROOT=$(cij_root) && '
            'source $CIJ_ROOT/modules/cijoe.sh && '
            'source %s && '
            'CIJ_TEST_RES_ROOT="%s" %s %s ' % (
                trun["conf"]["ENV_FPATH"],
                script["res_root"],
                launch,
                script["fpath"]
            )
        ]
        if trun["conf"]["VERBOSE"] > 1:
            cij.emph("rnr:script:run { cmd: %r }" % " ".join(cmd))

        evars = os.environ.copy()
        evars.update({k: str(script["evars"][k]) for k in script["evars"]})

        process = Popen(
            cmd,
            stdout=log_fd,
            stderr=STDOUT,
            cwd=script["res_root"],
            env=evars
        )
        process.wait()

        script["rcode"] = process.returncode
        script["wallc"] = time.time() - bgn

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:script:run { wallc: %02f }" % script["wallc"])
        cij.emph(
            "rnr:script:run { rcode: %r } " % script["rcode"],
            script["rcode"]
        )

    return script["rcode"]

def hook_setup(parent, hook_fpath):
    """Setup hook"""

    hook = copy.deepcopy(HOOK)
    hook["name"] = os.path.splitext(os.path.basename(hook_fpath))[0]
    hook["name"] = hook["name"].replace("_enter", "").replace("_exit", "")
    hook["res_root"] = parent["res_root"]
    hook["fpath_orig"] = hook_fpath
    hook["fname"] = "hook_%s" % os.path.basename(hook["fpath_orig"])
    hook["fpath"] = os.sep.join([hook["res_root"], hook["fname"]])
    hook["log_fpath"] = os.sep.join([
        hook["res_root"],
        "%s.log" % hook["fname"]
    ])

    hook["evars"].update(copy.deepcopy(parent["evars"]))

    shutil.copyfile(hook["fpath_orig"], hook["fpath"])

    return hook

def hooks_setup(trun, parent, hnames=None):
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
                fpath = os.sep.join([trun["conf"]["HOOKS"], ptn % hname])
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
        fpath = yml_fpath(trun["conf"]["OUTPUT"])

    with open(fpath, 'w') as yml_file:
        data = yaml.dump(trun, explicit_start=True, default_flow_style=False)
        yml_file.write(data)


def trun_from_file(fpath):
    """Returns trun from the given fpath"""

    with open(fpath, 'r') as yml_file:
        return yaml.safe_load(yml_file)


def trun_emph(trun):
    """Print essential info on"""

    if trun["conf"]["VERBOSE"] > 1:               # Print environment variables
        cij.emph("rnr:CONF {")
        for cvar in sorted(trun["conf"].keys()):
            cij.emph("  % 16s: %r" % (cvar, trun["conf"][cvar]))
        cij.emph("}")

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:INFO {")
        cij.emph("  OUTPUT: %r" % trun["conf"]["OUTPUT"])
        cij.emph("  yml_fpath: %r" % yml_fpath(trun["conf"]["OUTPUT"]))
        cij.emph("}")


def tcase_setup(trun, parent, tcase_fname):
    """
    Create and initialize a testcase
    """
    #pylint: disable=locally-disabled, unused-argument

    case = copy.deepcopy(TESTCASE)

    case["fname"] = tcase_fname
    case["fpath_orig"] = os.sep.join([trun["conf"]["TESTCASES"], case["fname"]])

    if not os.path.exists(case["fpath_orig"]):
        cij.err('rnr:tcase_setup: !case["fpath_orig"]: %r' % case["fpath_orig"])
        return None

    case["name"] = os.path.splitext(case["fname"])[0]
    case["ident"] = "/".join([parent["ident"], case["fname"]])

    case["res_root"] = os.sep.join([parent["res_root"], case["fname"]])
    case["aux_root"] = os.sep.join([case["res_root"], "_aux"])
    case["log_fpath"] = os.sep.join([case["res_root"], "run.log"])

    case["fpath"] = os.sep.join([case["res_root"], case["fname"]])

    case["evars"].update(copy.deepcopy(parent["evars"]))

    # Initalize
    os.makedirs(case["res_root"])                       # Create DIRS
    os.makedirs(case["aux_root"])
    shutil.copyfile(case["fpath_orig"], case["fpath"])  # Copy testcase

    # Initialize hooks
    case["hooks"] = hooks_setup(trun, case, parent.get("hooks_pr_tcase"))

    return case


def tsuite_exit(trun, tsuite):
    """Triggers when exiting the given testsuite"""

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tsuite:exit")

    rcode = 0
    for hook in reversed(tsuite["hooks"]["exit"]):      # EXIT-hooks
        rcode = script_run(trun, hook)
        if rcode:
            break

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tsuite:exit { rcode: %r } " % rcode, rcode)

    return rcode


def tsuite_enter(trun, tsuite):
    """Triggers when entering the given testsuite"""

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tsuite:enter { name: %r }" % tsuite["name"])

    rcode = 0
    for hook in tsuite["hooks"]["enter"]:     # ENTER-hooks
        rcode = script_run(trun, hook)
        if rcode:
            break

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tsuite:enter { rcode: %r } " % rcode, rcode)

    return rcode

def tsuite_setup(trun, declr, enum):
    """
    Creates and initialized a TESTSUITE struct and site-effects such as creating
    output directories and forwarding initialization of testcases
    """

    suite = copy.deepcopy(TESTSUITE)  # Setup the test-suite

    suite["name"] = declr.get("name")
    if suite["name"] is None:
        cij.err("rnr:tsuite_setup: no testsuite is given")
        return None

    suite["alias"] = declr.get("alias")
    suite["ident"] = "%s_%d" % (suite["name"], enum)

    suite["res_root"] = os.sep.join([trun["conf"]["OUTPUT"], suite["ident"]])
    suite["aux_root"] = os.sep.join([suite["res_root"], "_aux"])

    suite["evars"].update(copy.deepcopy(trun["evars"]))
    suite["evars"].update(copy.deepcopy(declr.get("evars", {})))

    # Initialize
    os.makedirs(suite["res_root"])
    os.makedirs(suite["aux_root"])

    # Setup testsuite-hooks
    suite["hooks"] = hooks_setup(trun, suite, declr.get("hooks"))

    # Forward from declaration
    suite["hooks_pr_tcase"] = declr.get("hooks_pr_tcase", [])

    suite["fname"] = "%s.suite" % suite["name"]
    suite["fpath"] = os.sep.join([trun["conf"]["TESTSUITES"], suite["fname"]])

    #
    # Load testcases from .suite file OR from declaration
    #
    tcase_fpaths = []                               # Load testcase fpaths
    if os.path.exists(suite["fpath"]):              # From suite-file
        suite_lines = (
            l.strip() for l in open(suite["fpath"]).read().splitlines()
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

        suite["testcases"].append(tcase)

    return suite


def tcase_exit(trun, tsuite, tcase):
    """..."""
    #pylint: disable=locally-disabled, unused-argument

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tcase:exit { fname: %r }" % tcase["fname"])

    rcode = 0
    for hook in reversed(tcase["hooks"]["exit"]):    # tcase EXIT-hooks
        rcode = script_run(trun, hook)
        if rcode:
            break

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tcase:exit { rcode: %r }" % rcode, rcode)

    return rcode


def tcase_enter(trun, tsuite, tcase):
    """
    setup res_root and aux_root, log info and run tcase-enter-hooks

    @returns 0 when all hooks succeed, some value othervise
    """
    #pylint: disable=locally-disabled, unused-argument

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tcase:enter")
        cij.emph("rnr:tcase:enter { fname: %r }" % tcase["fname"])
        cij.emph("rnr:tcase:enter { log_fpath: %r }" % tcase["log_fpath"])

    rcode = 0
    for hook in tcase["hooks"]["enter"]:    # tcase ENTER-hooks
        rcode = script_run(trun, hook)
        if rcode:
            break

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tcase:exit: { rcode: %r }" % rcode, rcode)

    return rcode

def trun_exit(trun):
    """Triggers when exiting the given testrun"""

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:trun:exit")

    rcode = 0
    for hook in reversed(trun["hooks"]["exit"]):    # EXIT-hooks
        rcode = script_run(trun, hook)
        if rcode:
            break

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:trun::exit { rcode: %r }" % rcode, rcode)

    return rcode


def trun_enter(trun):
    """Triggers when entering the given testrun"""

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:trun::enter")

    trun["stamp"]["begin"] = int(time.time())     # Record start timestamp

    rcode = 0
    for hook in trun["hooks"]["enter"]:     # ENTER-hooks
        rcode = script_run(trun, hook)
        if rcode:
            break

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:trun::enter { rcode: %r }" % rcode, rcode)

    return rcode


def trun_setup(conf):
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

    trun = copy.deepcopy(TRUN)
    trun["ver"] = cij.VERSION

    trun["conf"] = copy.deepcopy(conf)
    trun["res_root"] = conf["OUTPUT"]
    trun["aux_root"] = os.sep.join([trun["res_root"], "_aux"])
    trun["evars"].update(copy.deepcopy(declr.get("evars", {})))

    os.makedirs(trun["aux_root"])

    hook_names = declr.get("hooks", [])
    if "lock" not in hook_names:
        hook_names = ["lock"] + hook_names

    if hook_names[0] != "lock":
        return None

    # Setup top-level hooks
    trun["hooks"] = hooks_setup(trun, trun, hook_names)

    for enum, declr in enumerate(declr["testsuites"]):  # Setup testsuites
        tsuite = tsuite_setup(trun, declr, enum)
        if tsuite is None:
            cij.err("main::FAILED: setting up tsuite: %r" % tsuite)
            return 1

        trun["testsuites"].append(tsuite)
        trun["progress"]["UNKN"] += len(tsuite["testcases"])

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
    trun_emph(trun)                 # Print trun before run

    tr_err = 0
    tr_ent_err = trun_enter(trun)
    for tsuite in (ts for ts in trun["testsuites"] if not tr_ent_err):

        ts_err = 0
        ts_ent_err = tsuite_enter(trun, tsuite)
        for tcase in (tc for tc in tsuite["testcases"] if not ts_ent_err):

            tc_err = tcase_enter(trun, tsuite, tcase)
            if not tc_err:
                tc_err += script_run(trun, tcase)
                tc_err += tcase_exit(trun, tsuite, tcase)

            tcase["status"] = "FAIL" if tc_err else "PASS"

            trun["progress"][tcase["status"]] += 1  # Update progress
            trun["progress"]["UNKN"] -= 1

            ts_err += tc_err                        # Accumulate errors

            trun_to_file(trun)                      # Persist trun

        if not ts_ent_err:
            ts_err += tsuite_exit(trun, tsuite)

        ts_err += ts_ent_err                        # Accumulate errors
        tr_err += ts_err

        tsuite["status"] = "FAIL" if ts_err else "PASS"

        cij.emph("rnr:tsuite %r" % tsuite["status"], tsuite["status"] != "PASS")

    if not tr_ent_err:
        trun_exit(trun)

    tr_err += tr_ent_err
    trun["status"] = "FAIL" if tr_err else "PASS"

    trun["stamp"]["end"] = int(time.time()) + 1         # END STAMP
    trun_to_file(trun)                                  # PERSIST

    cij.emph("rnr:main:progress %r" % trun["progress"])
    cij.emph("rnr:main:trun %r" % trun["status"], trun["status"] != "PASS")

    return trun["progress"]["UNKN"] + trun["progress"]["FAIL"]
