"""
    library functions for the CIJOE test runner, `cij_runner`.
"""
from __future__ import print_function
from subprocess import Popen, STDOUT
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


def yml_fpath(output_path):
    """Returns the path to the trun-file"""

    return os.sep.join([output_path, "trun.yml"])


def hook_setup(evars, hooks=None):
    """
    Setup test-hooks
    @returns dict of hook filepaths {"enter": [], "exit": []}
    """

    hook_fpaths = {"enter": [], "exit": []}

    if hooks is None:       # Nothing to do, just return the struct
        return hook_fpaths

    for hook in hooks:      # Fill out paths
        fpaths = []
        for med in HOOK_PATTERNS:
            for ptn in HOOK_PATTERNS[med]:
                fpath = os.sep.join([evars["HOOKS"], ptn % hook])

                if os.path.exists(fpath):
                    hook_fpaths[med].append(fpath)
                    fpaths.append(fpath)

        if not hook_fpaths:
            cij.err("rnr:hook_setup:FAIL { hook: %r has no files }" % hook)
            return None

    return hook_fpaths


def hook_run(args, evars, hook_fpath, hook_run_root):
    """Run the given hook"""

    bgn = time.time()
    hook_log_path = os.sep.join([hook_run_root, "run.log"])

    if args.verbose:
        cij.emph("rnr:hook:run { hook_fpath: %r }" % hook_fpath)
        cij.emph("rnr:hook:run { hook_log_path: %r }" % hook_log_path)

    with open(hook_log_path, 'a') as log_fd:
        log_fd.write("# hook_fpath: %r\n" % hook_fpath)
        log_fd.flush()

        cmd = [
            'bash', '-c',
            'source cijoe.sh && '
            'source %s && '
            'CIJ_TEST_RES_ROOT="%s" source %s ' % (
                args.env_fpath, hook_run_root, hook_fpath
            )
        ]
        if args.verbose > 1:
            cij.emph("rnr:hook:run { cmd: %r }" % " ".join(cmd))

        process = Popen(
            cmd,
            stdout=log_fd,
            stderr=STDOUT,
            cwd=evars["MODULES"]
        )
        stdout, stderr = process.communicate()
        wallc = time.time() - bgn
        rcode = process.returncode

        hook_res = rcode, wallc, stdout, stderr

    if args.verbose:
        cij.emph("rnr:hook:run { rcode: %r } " % rcode, rcode)

    return hook_res


def trun_to_file(trun, fpath=None):
    """Dump the given trun to file"""

    if fpath is None:
        fpath = yml_fpath(trun["args"]["output"])

    with open(fpath, 'w') as yml_file:
        data = yaml.dump(trun, explicit_start=True, default_flow_style=False)
        yml_file.write(data)


def trun_from_file(fpath):
    """Returns trun from the given fpath"""

    with open(fpath, 'r') as yml_file:
        return yaml.load(yml_file)


def trun_emph(trun):
    """Print essential info on"""

    if trun["args"]["verbose"] > 1:               # Print environment variables
        cij.emph("rnr:ENVIRONMENT VARIABLES {")
        for evar in sorted(trun["evars"].keys()):
            cij.emph("  % 20s: %r" % ("CIJ_%s" % evar, trun["evars"][evar]))
        cij.emph("}")

    if trun["args"]["verbose"] > 1:               # Print command-line arguments
        cij.emph("rnr:COMMAND-LINE ARGUMENTS {")
        for arg in sorted(trun["args"].keys()):
            cij.emph("  % 16s: %r" % (arg, trun["args"][arg]))
        cij.emph("}")

    if trun["args"]["verbose"] > 1:
        cij.emph("rnr:HOOKS {")
        for arg in sorted(trun["hooks"]):
            cij.emph("  % 8s: %r" % (arg, trun["hooks"][arg]))
        cij.emph("}")

    if trun["args"]["verbose"]:
        cij.emph("rnr:INFO {")
        cij.emph("  output: %r" % trun["args"]["output"])
        cij.emph("  yml_fpath: %r" % yml_fpath(trun["args"]["output"]))
        cij.emph("}")


def tcase_setup(args, evars, tsuite, tcase_fpath):
    """
    @returns a testcase for the given tcase_fpath

    """
    #pylint: disable=locally-disabled, unused-argument

    if not os.path.exists(tcase_fpath):
        cij.err("rnr:tcase_setup: !tcase_fpath: %r" % tcase_fpath)
        return None

    tcase_fname = os.path.basename(tcase_fpath)
    tcase_name = os.path.splitext(tcase_fname)[0]

    tcase_res_root = os.sep.join([args.output, tsuite["name"], tcase_fname])
    tcase_aux_root = os.sep.join([tcase_res_root, "_aux"])
    tcase_log_fpath = os.sep.join([tcase_res_root, "run.log"])

    return {
        "id": "/".join([tsuite["name"], tcase_fpath]),
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


def tsuite_exit(args, evars, trun, tsuite):
    """Triggers when exiting the given testsuite"""

    if args.verbose:
        cij.emph("rnr:tsuite:exit")

    err = 0
    for hook_fpath in reversed(tsuite["hooks"]["exit"]):      # EXIT-hooks
        err, _, _, _ = hook_run(args, evars, hook_fpath, tsuite["res_root"])
        if err:
            break

    if args.verbose:
        cij.emph("rnr:tsuite:exit { err: %r }" % err, err)

    return err


def tsuite_enter(args, evars, trun, tsuite):
    """Triggers when entering the given testsuite"""

    if args.verbose:
        cij.emph("rnr:tsuite:enter { name: %r }" % tsuite["name"])

    os.makedirs(tsuite["res_root"])                         # Create DIRS
    os.makedirs(tsuite["aux_root"])

    err = 0
    for hook_fpath in tsuite["hooks"]["enter"]:     # ENTER-hooks
        err, _, _, _ = hook_run(args, evars, hook_fpath, tsuite["res_root"])
        if err:
            break

    if args.verbose:
        cij.emph("rnr:tsuite:enter { err: %r }" % err, err)

    return err


def tsuite_setup(args, evars, tplan_tsuite):
    """
    @returns a list of testcases from tcases_dpath that are in the given
    testsuite (tsuite_fpath)
    """

    tsuite_name = tplan_tsuite["name"]
    tsuite_fname = "%s.suite" % tsuite_name
    tsuite_fpath = os.sep.join([evars["TESTSUITES"], tsuite_fname])

    tsuite_res_root = os.sep.join([args.output, tsuite_name])
    tsuite_aux_root = os.sep.join([tsuite_res_root, "_aux"])
    tsuite_log_fpath = os.sep.join([tsuite_res_root, "run.log"])

    tsuite = {
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

        "id": tsuite_fname,
        "fpath": tsuite_fpath,
        "fname": tsuite_fname,
        "res_root": tsuite_res_root,
        "aux_root": tsuite_aux_root,
        "aux_list": [],
        "log_fpath": tsuite_log_fpath,
        "testcases": [],

        "status": "UNKN",
        "wallc": None,
    }

    # Setup hooks
    tsuite["hooks"] = hook_setup(evars, tplan_tsuite.get("hooks"))
    tsuite["hooks_pr_tcase"] = hook_setup(evars, tplan_tsuite.get("hooks_pr_tcase"))

    # Filter testcases, remove those that have been commented out with "#"
    tsuite_lines = (l.strip() for l in open(tsuite_fpath).read().splitlines())
    tsuite_tcase_line = (l for l in tsuite_lines if len(l) > 1 and l[0] != "#")

    # Add the tcases by their fname
    for tcase_fname in tsuite_tcase_line:
        tcase_fpath = os.sep.join([evars["TESTCASES"], tcase_fname])

        tcase = tcase_setup(args, evars, tsuite, tcase_fpath)
        if not tcase:
            cij.err("rnr:tsuite:  SETUP: FAILED")
            return None

        tsuite["testcases"].append(tcase)

    return tsuite


def tcase_exit(args, evars, trun, tsuite, tcase):
    """..."""
    #pylint: disable=locally-disabled, unused-argument

    if args.verbose:
        cij.emph("rnr:tcase:exit { fname: %r }" % tcase["fname"])

    err = 0
    for hook_fpath in reversed(tsuite["hooks_pr_tcase"]["exit"]):     # tcase EXIT-hooks
        err, _, _, _ = hook_run(args, evars, hook_fpath, tcase["res_root"])
        if err:
            break

    if args.verbose:
        cij.emph("rnr:tcase:exit { err: %r }" % err, err)

    return err


def tcase_enter(args, evars, trun, tsuite, tcase):
    """
    setup res_root and aux_root, log info and run tcase-enter-hooks

    @returns 0 when all hooks succeed, some value othervise
    """
    #pylint: disable=locally-disabled, unused-argument

    os.makedirs(tcase["res_root"])                          # Create output dirs
    os.makedirs(tcase["aux_root"])

    if args.verbose:
        cij.emph("rnr:tcase:enter")
        cij.emph("rnr:tcase:enter { fname: %r }" % tcase["fname"])
        cij.emph("rnr:tcase:enter { log_fpath: %r }" % tcase["log_fpath"])

    err = 0
    for hook_fpath in tsuite["hooks_pr_tcase"]["enter"]:    # tcase ENTER-hooks
        err, _, _, _ = hook_run(args, evars, hook_fpath, tcase["res_root"])
        if err:
            break

    if args.verbose:
        cij.emph("rnr:tcase:exit: { err: %r }" % err, err)

    return err


def tcase_run(args, evars, trun, tsuite, tcase):
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
            'source cijoe.sh && '
            'source %s && '
            'CIJ_TEST_RES_ROOT="%s" %s %s' % (
                args.env_fpath, tcase["res_root"], launch, tcase["fpath"]
            )
        ]
        if args.verbose > 1:
            cij.emph("rnr:tcase:run { cmd: %r }" % " ".join(cmd))

        process = Popen(
            cmd,
            stdout=log_fd,
            stderr=STDOUT,
            cwd=trun["evars"]["MODULES"]
        )
        process.wait()

        tcase["rcode"] = process.returncode
        tcase["wallc"] = time.time() - bgn

    if args.verbose:
        cij.emph("rnr:tcase:run { wallc: %02f }" % tcase["wallc"])
        cij.emph("rnr:tcase:run { rcode: %r }" % tcase["rcode"], tcase["rcode"])

    return tcase["rcode"]


def trun_exit(args, evars, trun):
    """Triggers when exiting the given testrun"""

    if args.verbose:
        cij.emph("rnr:trun:exit")

    err = 0
    for hook_fpath in reversed(trun["hooks"]["exit"]):    # EXIT-hooks
        err, _, _, _ = hook_run(args, evars, hook_fpath, args.output)
        if err:
            break

    if args.verbose:
        cij.emph("rnr:trun::exit { err: %r }" % err, err)

    return err


def trun_enter(args, evars, trun):
    """Triggers when entering the given testrun"""

    if args.verbose:
        cij.emph("rnr:trun::enter")

    trun_aux_root = os.sep.join([args.output, "_aux"])      # Create AUX
    os.makedirs(trun_aux_root)

    trun["stamp"]["begin"] = int(time.time())     # Record start timestamp

    err = 0
    for hook_fpath in trun["hooks"]["enter"]:     # ENTER-hooks
        err, _, _, _ = hook_run(args, evars, hook_fpath, args.output)
        if err:
            break

    if args.verbose:
        cij.emph("rnr:trun::enter { err: %r }" % err, err)

    return err


def trun_setup(args, evars):
    """Setup the testrunner data-structure"""

    tplan = None

    try:
        with open(args.testplan_fpath) as tplan_fd:
            tplan = yaml.load(tplan_fd)
    except AttributeError as exc:
        cij.err("rnr: %r" % exc)

    if not tplan:
        return None

    trun = {
        "evars": {e: evars[e] for e in evars.keys()},
        "args": {a: getattr(args, a) for a in vars(args)},
        "progress": {
            "PASS": 0, "FAIL": 0, "UNKN": 0
        },
        "stamp": {"begin": None, "end": None},
        "hooks": {
            "enter": [],
            "exit": []
        },
        "aux_root": os.sep.join([args.output, "_aux"]),
        "aux_list": [],
        "log_fpath": os.sep.join([args.output, "run.log"]),

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
    trun["hooks"] = hook_setup(evars, hooks)

    for tplan_tsuite in tplan["testsuites"]:        # Setup testsuites
        tsuite = tsuite_setup(args, evars, tplan_tsuite)
        if not tsuite:
            cij.err("main::FAILED: setting up tsuite: %r" % tsuite)
            return 1

        trun["testsuites"].append(tsuite)
        trun["progress"]["UNKN"] += len(tsuite["testcases"])

    return trun


def main(args, evars):
    """CIJ Test Runner main entry point"""

    fpath = yml_fpath(args.output)  # YAML exists, we exit, it might be RUNNING!
    if os.path.exists(fpath):
        cij.err("main:FAILED { fpath: %r }, exists" % fpath)
        return 1

    trun = trun_setup(args, evars)                  # Setup trun
    if not trun:
        return 1

    trun_to_file(trun)                              # Persist trun
    trun_emph(trun)                                 # Print trun before run

    tr_err = 0
    tr_ent_err = trun_enter(args, evars, trun)
    for tsuite in (ts for ts in trun["testsuites"] if not tr_ent_err):

        ts_err = 0
        ts_ent_err = tsuite_enter(args, evars, trun, tsuite)
        for tcase in (tc for tc in tsuite["testcases"] if not ts_ent_err):

            tc_err = tcase_enter(args, evars, trun, tsuite, tcase)
            if not tc_err:
                tc_err += tcase_run(args, evars, trun, tsuite, tcase)
                tc_err += tcase_exit(args, evars, trun, tsuite, tcase)

            tcase["status"] = "FAIL" if tc_err else "PASS"

            trun["progress"][tcase["status"]] += 1  # Update progress
            trun["progress"]["UNKN"] -= 1

            ts_err += tc_err                        # Accumulate errors

            trun_to_file(trun)                      # Persist trun

        if not ts_ent_err:
            ts_err += tsuite_exit(args, evars, trun, tsuite)

        ts_err += ts_ent_err                        # Accumulate errors
        tr_err += ts_err

        tsuite["status"] = "FAIL" if ts_err else "PASS"

        cij.emph("rnr:tsuite %r" % tsuite["status"], tsuite["status"] != "PASS")

    if not tr_ent_err:
        trun_exit(args, evars, trun)

    tr_err += tr_ent_err
    trun["status"] = "FAIL" if tr_err else "PASS"

    trun["stamp"]["end"] = int(time.time()) + 1         # END STAMP
    trun_to_file(trun)                                  # PERSIST

    cij.emph("rnr:main:progress %r" % trun["progress"])
    cij.emph("rnr:main:trun %r" % trun["status"], trun["status"] != "PASS")

    return trun["progress"]["UNKN"] + trun["progress"]["FAIL"]
