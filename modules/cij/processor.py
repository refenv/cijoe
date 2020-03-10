#!/usr/bin/env python
"""
    Library functions for cij_processor
"""
import datetime
import glob
import os
import jinja2
import cij.runner
import cij
import re
import json

def file_get_contents(filename):
    with open(filename) as f:
        return f.read()

def parse(name, filter_path):
    log = file_get_contents(name)
    matched = 0
    results = {}

    for root, dirs, files in os.walk(filter_path, topdown=False):
        for filter_name in files:
            filter = re.compile(
                file_get_contents(os.path.join(root, filter_name)).replace("\n", ""),
                re.DOTALL
            )
            matches = filter.finditer(log)
            if not matches: continue;
            matched = 1

            for count,match in enumerate(matches):
                id = match.group("id")
                if id not in results:
                    results[id] = []

                results[id].append(match.groupdict())

    if not matched: return

    with open(name + '.json', 'w') as json_file:
        json.dump(results, json_file)

def main(args):
    """Main entry point"""

    for root, dirs, files in os.walk(args.output, topdown=False):
        for name in files:
            if not name.endswith("run.log"): continue
            parse(os.path.join(root, name), args.filters)

    return 0
