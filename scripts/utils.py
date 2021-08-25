# Copyright 2019-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula

import json
import pkg_resources
from jinja2 import PackageLoader, Environment


def fixtures_path(path):
    return pkg_resources.resource_filename("scripts", f"templates/{path}")


def deserialize_fixture(path):
    if not path.endswith(".json"):
        path += ".json"
    with open(fixtures_path(path), "r") as fp:
        return json.load(fp)


def read_fixture(path):
    with open(fixtures_path(path), "r") as fp:
        return fp.read()


def render_jinja_template(template: str, context: dict) -> str:
    file_loader = PackageLoader("scripts", "templates")
    env = Environment(
        loader=file_loader, autoescape=True, lstrip_blocks=True, trim_blocks=True
    )
    template = env.get_template(template)

    return template.render(context)
