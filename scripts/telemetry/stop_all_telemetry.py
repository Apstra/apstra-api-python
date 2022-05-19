import aos
from aos.client import AosClient
import urllib3
import json
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# You will need to update the connection details below with your
# specific AOS instance
AOS_IP = "66.129.234.206"
AOS_PORT = 37000 
AOS_USER = "admin"
AOS_PW = "admin"

# Where is the listener listening?
LISTENER_IP = "100.123.0.8"
ALERTS_PORT = 64429
EVENTS_PORT = 64428
PERFMON_PORT = 64427

# Login
aos = AosClient(protocol="https", host=AOS_IP, port=AOS_PORT)
aos.auth.login(AOS_USER, AOS_PW)
aos.telemetry_mgr.delete_all_endpoints()
