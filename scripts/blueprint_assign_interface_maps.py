# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
from aos.client import AosClient
from scripts.utils import deserialize_fixture
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


# Get Blueprint System Nodes
bp_nodes = aos.blueprint.get_bp_system_nodes(bp.id)


# Define IM mapping
im_assignment = {
    "spine1": "Cumulus_VX__slicer-7x10-1",
    "spine2": "Cumulus_VX__slicer-7x10-1",
    "evpn_mlag_001_leaf1": "Cumulus_VX__slicer-7x10-1",
    "evpn_mlag_001_leaf2": "Cumulus_VX__slicer-7x10-1",
    "evpn_single_001_leaf1": "Arista_vEOS__slicer-7x10-1",
}


# Map Node to System ID
assignment = dict()
for device, im in im_assignment.items():
    for value in bp_nodes.values():
        if value["label"] == device:
            assignment[value["id"]] = im


# Assign Interface Maps to Nodes
data = {"assignments": assignment}
aos.blueprint.assign_interface_maps_raw(bp_id=bp.id, assignments=data)


# Bulk Assign Interface Maps
# Finds all system nodes in blueprint and assigns them the given IM
sys_nodes = ["spine1", "spine2", "leaf1"]
aos.blueprint.assign_interface_map_by_name(
    bp.id, node_names=sys_nodes, im_name="Arista_vEOS__slicer-7x10-1"
)
