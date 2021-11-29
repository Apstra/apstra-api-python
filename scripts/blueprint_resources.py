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


# Find Resource pool IDs
spine_asn_pool = aos.resources.asn_pools.find_by_name("asn-pool").pop()


# Assign resource pools to Blueprint
aos.blueprint.apply_resource_groups(
    bp_id=bp.id,
    resource_type="asn",
    group_name="spine-asns",
    pool_ids=[spine_asn_pool.id],
)


# Assign All Avialable Resources in Blueprint
# Not all resources are available in a Blueprint from the begging
# As you add elements (VNs, routing-zones, etc) additional resources
# will be required.
# This code sample looks up all resources available in a Blueprint,
# and assigns the given pools configured in the file.
# Running this multiple times through out your blueprint build
# will ensure all resources get assigned as they come available.
assignments = deserialize_fixture("bp_resources.json")
resources = aos.blueprint.get_all_bp_resource_groups(bp.id)

for r in resources:
    if not r.pool_ids:
        for a in assignments:
            if r.group_name == a["name"]:
                if a["type"] == "asn":
                    pool = aos.resources.asn_pools.find_by_name(a["pool"]).pop()
                    aos.blueprint.apply_resource_groups(
                        bp_id=bp.id,
                        resource_type=a["type"],
                        group_name=r.name,
                        pool_ids=[pool.id],
                    )
                elif a["type"] == "vni":
                    pool = aos.resources.vni_pools.find_by_name(a["pool"]).pop()
                    aos.blueprint.apply_resource_groups(
                        bp_id=bp.id,
                        resource_type=a["type"],
                        group_name=r.name,
                        pool_ids=[pool.id],
                    )
                elif a["type"] == "ip":
                    pool = aos.resources.ipv4_pools.find_by_name(a["pool"]).pop()
                    aos.blueprint.apply_resource_groups(
                        bp_id=bp.id,
                        resource_type=a["type"],
                        group_name=r.name,
                        pool_ids=[pool.id],
                    )
                elif a["type"] == "ipv6":
                    pool = aos.resources.ipv6_pools.find_by_name(a["pool"]).pop()
                    aos.blueprint.apply_resource_groups(
                        bp_id=bp.id,
                        resource_type=a["type"],
                        group_name=r.name,
                        pool_ids=[pool.id],
                    )
