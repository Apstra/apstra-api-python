# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import json

from aos.client import AosClient
from scripts.utils import deserialize_fixture, render_jinja_template
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# You will need to update the connection details below with your
# specific AOS instance
AOS_IP = "<aos-IP>"
AOS_PORT = 443
AOS_USER = "admin"
AOS_PW = "aos-aos"

# Login
aos = AosClient(protocol="https", host=AOS_IP, port=AOS_PORT)
aos.auth.login(AOS_USER, AOS_PW)


# Find Blueprint and Default Routing-Zone by Name
bp_name = "apstra-pod1"
bp = aos.blueprint.get_id_by_name(label=bp_name)
default_rz = aos.blueprint.find_sz_by_name(bp.id, "default")
ct_id = "external-router-peering"

# Create Connectivity-Template
context = {"default_rz_id": default_rz.id}
ct_template = "ext_rtr_ct_default.jinja"

ext_rtr_ct = json.loads(render_jinja_template(ct_template, context))

aos.blueprint.create_connectivity_template_from_json(bp.id, data=ext_rtr_ct)


# Assign interfaces to CT
ct_intfs = aos.blueprint.get_endpoint_policy_app_points(bp.id, ct_id)

rlink_interfaces = list()


# here we assume the external generic system interfaces were tagged
# with "Router". The below logic uses this tag to identify the interfaces
# to assign.
def find_tags(d, intf, tag):
    for child in d:
        if child["children_count"] == 0 and child["tags"] == [tag]:
            intf.append(child["id"])
        find_tags(child["children"], intf, tag)
    return intf


find_tags(ct_intfs["application_points"]["children"], rlink_interfaces, "Router")

data = {"application_points": []}
for intf_id in rlink_interfaces:
    data["application_points"].append(
        {
            "id": intf_id,
            "policies": [{"policy": "external-router-peering", "used": True}],
        }
    )


# Create the Connectivity-Template
aos.blueprint.update_connectivity_template(bp.id, data)
