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


# Find Blueprint by Name
bp_name = "apstra-pod1"
bp = aos.blueprint.get_id_by_name(label=bp_name)


# Define rack nodes for Virtual-Network association
# In this case its all nodes with role "leaf"
bound_to = list()
tor_nodes = aos.blueprint.get_all_tor_nodes(bp.id)

for node in tor_nodes:
    bound_to.append({"system_id": node["id"]})


# Create Virtual-Network
# tagged_ct will also create a tagged Connectivity-Template for this
# virtual-network.
aos.blueprint.create_virtual_network(
    bp_id=bp.id,
    name="vn101",
    bound_to=bound_to,
    sz_name="Finance",
    ipv4_subnet="10.10.100.0/24",
    ipv4_gateway="10.10.100.1",
    tagged_ct=True,
)

# Get Virtual-Network details by name
vn = aos.blueprint.find_vn_by_name(bp.id, name="vn101")
