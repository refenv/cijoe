"""
example of using templates
==========================

An example of how to use a template from the cijoe resources. 

The script renders a Jinja template with filename `template.html.jinja2` that
takes `name` as a parameter, and creates a new html file from the template 
where all instances of "{{ name }}" has been replaced with the initiator's 
hostname.

"""

from argparse import Namespace

import jinja2

from cijoe.core.command import Cijoe
from cijoe.core.resources import get_resources


def main(args: Namespace, cijoe: Cijoe):
    resources = get_resources()
    template_path = resources["templates"]["template.html"].path

    jinja_env = jinja2.Environment(
        autoescape=True, loader=jinja2.FileSystemLoader(template_path.parent)
    )
    template = jinja_env.get_template(template_path.name)

    err, state = cijoe.run_local("hostname")
    if err:
        return err

    hostname = state.output().strip()

    with open("hello.html", "a") as file:
        html = template.render({"name": hostname})
        file.write(html)

    return 0
