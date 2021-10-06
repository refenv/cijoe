#!/usr/bin/env python3
"""
    Library functions for cij_reporter
"""
import datetime
import traceback
import glob
import os
import jinja2
import cij.runner
import cij
from cij.util import rehome


def tcase_comment(tcase):
    """
    Extract testcase comment section / testcase description

    @returns the testcase-comment from the tcase.fpath as a list of strings
    """

    src = ""
    with open(tcase.fpath, encoding="UTF-8") as tcase_f:
        src = tcase_f.read()

    if len(src) < 3:
        cij.err("rprtr::tcase_comment: invalid src, tcase: %r" % tcase.name)
        return None

    ext = os.path.splitext(tcase.fpath)[-1]
    if ext not in [".sh", ".py"]:
        cij.err("rprtr::tcase_comment: invalid ext: %r, tcase: %r" % (
            ext, tcase.name
        ))
        return None

    comment = []
    for line in src.splitlines()[2:]:
        if ext == ".sh" and not line.startswith("#"):
            break
        if ext == ".py" and '"""' not in line:
            break

        comment.append(line)

    return comment


def tcase_parse_descr(tcase):
    """Parse descriptions from the the given tcase"""

    descr_short = "SHORT"
    descr_long = "LONG"

    try:
        comment = tcase_comment(tcase)
    except (IOError, OSError, ValueError) as exc:
        comment = []
        cij.err("tcase_parse_descr: failed: %r, tcase: %r" % (exc, tcase))

    # Remove empty lines
    comment = [line for line in comment if line.strip()]
    for line_number, line in enumerate(comment):
        if line.startswith("#"):
            comment[line_number] = line[1:]

    if comment:
        descr_short = comment[0]

    if len(comment) > 1:
        descr_long = "\n".join(comment[1:])

    return descr_short, descr_long


def runlogs_to_html(run_root):
    """
    Returns content of the given 'fpath' with HTML annotations, currently
    simply a conversion of ANSI color codes to HTML elements
    """

    if not os.path.isdir(run_root):
        return "CANNOT_LOCATE_LOGFILES"

    hook_enter = []
    hook_exit = []
    tcase = []
    for fpath in glob.glob(os.path.join(run_root, "*.log")):
        if "exit" in fpath:
            hook_exit.append(fpath)
            continue

        if "hook" in fpath:
            hook_enter.append(fpath)
            continue

        tcase.append(fpath)

    content = ""
    for fpath in hook_enter + tcase + hook_exit:
        with open(fpath, "r", encoding="UTF-8") as logf:
            content += "# BEGIN: run-log from log_fpath: %s\n" % fpath
            content += logf.read()
            content += "# END: run-log from log_fpath: %s\n\n" % fpath

    return content


def analysislog_to_html(fpath):
    """
    Returns contents of the given 'fpath' with HTML annotations, currently
    simply a conversion of ANSI color codes to HTML elements
    """

    if not os.path.exists(fpath):
        return "CANNOT_LOCATE_ANALYSIS_LOGFILES"

    content = ""
    with open(fpath, "r", encoding="UTF-8") as logf:
        content += f"# BEGIN: analysis-log from log_fpath: {fpath}\n"
        content += logf.read()
        content += f"# END: analysis-log from log_fpath: {fpath}\n\n"
    return content


def src_to_html(fpath):
    """
    Returns content of the given 'fpath' with HTML annotations for syntax
    highlighting
    """

    if not os.path.exists(fpath):
        return "COULD-NOT-FIND-TESTCASE-SRC-AT-FPATH:%r" % fpath

    # NOTE: Do SYNTAX highlight?

    with open(fpath, "r", encoding="UTF-8") as fpath_file:
        return fpath_file.read()


def aux_listing(aux_root):
    """Listing"""

    listing = []

    for root, _, fnames in os.walk(aux_root):
        count = len(aux_root.split(os.sep))
        prefix = root.split(os.sep)[count:]

        for fname in fnames:
            listing.append(os.sep.join(prefix + [fname]))

    return listing


def process_tsuite(tsuite):
    """Goes through the tsuite and processes "*.log" """

    # scoop of output from all run-logs

    tsuite.log_content = runlogs_to_html(tsuite.res_root)
    tsuite.aux_list = aux_listing(tsuite.aux_root)

    return True


def process_tcase(tcase):
    """Goes through the trun and processes "run.log" """

    tcase.src_content = src_to_html(tcase.fpath)
    tcase.log_content = runlogs_to_html(tcase.res_root)
    tcase.analysis_content = analysislog_to_html(tcase.analysis_log_fpath)
    tcase.aux_list = aux_listing(tcase.aux_root)
    tcase.descr, tcase.descr_long = tcase_parse_descr(tcase)

    return True


def process_tplan(tplan):
    """Goes through the tplan and processes "run.log" """

    tplan.log_content = runlogs_to_html(tplan.res_root)
    tplan.aux_list = aux_listing(tplan.aux_root)

    return True


def process_trun(trun):
    """Goes through the trun and processes "run.log" """

    trun.log_content = runlogs_to_html(trun.res_root)
    trun.aux_list = aux_listing(trun.aux_root)

    return True


def postprocess(trun):
    """Perform postprocessing of the given test run"""

    plog = []
    plog.append(("trun", process_trun(trun)))

    for tplan in trun.testplans:
        plog.append(("tplan", process_tplan(tplan)))

        for tsuite in tplan.testsuites:
            plog.append(("tsuite", process_tsuite(tsuite)))

            for tcase in tsuite.testcases:
                plog.append(("tcase", process_tcase(tcase)))

    for task, success in plog:
        if not success:
            cij.err("rprtr::postprocess: FAILED for %r" % task)

    return sum((success for task, success in plog))


def dset_to_html(dset, tmpl_fpath):
    """
    @returns A HTML representation of the given 'dset' using the template at
    'tmpl_fpath'
    """

    def stamp_to_datetime(stamp):
        """Create a date object from timestamp"""

        return datetime.datetime.fromtimestamp(int(stamp))

    def strftime(dtime, fmt):
        """Create a date object from timestamp"""

        return dtime.strftime(fmt)

    tmpl_dpath = os.path.dirname(tmpl_fpath)
    tmpl_fname = os.path.basename(tmpl_fpath)

    env = jinja2.Environment(
        autoescape=True,
        loader=jinja2.FileSystemLoader(tmpl_dpath)
    )
    env.filters['stamp_to_datetime'] = stamp_to_datetime
    env.filters['strftime'] = strftime

    tmpl = env.get_template(tmpl_fname)

    return tmpl.render(dset=dset)


def main(args):
    """Main entry point"""

    trun = cij.runner.trun_from_file(args.trun_fpath)

    # pylint: disable=no-member
    rehome(trun.args.output, args.output, trun)

    postprocess(trun)

    cij.emph("main: reports are uses tmpl_fpath: %r" % args.tmpl_fpath)
    cij.emph("main: reports are here args.output: %r" % args.output)

    _, ext = os.path.splitext(args.tmpl_fpath)

    html_fpath = os.path.join(args.output, "".join([args.tmpl_name, ext]))
    cij.emph("html_fpath: %r" % html_fpath)
    try:                                    # Create and store HTML report
        with open(html_fpath, 'w', encoding="UTF-8") as html_file:
            html_file.write(dset_to_html(trun, args.tmpl_fpath))
    except (IOError, OSError, ValueError) as exc:
        traceback.print_exc()
        cij.err("rprtr:main: exc: %s" % exc)
        return 1

    return 0
