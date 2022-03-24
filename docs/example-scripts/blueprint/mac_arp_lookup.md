# Mac address and ARP Queries
A common scenario for Network Engineers is to find the location details of 
a specific MAC address or a known IP address. 

  > This library has the ability to pass in api endpoints directly for 
  > features that have not been implemented yet. We will use this method
  > here to highlight its use and flexability so you can explore other 
  > endpoints on your own.

## Imports
```python
from aos.client import AosClient
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

## Find all devices and location details
```python
mac_lookup_endpoint = f"/api/blueprints/{bp.id}/query/mac"
payload = {"mac_address": "*"}

resp = aos.rest.json_resp_post(uri=mac_lookup_endpoint, data=payload)
print(resp['items'])
```

## Find Device with MAC Address
```python
mac_lookup_endpoint = f"/api/blueprints/{bp.id}/query/mac"
mac_address = "52:15:a5:e7:1b:08"
payload = {"mac_address": mac_address}

resp = aos.rest.json_resp_post(uri=mac_lookup_endpoint, data=payload)
print(resp['items'])
```

### Additional MAC filtering options
You can adjust the filtering options for MAC queries by including 
additional options in the payload body. 
```python
payload = {
    "vlan": "string",
    "exclude_interface": "string",
    "query_filter": "string",
    "system_id": "string",
    "mac_address": "string",
    "vxlan": "string"
}
```

## Find device with IP Address
```python
ip_lookup_endpoint = f"/api/blueprints/{bp.id}/query/arp"
ip_address = "10.1.5.53"
payload = {"ip_address": ip_address}

resp = aos.rest.json_resp_post(uri=ip_lookup_endpoint, data=payload)
print(resp['items'])
```

### Additional IP filtering options
You can adjust the filtering options for ARP queries by including 
additional options in the payload body. 
```python
payload = {
    "ip_address": "string",
    "system_id": "string",
    "query_filter": "string",
    "mac_address": "string"
}
```