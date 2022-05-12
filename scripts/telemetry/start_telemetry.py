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
ALERTS_PORT = 64420
EVENTS_PORT = 64421
PERFMON_PORT = 64422

# Login
aos = AosClient(protocol="https", host=AOS_IP, port=AOS_PORT)
aos.auth.login(AOS_USER, AOS_PW)
aos.telemetry_mgr.add_endpoint("100.123.0.8", ALERTS_PORT, "alerts")
aos.telemetry_mgr.add_endpoint("100.123.0.8", EVENTS_PORT, "events")
aos.telemetry_mgr.add_endpoint("100.123.0.8", PERFMON_PORT, "perfmon")
print(aos.telemetry_mgr.get_endpoints())
