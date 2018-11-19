#!/usr/bin/env python
"""
    Library functions for cij_reporter
"""
from subprocess import Popen, PIPE
import datetime
import os
import jinja2
import ansi2html
import cij.runner
import cij


def tcase_comment(tcase):
    """
    @returns the testcase-comment from the tcase["fpath"] as a list of strings
    """

    comment = []

    ext = os.path.splitext(tcase["fpath"])[-1]
    src = open(tcase["fpath"]).read()

    if len(src) < 3:
        cij.err("rprtr::tcase_comment: invalid src, tcase: %r" % tcase["name"])
        return None

    if ext not in [".sh", ".py"]:
        cij.err("rprtr::tcase_comment: invalid ext: %r, tcase: %r" % (
            ext, tcase["name"]
        ))
        return None

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
    except Exception as exc:
        comment = []
        cij.err("tcase_comment: failed: %r, tcase: %r" % (exc, tcase))

    comment = [l for l in comment if l.strip()]     # Remove empty lines

    for line_number, line in enumerate(comment):
        if line.startswith("#"):
            comment[line_number] = line[1:]

    if comment:
        descr_short = comment[0]

    if len(comment) > 1:
        descr_long = "\n".join(comment[1:])

    return descr_short, descr_long


def runlog_to_html(trun, fpath):
    """
    Returns content of the given 'fpath' with HTML annotations, currently simply
    a conversion of ANSI color codes to HTML elements
    """

    if not os.path.exists(fpath):
        return "LOG-DOES-NOT-EXIST"

    # TODO: Do ANSI color conversion ?

    return open(fpath, "r").read()


def src_to_html(trun, fpath):
    """
    Returns content of the given 'fpath' with HTML annotations for syntax
    highlighting
    """

    if not os.path.exists(fpath):
        return "COULD-NOT-FIND-TESTCASE-SRC-AT-FPATH:%r" % fpath

    # TODO: Do SYNTAX highlight?

    return open(fpath, "r").read()


def aux_listing(trun, aux_root):
    """Listing"""

    listing = []

    for root, _, fnames in os.walk(aux_root):
        count = len(aux_root.split(os.sep))
        prefix = root.split(os.sep)[count:]

        for fname in fnames:
            listing.append(os.sep.join(prefix + [fname]))

    return listing


def process_tsuite(trun, tsuite):
    """Goes through the trun and processes "run.log" """

    tsuite["log_content"] = runlog_to_html(trun, tsuite["log_fpath"])
    tsuite["aux_list"] = aux_listing(trun, tsuite["aux_root"])

    return True


def process_tcase(trun, tsuite, tcase):
    """Goes through the trun and processes "run.log" """

    def tcase_src_to_html(trun, runlog_fpath):
        """Convert the runlog in the given bath to annotated HTML"""

        return ""

    tcase["src_content"] = src_to_html(trun, tcase["fpath"])
    tcase["log_content"] = runlog_to_html(trun, tcase["log_fpath"])
    tcase["aux_list"] = aux_listing(trun, tcase["aux_root"])

    tcase["descr_short"], tcase["descr_long"] = tcase_parse_descr(tcase)

    return True


def process_trun(trun):
    """Goes through the trun and processes "run.log" """

    trun["log_content"] = runlog_to_html(trun, trun["log_fpath"])
    trun["aux_list"] = aux_listing(trun, trun["aux_root"])

    return True


def postprocess(trun):
    """Perform postprocessing of the given test run"""

    plog = []

    plog.append(("trun", process_trun(trun)))

    for tsuite in trun["testsuites"]:
        plog.append(("tsuite", process_tsuite(trun, tsuite)))

        for tcase in tsuite["testcases"]:
            plog.append(("tcase", process_tcase(trun, tsuite, tcase)))

    for task, success in plog:
        if not success:
            cij.err("rprtr::postprocess: FAILED for %r" % task)

    return sum((success for task, success in plog))


def trun_to_html(trun, tmpl_fpath):
    """
    @returns A HTML representation of the given 'trun' using the template at
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

    return tmpl.render(trun=trun)


def html_to_pdf(args, html_fpath):
    """..."""

    # Convert HTML html to PDF
    pdf_fpath = os.sep.join([args.output, "%s.pdf" % args.tmpl_name])
    cij.emph("pdf_fpath: %r" % pdf_fpath)

    out, err, rcode = ("", "have you installed 'wkhtmltopdf'?", 1)
    try:
        cmd = ["wkhtmltopdf", "--page-size", "A4", html_fpath, pdf_fpath]
        process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        out, err = process.communicate()
        rcode = process.returncode
    except Exception as exc:
        cij.warn("exc: %r" % exc)

    if rcode:
        cij.warn("out: %r, err: %r, rcode: %r" % (out, err, rcode))


def main(args, evar):
    """.."""

    trun = cij.runner.trun_from_file(args.trun_fpath)

    postprocess(trun)   # Post process the test run

    cij.emph("reports are generated in args.output: %r" % args.output)
    cij.emph("reports are generated using tmpl_fpath: %r" % args.tmpl_fpath)

    html_fpath = os.sep.join([args.output, "%s.html" % args.tmpl_name])
    cij.emph("html_fpath: %r" % html_fpath)
    try:                                    # Create and store HTML report
        with open(html_fpath, 'w') as html_file:
            html_file.write(trun_to_html(trun, args.tmpl_fpath))

    except Exception as exc:
        cij.err("exc: %r" % exc)
        return 1

    # html_to_pdf(args, html_fpath)

    return 0
