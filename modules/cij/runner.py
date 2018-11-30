"""
    library functions for the CIJOE test runner, `cij_runner`.
"""
from __future__ import print_function
from subprocess import Popen, STDOUT
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

SCRIPT = {
    "fname": None,
    "fpath": None,
    "res_root": None,
    "log_fpath": None,
    "rcode": None,
    "wallc": None,
}

def yml_fpath(output_path):
    """Returns the path to the trun-file"""

    return os.sep.join([output_path, "trun.yml"])


def script_run(trun, script_fpath, script_run_root, log_tag=None):
    """Execute a hook or testcase"""

    if log_tag is None:
        log_tag = os.path.basename(script_fpath)

    bgn = time.time()
    script_log_fpath = os.sep.join([script_run_root, "run_%s.log" % log_tag])

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:script:run { script_fpath: %r }" % script_fpath)
        cij.emph("rnr:script:run { script_log_fpath: %r }" % script_log_fpath)

    launchers = {
        ".py": "python",
        ".sh": "source"
    }

    ext = os.path.splitext(script_fpath)[-1]
    if not ext in launchers.keys():
        cij.err("rnr:script:run { invalid fname: %r }" % script_fpath)
        return 1

    launch = launchers[ext]

    with open(script_log_fpath, 'a') as script_log_fd:
        script_log_fd.write("# script_fpath: %r\n" % script_fpath)
        script_log_fd.flush()

        cmd = [
            'bash', '-c',
            'source %s && '
            'source cijoe.sh && '
            'CIJ_TEST_RES_ROOT="%s" source %s ' % (
                trun["conf"]["ENV_FPATH"], script_run_root, script_fpath
            )
        ]
        if trun["conf"]["VERBOSE"] > 1:
            cij.emph("rnr:script:run { cmd: %r }" % " ".join(cmd))

        process = Popen(
            cmd,
            stdout=script_log_fd,
            stderr=STDOUT,
            cwd=trun["conf"]["MODULES"]
        )
        process.wait()

        #stdout, stderr = process.communicate()
        rcode = process.returncode
        wallc = time.time() - bgn

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:script:run { wallc: %02f }" % wallc)
        cij.emph("rnr:script:run { rcode: %r } " % rcode)

    return rcode

def hook_setup(trun, hooks=None):
    """
    Setup test-hooks
    @returns dict of hook filepaths {"enter": [], "exit": []}
    """

    hook_fpaths = {
        "enter": [],
        "exit": []
    }

    if hooks is None:       # Nothing to do, just return the struct
        return hook_fpaths

    for hook in hooks:      # Fill out paths
        fpaths = []
        for med in HOOK_PATTERNS:
            for ptn in HOOK_PATTERNS[med]:
                fpath = os.sep.join([trun["conf"]["HOOKS"], ptn % hook])

                if os.path.exists(fpath):
                    hook_fpaths[med].append(fpath)
                    fpaths.append(fpath)

        if not hook_fpaths:
            cij.err("rnr:hook_setup:FAIL { hook: %r has no files }" % hook)
            return None

    return hook_fpaths


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
        return yaml.load(yml_file)


def trun_emph(trun):
    """Print essential info on"""

    if trun["conf"]["VERBOSE"] > 1:               # Print environment variables
        cij.emph("rnr:CONF {")
        for cvar in sorted(trun["conf"].keys()):
            cij.emph("  % 16s: %r" % (cvar, trun["conf"][cvar]))
        cij.emph("}")

    if trun["conf"]["VERBOSE"] > 1:
        cij.emph("rnr:HOOKS {")
        for arg in sorted(trun["hooks"]):
            cij.emph("  % 8s: %r" % (arg, trun["hooks"][arg]))
        cij.emph("}")

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:INFO {")
        cij.emph("  OUTPUT: %r" % trun["conf"]["OUTPUT"])
        cij.emph("  yml_fpath: %r" % yml_fpath(trun["conf"]["OUTPUT"]))
        cij.emph("}")


def tcase_setup(trun, tsuite, tcase_fname):
    """
    @returns a testcase for the given tcase_fpath

    """
    #pylint: disable=locally-disabled, unused-argument

    tcase_fpath = os.sep.join([trun["conf"]["TESTCASES"], tcase_fname])
    if not os.path.exists(tcase_fpath):
        cij.err("rnr:tcase_setup: !tcase_fpath: %r" % tcase_fpath)
        return None

    tcase_fname = os.path.basename(tcase_fpath)
    tcase_name = os.path.splitext(tcase_fname)[0]

    tcase_res_root = os.sep.join([tsuite["res_root"], tcase_fname])
    tcase_aux_root = os.sep.join([tcase_res_root, "_aux"])
    tcase_log_fpath = os.sep.join([tcase_res_root, "run.log"])

    return {
        "ident": "/".join([tsuite["ident"], tcase_fpath]),
        "fpath": tcase_fpath,
        "fname": tcase_fname,
        "name": tcase_name,
        "res_root": tcase_res_root,
        "aux_root": tcase_aux_root,
        "aux_list": [],
        "log_fpath": tcase_log_fpath,

        "hooks": {
            "enter": [],
            "exit": []
        },

        "status": "UNKN",
        "rcode": None,
        "wallc": None,
    }


def tsuite_exit(trun, tsuite):
    """Triggers when exiting the given testsuite"""

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tsuite:exit")

    rcode = 0
    for hook_fpath in reversed(tsuite["hooks"]["exit"]):      # EXIT-hooks
        hook_fname = os.path.basename(hook_fpath)
        rcode = script_run(
            trun,
            hook_fpath,
            tsuite["res_root"],
            "hook_%s" % hook_fname
        )
        if rcode:
            break

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tsuite:exit { rcode: %r }" % rcode)

    return rcode


def tsuite_enter(trun, tsuite):
    """Triggers when entering the given testsuite"""

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tsuite:enter { name: %r }" % tsuite["name"])

    os.makedirs(tsuite["res_root"])                         # Create DIRS
    os.makedirs(tsuite["aux_root"])

    rcode = 0
    for hook_fpath in tsuite["hooks"]["enter"]:     # ENTER-hooks
        hook_fname = os.path.basename(hook_fpath)
        rcode = script_run(
            trun,
            hook_fpath,
            tsuite["res_root"],
            "hook_%s" % hook_fname
        )
        if rcode:
            break

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tsuite:enter { rcode: %r }" % rcode)

    return rcode


def tsuite_setup(trun, tplan_tsuite, enum):
    """
    @returns a list of testcases from tcases_dpath that are in the given
    testsuite (tsuite_fpath)
    """

    tsuite_name = tplan_tsuite["name"]
    tsuite_fname = "%s.suite" % tsuite_name
    tsuite_fpath = os.sep.join([trun["conf"]["TESTSUITES"], tsuite_fname])
    tsuite_ident = "%s_%d" % (tsuite_name, enum)

    tsuite_res_root = os.sep.join([trun["conf"]["OUTPUT"], tsuite_ident])
    tsuite_aux_root = os.sep.join([tsuite_res_root, "_aux"])

    tsuite = {
        "ident": tsuite_ident,
        "name": tsuite_name,
        "hooks": {
            "enter": [],
            "exit": []
        },
        "hooks_pr_tcase": {
            "enter": [],
            "exit": []
        },
        "evars": {},
        "evars_pr_tcase": [],

        "fpath": tsuite_fpath,
        "fname": tsuite_fname,
        "res_root": tsuite_res_root,
        "aux_root": tsuite_aux_root,
        "aux_list": [],
        "testcases": [],

        "status": "UNKN",
        "wallc": None,
    }

    # Setup hooks
    tsuite["hooks"] = hook_setup(trun, tplan_tsuite.get("hooks"))
    tsuite["hooks_pr_tcase"] = hook_setup(trun, tplan_tsuite.get("hooks_pr_tcase"))

    # Filter testcases, remove those that have been commented out with "#"
    tsuite_lines = (l.strip() for l in open(tsuite_fpath).read().splitlines())
    tsuite_tcase_line = (l for l in tsuite_lines if len(l) > 1 and l[0] != "#")

    # Add the tcases by their fname
    for tcase_fname in tsuite_tcase_line:
        tcase = tcase_setup(trun, tsuite, tcase_fname)
        if not tcase:
            cij.err("rnr:tsuite:  SETUP: FAILED")
            return None

        tsuite["testcases"].append(tcase)

    return tsuite


def tcase_exit(trun, tsuite, tcase):
    """..."""
    #pylint: disable=locally-disabled, unused-argument

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tcase:exit { fname: %r }" % tcase["fname"])

    rcode = 0
    for hook_fpath in reversed(tsuite["hooks_pr_tcase"]["exit"]):     # tcase EXIT-hooks
        hook_fname = os.path.basename(hook_fpath)
        rcode = script_run(
            trun,
            hook_fpath,
            tcase["res_root"],
            "hook_%s" % hook_fname
        )
        if rcode:
            break

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tcase:exit { rcode: %r }" % rcode)

    return rcode


def tcase_enter(trun, tsuite, tcase):
    """
    setup res_root and aux_root, log info and run tcase-enter-hooks

    @returns 0 when all hooks succeed, some value othervise
    """
    #pylint: disable=locally-disabled, unused-argument

    os.makedirs(tcase["res_root"])                          # Create OUTPUT dirs
    os.makedirs(tcase["aux_root"])

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tcase:enter")
        cij.emph("rnr:tcase:enter { fname: %r }" % tcase["fname"])
        cij.emph("rnr:tcase:enter { log_fpath: %r }" % tcase["log_fpath"])

    rcode = 0
    for hook_fpath in tsuite["hooks_pr_tcase"]["enter"]:    # tcase ENTER-hooks
        hook_fname = os.path.basename(hook_fpath)
        rcode = script_run(
            trun,
            hook_fpath,
            tcase["res_root"],
            "hook_%s" % hook_fname
        )
        if rcode:
            break

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tcase:exit: { rcode: %r }" % rcode)

    return rcode


def tcase_run(trun, tsuite, tcase):
    """
    Run the given test

    @returns 0 on success, some value othervise
    """
    #pylint: disable=locally-disabled, unused-argument

    cij.emph("rnr:tcase:run { fname: %r }" % tcase["fname"])

    launchers = {
        ".py": "python",
        ".sh": "source"
    }

    ext = os.path.splitext(tcase["fname"])[-1]
    if not ext in launchers.keys():
        cij.err("rnr:tcase:run { invalid fname: %r }" % tcase["fname"])
        return 1

    launch = launchers[ext]

    with open(tcase["log_fpath"], 'a') as log_fd:
        bgn = time.time()
        cmd = [
            'bash', '-c',
            'source %s && '
            'source cijoe.sh && '
            'CIJ_TEST_RES_ROOT="%s" %s %s' % (
                trun["conf"]["ENV_FPATH"],
                tcase["res_root"],
                launch,
                tcase["fpath"]
            )
        ]
        if trun["conf"]["VERBOSE"] > 1:
            cij.emph("rnr:tcase:run { cmd: %r }" % " ".join(cmd))

        process = Popen(
            cmd,
            stdout=log_fd,
            stderr=STDOUT,
            cwd=trun["conf"]["MODULES"]
        )
        process.wait()

        tcase["rcode"] = process.returncode
        tcase["wallc"] = time.time() - bgn

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:tcase:run { wallc: %02f }" % tcase["wallc"])
        cij.emph("rnr:tcase:run { rcode: %r }" % tcase["rcode"])

    return tcase["rcode"]


def trun_exit(trun):
    """Triggers when exiting the given testrun"""

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:trun:exit")

    rcode = 0
    for hook_fpath in reversed(trun["hooks"]["exit"]):    # EXIT-hooks
        hook_fname = os.path.basename(hook_fpath)
        rcode = script_run(
            trun,
            hook_fpath,
            trun["conf"]["OUTPUT"],
            "hook_%s" % hook_fname
        )
        if rcode:
            break

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:trun::exit { rcode: %r }" % rcode, rcode)

    return rcode


def trun_enter(trun):
    """Triggers when entering the given testrun"""

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:trun::enter")

    trun_aux_root = os.sep.join([trun["conf"]["OUTPUT"], "_aux"])      # Create AUX
    os.makedirs(trun_aux_root)

    trun["stamp"]["begin"] = int(time.time())     # Record start timestamp

    rcode = 0
    for hook_fpath in trun["hooks"]["enter"]:     # ENTER-hooks
        hook_fname = os.path.basename(hook_fpath)
        rcode = script_run(
            trun,
            hook_fpath,
            trun["conf"]["OUTPUT"],
            "hook_%s" % hook_fname
        )
        if rcode:
            break

    if trun["conf"]["VERBOSE"]:
        cij.emph("rnr:trun::enter { rcode: %r }" % rcode)

    return rcode


def trun_setup(conf):
    """
    Setup the testrunner data-structure, embedding the parsed environment
    variables and command-line arguments and continues with setup for testplans,
    testsuites, and testcases
    """

    tplan = None
    try:
        with open(conf["TESTPLAN_FPATH"]) as tplan_fd:
            tplan = yaml.load(tplan_fd)
    except AttributeError as exc:
        cij.err("rnr: %r" % exc)

    if not tplan:
        return None

    trun = {
        "ver": cij.VERSION,
        "conf": copy.deepcopy(conf),
        "evars": {},
        "progress": {
            "PASS": 0, "FAIL": 0, "UNKN": 0
        },
        "stamp": {"begin": None, "end": None},
        "hooks": {
            "enter": [],
            "exit": []
        },
        "aux_root": os.sep.join([conf["OUTPUT"], "_aux"]),
        "aux_list": [],

        "testsuites": [],

        "status": "UNKN",
        "wallc": None,
    }

    hooks = tplan.get("hooks")
    if hooks is None:
        hooks = []

    if "lock" not in hooks:
        hooks = ["lock"] + hooks

    if hooks[0] != "lock":
        return None

    # Setup top-level hooks
    trun["hooks"] = hook_setup(trun, hooks)

    for enum, tplan_tsuite in enumerate(tplan["testsuites"]):# Setup testsuites
        tsuite = tsuite_setup(trun, tplan_tsuite, enum)
        if not tsuite:
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
                tc_err += tcase_run(trun, tsuite, tcase)
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
