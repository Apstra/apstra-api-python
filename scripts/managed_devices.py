# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
from aos.client import AosClient
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from aos.resources import Range

# You will need to update the connection details below with your
# specific AOS instance
AOS_IP = "<aos-IP>"
AOS_PORT = 443
AOS_USER = "admin"
AOS_PW = "aos-aos"

# Login
aos = AosClient(protocol="https", host=AOS_IP, port=AOS_PORT)
aos.auth.login(AOS_USER, AOS_PW)


# Install System Agents
devices = [
    {"name": "Spine1", "ip": "192.168.0.90"},
    {"name": "Spine2", "ip": "192.168.0.91"},
    {"name": "Leaf1", "ip": "192.168.0.100"},
    {"name": "Leaf2", "ip": "192.168.0.101"},
    {"name": "Leaf3", "ip": "192.168.0.102"},
]
for d in devices:
    aos.devices.system_agents.create(
        management_ip=d["ip"], label=d["name"], username="admin", password="admin"
    )

# Find system agent
aos.devices.system_agents.find_agent_with_ip(ip_addr="192.168.0.90")


# Find System with AOS agent installed
aos.devices.managed_devices.find_system_with_ip(ip_addr="192.168.0.90")


# Acknowledge all devices
aos.devices.managed_devices.acknowledge_all()
