# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
from aos.client import AosClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from aos.resources import Range
from scripts.utils import deserialize_fixture

# You will need to update the connection details below with your
# specific AOS instance
AOS_IP = "<aos-IP>"
AOS_PORT = 443
AOS_USER = "admin"
AOS_PW = "aos-aos"


# labguide 1 step 1 - Resources

# Login
aos = AosClient(protocol="https", host=AOS_IP, port=AOS_PORT)
aos.auth.login(AOS_USER, AOS_PW)


# Create IP Resource Pool
aos.resources.ipv4_pools.create(
    name="apstra-pool", subnets=["4.0.0.0/24", "4.0.1.0/24"]
)


# Create ASN Resource Pool
aos.resources.asn_pools.create(name="vpod-evpn-asn-pool", ranges=[Range(100, 1000)])


# Create External Router
aos.external_systems.external_router.create(
    name="apstra-rtr", asn=10, address="9.0.0.1"
)


# Create Rack Types
rt_mlag = deserialize_fixture("rack_type_evpn_mlag.json")
rt_single = deserialize_fixture("rack_type_evpn_single.json")
rt_list = [rt_mlag, rt_single]

# Here I am making sure the rack-types don't already exist.
for rt in [rt_mlag, rt_single]:
    rt_id = rt["id"]
    if aos.design.rack_types.get(rt_id):
        aos.design.rack_types.delete_rack_type(rt_id)

aos.design.rack_types.add_rack_type(rt_list=rt_list)


# Create EVPN Template
evpn_template = deserialize_fixture("evpn_template.json")

# make sure the template does not already exist
temp_id = evpn_template["id"]
if aos.design.templates.get_template(temp_id):
    aos.design.templates.delete_templates(temp_id)

aos.design.templates.add_template([evpn_template])


# Acknowledge all Devices
# acknowledge_all assumes all devices in AOS should
# be acknowledged
aos.devices.managed_devices.acknowledge_all()
