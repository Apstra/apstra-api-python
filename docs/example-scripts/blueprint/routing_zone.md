# Routing Zones (VRFs)
In Apstra 4.0 Security-Zones were renamed Routing-Zones. To conform
to backwards-conpatability of the API you will see the security-zone 
API endpoint used. 
## Imports
```python
import json

from aos.client import AosClient
from scripts.utils import deserialize_fixture, render_jinja_template
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```

You will need to update the connection details below with your
specific AOS instance
```python
AOS_IP = "<aos-IP>"
AOS_PORT = 443
AOS_USER = "admin"
AOS_PW = "aos-aos"
```

## Login
```python
aos = AosClient(protocol="https", host=AOS_IP, port=AOS_PORT)
aos.auth.login(AOS_USER, AOS_PW)
```

## Find Blueprint by Name
```python
bp_name = "apstra-pod1"
bp = aos.blueprint.get_id_by_name(label=bp_name)
```

## Find IP resource pool to use with the Routing-Zone
```python
leaf_lo_pool = aos.resources.ipv4_pools.find_by_name(name="leaf-loopback").pop()
sz_name = "Finance"
dhcp_rely_addr = "9.0.0.1"
```

## Create Routing-Zone
```python
aos.blueprint.create_security_zone(
    bp_id=bp.id,
    name=sz_name,
    leaf_loopback_ip_pools=[leaf_lo_pool.id],
    dhcp_servers=[dhcp_rely_addr],
)
```

## Get Routing-Zone Details by name
```python
rz = aos.blueprint.find_sz_by_name(bp.id, name="Finance")
```