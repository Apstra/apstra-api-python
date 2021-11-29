# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
from aos.client import AosClient
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# You will need to update the connection details below with your
# specific AOS instance
AOS_IP = "<aos-IP>"
AOS_PORT = 443
AOS_USER = "admin"
AOS_PW = "admin"

aos = AosClient(protocol="https", host=AOS_IP, port=AOS_PORT)
aos.auth.login(AOS_USER, AOS_PW)
