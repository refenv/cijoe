#!/usr/bin/env python
"""
    Library functions for cij_reporter
"""
import datetime
import glob
import os
import ansi2html
import jinja2
import cij.runner
import cij


def extract_hook_names(ent):
    """Extract hook names from the given entity"""

    hnames = []
    for hook in ent["hooks"]["enter"] + ent["hooks"]["exit"]:
        hname = os.path.basename(hook["fpath_orig"])
        hname = os.path.splitext(hname)[0]
        hname = hname.strip()
        hname = hname.replace("_enter", "")
        hname = hname.replace("_exit", "")
        if hname in hnames:
            continue

        hnames.append(hname)

    hnames.sort()

    return hnames


def tcase_comment(tcase):
    """
    Extract testcase comment section / testcase description

    @returns the testcase-comment from the tcase["fpath"] as a list of strings
    """

    src = open(tcase["fpath"]).read()
    if len(src) < 3:
        cij.err("rprtr::tcase_comment: invalid src, tcase: %r" % tcase["name"])
        return None

    ext = os.path.splitext(tcase["fpath"])[-1]
    if ext not in [".sh", ".py"]:
        cij.err("rprtr::tcase_comment: invalid ext: %r, tcase: %r" % (
            ext, tcase["name"]
        ))
        return None

    comment = []
    for line in src.splitlines()[2:]:
        if ext == ".sh" and not line.startswith("#"):
            break
        elif ext == ".py" and not '"""' in line:
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

    comment = [l for l in comment if l.strip()]     # Remove empty lines

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
    Returns content of the given 'fpath' with HTML annotations, currently simply
    a conversion of ANSI color codes to HTML elements
    """

    if not os.path.isdir(run_root):
        return "CANNOT_LOCATE_LOGFILES"

    hook_enter = []
    hook_exit = []
    tcase = []
    for fpath in glob.glob(os.sep.join([run_root, "*.log"])):
        if "exit" in fpath:
            hook_exit.append(fpath)
            continue

        if "hook" in fpath:
            hook_enter.append(fpath)
            continue

        tcase.append(fpath)

    content = ""
    for fpath in hook_enter + tcase + hook_exit:
        content += "# BEGIN: run-log from log_fpath: %s\n" % fpath
        content += open(fpath, "r").read()
        content += "# END: run-log from log_fpath: %s\n\n" % fpath

    return content


def src_to_html(fpath):
    """
    Returns content of the given 'fpath' with HTML annotations for syntax
    highlighting
    """

    if not os.path.exists(fpath):
        return "COULD-NOT-FIND-TESTCASE-SRC-AT-FPATH:%r" % fpath

    # NOTE: Do SYNTAX highlight?

    return open(fpath, "r").read()


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

    tsuite["log_content"] = runlogs_to_html(tsuite["res_root"])
    tsuite["aux_list"] = aux_listing(tsuite["aux_root"])
    tsuite["hnames"] = extract_hook_names(tsuite)

    return True


def process_tcase(tcase):
    """Goes through the trun and processes "run.log" """

    tcase["src_content"] = src_to_html(tcase["fpath"])
    tcase["log_content"] = runlogs_to_html(tcase["res_root"])
    tcase["aux_list"] = aux_listing(tcase["aux_root"])
    tcase["descr_short"], tcase["descr_long"] = tcase_parse_descr(tcase)
    tcase["hnames"] = extract_hook_names(tcase)

    return True


def process_trun(trun):
    """Goes through the trun and processes "run.log" """

    trun["log_content"] = runlogs_to_html(trun["res_root"])
    trun["aux_list"] = aux_listing(trun["aux_root"])
    trun["hnames"] = extract_hook_names(trun)

    return True


def postprocess(trun):
    """Perform postprocessing of the given test run"""

    plog = []
    plog.append(("trun", process_trun(trun)))

    for tsuite in trun["testsuites"]:
        plog.append(("tsuite", process_tsuite(tsuite)))

        for tcase in tsuite["testcases"]:
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

    def ansi_to_html(ansi):
        """Convert the given ANSI text to HTML"""

        conv = ansi2html.Ansi2HTMLConverter(
            scheme="solarized",
            inline=True
        )
        html = conv.convert(ansi, full=False)

        with open("/tmp/jazz.html", "w") as html_file:
            html_file.write(html)

        return html

    tmpl_dpath = os.path.dirname(tmpl_fpath)
    tmpl_fname = os.path.basename(tmpl_fpath)

    env = jinja2.Environment(
        autoescape=True,
        loader=jinja2.FileSystemLoader(tmpl_dpath)
    )
    env.filters['stamp_to_datetime'] = stamp_to_datetime
    env.filters['strftime'] = strftime
    env.filters['ansi_to_html'] = ansi_to_html

    tmpl = env.get_template(tmpl_fname)

    return tmpl.render(dset=dset)


def rehome(old, new, struct):
    """
    Replace all absolute paths to "re-home" it
    """

    if old == new:
        return

    if isinstance(struct, list):
        for item in struct:
            rehome(old, new, item)
    elif isinstance(struct, dict):
        for key, val in struct.iteritems():
            if isinstance(val, (dict, list)):
                rehome(old, new, val)
            elif "conf" in key:
                continue
            elif "orig" in key:
                continue
            elif "root" in key or "path" in key:
                struct[key] = struct[key].replace(old, new)


def main(args):
    """Main entry point"""

    trun = cij.runner.trun_from_file(args.trun_fpath)

    rehome(trun["conf"]["OUTPUT"], args.output, trun)

    postprocess(trun)

    cij.emph("main: reports are uses tmpl_fpath: %r" % args.tmpl_fpath)
    cij.emph("main: reports are here args.output: %r" % args.output)

    html_fpath = os.sep.join([args.output, "%s.html" % args.tmpl_name])
    cij.emph("html_fpath: %r" % html_fpath)
    try:                                    # Create and store HTML report
        with open(html_fpath, 'w') as html_file:
            html_file.write(dset_to_html(trun, args.tmpl_fpath))
    except (IOError, OSError, ValueError) as exc:
        import traceback
        traceback.print_exc()
        cij.err("rprtr:main: exc: %s" % exc)
        return 1

    return 0
