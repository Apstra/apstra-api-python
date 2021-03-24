# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
from aos.client import AosClient
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from aos.resources import Range
from scripts.utils import deserialize_fixture
from aos.repeat import repeat_until

# You will need to update the connection details below with your
# specific AOS instance
AOS_IP = "<aos-IP>"
AOS_PORT = 443
AOS_USER = "admin"
AOS_PW = "aos-aos"


# labguide 1 Step 3 - Multitenency

# Login
aos = AosClient(protocol="https", host=AOS_IP, port=AOS_PORT)
aos.auth.login(AOS_USER, AOS_PW)


# Configure New Security-Zone (VRF)
bp = aos.blueprint.get_bp(bp_name="apstra-pod1")

# 'create_security_zone has the option to configure the loopback pool
# along with dhcp_servers (relay) needed with each security-zone.
# We will use that here to save steps.
leaf_lo_pool = aos.resources.ipv4_pools.find_by_name(name="leaf-loopback").pop()
sz_name = "Finance"
dhcp_rely_addr = "9.0.0.1"

sz = aos.blueprint.create_security_zone_sync(
    bp_id=bp.id,
    name=sz_name,
    leaf_loopback_ip_pools=[leaf_lo_pool.id],
    dhcp_servers=[dhcp_rely_addr],
)

# Now we connect the external-router to the security-zone the same
# way we did in lab1 step2 for the default security-zone
sz_cp = aos.blueprint.get_sz_connectivity_points(bp.id, sz.id).pop()
sz_subnet = "10.60.61.0/24"
sz_vlan_id = 61
sz_rtr_ip = "10.60.61.254/24"
sz_leaf1_ip = "10.60.61.1/24"
sz_leaf2_ip = "10.60.61.2/24"

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


# Configure Virtual-Networks (VLANs)

# First we need to define which nodes to apply
# the virtual-networks to. We will apply them to both racks
# Note: With MLAG racks a single node will be returned representing
# both members of the MLAG. This is the node you must use.

bound_to = list()
tor_nodes = aos.blueprint.get_all_tor_nodes(bp.id)

for node in tor_nodes:
    bound_to.append({"system_id": node["id"]})

# Define the virtual-networks we will create.
virtual_networks = (deserialize_fixture("milestone3_virtual_networks.json"),)

for vn in virtual_networks:
    # Check if virtual-network already exist. Here I delete it if True.
    # Keep in mind changes here are in "stagging" and do not update the
    # fabric switches until they are commited.
    existing = aos.blueprint.find_vn_by_name(bp.id, vn["name"])
    if existing:
        aos.blueprint.delete_virtual_network(bp.id, existing.id)

    resp = aos.blueprint.create_virtual_network(
        bp_id=bp.id,
        name=vn["name"],
        bound_to=bound_to,
        sz_name=sz_name,
        ipv4_subnet=vn["ipv4_subnet"],
        ipv4_gateway=vn["ipv4_gateway"],
    )

# There is also 'add_virtual_network_batch' if you would like to
# add multiple virtual-networks at once.


# Assign New Security-Zone Resources
resources = deserialize_fixture("sz_vn_resources.json")

for r in resources:
    if r["type"] == "vni":
        pool = aos.resources.vni_pools.find_by_name(r["pool"]).pop()
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


# Commit Blueprint Changes
# It might take a bit of time for build errors to clear out as the
# backend updates. Here I am checking build errors until they clear.
repeat_until(lambda: aos.blueprint.has_build_errors(bp.id) is False, timeout=60)

aos.blueprint.commit_staging(bp.id, description="Milestone2")
