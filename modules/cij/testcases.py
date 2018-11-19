#!/usr/bin/env python
"""
    Library functions for cij_testcases
"""
import os
import datetime
import ansi2html
import jinja2
import cij.reporter
import cij

EXTS = {
    "TESTPLANS": [".plan"],
    "TESTSUITES": [".suite"],
    "TESTCASES": [".py", ".sh"],
}


def index(search_path, ext=None):
    """@returns a set of testcases in the given search_path"""

    if ext is None:
        ext = "TCASE"

    tcases = set([])
    for _, _, files in os.walk(search_path):
        for tc_fname in files:
            if os.path.splitext(tc_fname)[-1] in EXTS[ext]:
                tcases.add(tc_fname)

    return sorted(list(tcases))


def construct_dset(args, evars):
    """
    """

    fnames = index(evars["TESTCASES"], "TESTCASES")

    dset = {
        "group_names": [],
    }

    for fname in fnames:
        group = fname.split("_")[0]
        if group not in dset:
            dset[group] = []
            dset["group_names"].append(group)

        fpath = os.sep.join([evars["TESTCASES"], fname])

        tcase = {
            "fpath": fpath,
            "name": fname,
            "fname": fname,
            "descr": "",
            "descr_long": "",
            "src_content": open(fpath, "r").read()
        }

        descr, descr_long = cij.reporter.tcase_parse_descr(tcase)

        tcase["descr"] = descr
        tcase["descr_long"] = descr_long

        dset[group].append(tcase)

    return dset


def dset_to_html(dset, tmpl_fpath):
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

    return tmpl.render(dset=dset)


def main(args, evars):
    """
    Search for testcases, parse their descriptions and write them to report
    """

    html_fpath = os.sep.join([args.output, "testcases.html"])

    cij.emph("html_fpath: %r" % html_fpath)

    dset = construct_dset(args, evars)

    with open(html_fpath, 'w') as html_fd:
        html = dset_to_html(dset, args.tmpl_fpath)
        html_fd.write(html)

    return 0
