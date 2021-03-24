# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
from aos.client import AosClient
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from scripts.utils import deserialize_fixture
from aos.repeat import repeat_until

# You will need to update the connection details below with your
# specific AOS instance
AOS_IP = "<aos-IP>"
AOS_PORT = 443
AOS_USER = "admin"
AOS_PW = "aos-aos"


# labguide 1 step 2 - Blueprint

# Login
aos = AosClient(protocol="https", host=AOS_IP, port=AOS_PORT)
aos.auth.login(AOS_USER, AOS_PW)


# Create Blueprint
bp_name = "apstra-pod1"
template = aos.design.templates.get_template(temp_name="apstra")


# Blueprint id is returned when creating and we will use that throughout.
bp = aos.blueprint.add_blueprint(label=bp_name, template_id=template["id"])


# Assign Blueprint Resources
resources = deserialize_fixture("bp_resources.json")

for r in resources:
    if r["type"] == "asn":
        pool = aos.resources.asn_pools.find_by_name(r["pool"]).pop()
        aos.blueprint.apply_resource_groups(
            bp_id=bp.id,
            resource_type=r["type"],
            group_name=r["group"],
            # If you do not have the pool ID, you will need to do a lookup
            pool_ids=[pool.id],
        )
    elif r["type"] == "ip":
        pool = aos.resources.ip_pools.find_by_name(r["pool"]).pop()
        aos.blueprint.apply_resource_groups(
            bp_id=bp.id,
            resource_type=r["type"],
            group_name=r["group"],
            pool_ids=[pool.id],
        )


# Assign Blueprint InterfaceMaps
# We need the blueprint node IDs for device assignment. Note the node ID
# is not the same as the system ID you will find with
# 'aos.devices.managed_devices.get_all()'

bp_nodes = aos.blueprint.get_bp_system_nodes(bp.id)

# We also need to provide an assignment for each device based on
# the interface-map assignment. Note the key must match the
# blueprint node name exactly.
im_assignment = {
    "spine1": "Cumulus_VX__slicer-7x10-1",
    "spine2": "Cumulus_VX__slicer-7x10-1",
    "evpn_mlag_001_leaf1": "Cumulus_VX__slicer-7x10-1",
    "evpn_mlag_001_leaf2": "Cumulus_VX__slicer-7x10-1",
    "evpn_single_001_leaf1": "Arista_vEOS__slicer-7x10-1",
}

# We need to map the blueprint node ID of each system to the correct
# interface map above.
assignment = dict()
for device, im in im_assignment.items():
    for value in bp_nodes.values():
        if value["label"] == device:
            assignment[value["id"]] = im


data = {"assignments": assignment}
aos.blueprint.assign_interface_maps_raw(bp_id=bp.id, assignments=data)
# Note: there is also 'assign_interface_map_by_name' which allows you to
# bulk assign multiple device to the same interface-map.


# Assign Blueprint Devices
# We need to determine which system will be assigned to each blueprint
# node. If you set the 'location' field in each system under Devices -
# Managed Devices, you can use 'assign_all_devices_from_location'.

# We will do this the hard way and chose based on IP address.

systems = aos.devices.managed_devices.get_all()
bp_nodes = aos.blueprint.get_bp_system_nodes(bp.id)

system_list = []
node_assignment = []


def get_last_octet(ipaddr):
    return int(ipaddr.split(".")[3])

# assign location
for s in systems:
    if get_last_octet(s.management_ip) == 11:
        system_list.append({"id": s.system_id, "location": "spine1"})
    elif get_last_octet(s.management_ip) == 12:
        system_list.append({"id": s.system_id, "location": "spine2"})
    elif get_last_octet(s.management_ip) == 13:
        system_list.append({"id": s.system_id, "location": "evpn_mlag_001_leaf1"})
    elif get_last_octet(s.management_ip) == 15:
        system_list.append({"id": s.system_id, "location": "evpn_mlag_001_leaf2"})
    elif get_last_octet(s.management_ip) == 14:
        system_list.append({"id": s.system_id, "location": "evpn_single_001_leaf1"})
    else:
        print(f"{s.management_ip} unknown device")

for s in system_list:
    for v in bp_nodes.values():
        if v["label"] == s["location"]:
            node_assignment.append(
                {"system_id": s["id"], "id": v["id"], "deploy_mode": "deploy"}
            )

aos.blueprint.assign_bp_devices_from_json(bp.id, node_assignment)


# Assign Blueprint External Router
ext_rtr_name = "apstra-rtr"
ext_rtr = aos.external_systems.external_router.find_by_name(ext_rtr_name)

aos.blueprint.apply_external_router(
    bp_id=bp.id, ext_rtr_id=ext_rtr.id, connectivity_type="bond"
)

# Assign Blueprint SVI Resources for MLAG svi subnet IPs
resources = deserialize_fixture("svi_resources.json")

for r in resources:
    if r["type"] == "ip":
        pool = aos.resources.asn_pools.find_by_name(r["pool"]).pop()
        aos.blueprint.apply_resource_groups(
            bp_id=bp.id,
            resource_type=r["type"],
            group_name=r["group"],
            pool_ids=[pool.id],
        )


# Configure Default Security-Zone (VRF) with external router
# connectivity-points
sz = aos.blueprint.find_sz_by_name(bp.id, "default")
sz_cp = aos.blueprint.get_sz_connectivity_points(bp.id, sz.id).pop()

# Subnet and IP assignment for connections
sz_subnet = "10.60.60.0/24"
sz_vlan_id = 60
sz_rtr_ip = "10.60.60.254/24"
sz_leaf1_ip = "10.60.60.1/24"
sz_leaf2_ip = "10.60.60.2/24"

resources = dict()
for system in sz_cp["composed_of"].values():
    resources[system["router_id"]] = [{"ipv4_addr": sz_rtr_ip}]

for v in sz_cp["composed_of"].values():
    for s in v["systems"].values():
        if s["system_label"].split("_")[-1] == "leaf1":
            resources[s["system_id"]] = [{"ipv4_addr": sz_leaf1_ip}]
        elif s["system_label"].split("_")[-1] == "leaf2":
            resources[s["system_id"]] = [{"ipv4_addr": sz_leaf2_ip}]


aos.blueprint.apply_sz_connectivity_points(
    bp_id=bp.id,
    sz_id=sz.id,
    links=sz_cp["composed_of"],
    peering_type="interface",
    resources=resources,
    ipv4_subnet=sz_subnet,
    vlan_id=sz_vlan_id,
)


# Commit Blueprint Changes
# It might take a bit of time for build errors to clear out as the
# backend updates. Here I am checking build errors until they clear.
repeat_until(lambda: aos.blueprint.has_build_errors(bp.id) is False, timeout=60)

aos.blueprint.commit_staging(bp.id, description="Milestone2")
