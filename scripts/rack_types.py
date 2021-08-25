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


# Import Rack Type template
rt_mlag = deserialize_fixture("rack_type_evpn_mlag.json")

# Create Rack-Type
aos.design.rack_types.create(rt_mlag)


# Find Rack-Type by name
aos.design.rack_types.find_by_name("apstra-mlag")
