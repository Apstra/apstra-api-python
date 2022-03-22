# Assign Devices to Blueprint
## Imports
```python
from aos.client import AosClient
from scripts.utils import deserialize_fixture
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

## Assign Device
Static assignment 
```python
aos.blueprint.assign_device(
    bp.id,
    system_id="525400DCC108",
    node_id="80f4b1ee-5268-424b-85ec-c218369e76ed",
    deploy_mode="deploy",
)
```

## Assign Devices based on System Location Field
This method assumes all systems' location field matches the blueprint
node name exactly
```python
aos.blueprint.assign_all_devices_from_location(bp.id, deploy_mode="deploy")
```

## Dynamically identify and assign all devices to nodes based on IP address
### Collect BP System nodes and IM assignment
In this example we build a map of the device role to interface-map for
asignment. We then assign devices based on the management IP address of the device
or system.
```python
bp_nodes = aos.blueprint.get_bp_system_nodes(bp.id)
im_assignment = {
    "spine1": "Juniper_vQFX__slicer-7x10-1",
    "spine2": "Juniper_vQFX__slicer-7x10-1",
    "evpn_mlag_001_leaf1": "VS_SONiC_BUZZNIK_PLUS__slicer-7x10-1",
    "evpn_mlag_001_leaf2": "VS_SONiC_BUZZNIK_PLUS__slicer-7x10-1",
    "evpn_single_001_leaf1": "Arista_vEOS__slicer-7x10-1",
}


systems = aos.devices.managed_devices.get_all()
system_list = []
node_assignment = []
```

## Assign location field
We assume we know the IP address of each device in this example. 
Depending on your environment you might need different logic.
```python
def get_last_octet(ipaddr):
    return int(ipaddr.split(".")[3])


for s in systems:
    if get_last_octet(s.facts["mgmt_ipaddr"]) == 11:
        system_list.append({"id": s.id, "location": "spine1"})
    elif get_last_octet(s.facts["mgmt_ipaddr"]) == 12:
        system_list.append({"id": s.id, "location": "spine2"})
    elif get_last_octet(s.facts["mgmt_ipaddr"]) == 13:
        system_list.append({"id": s.id, "location": "evpn_mlag_001_leaf1"})
    elif get_last_octet(s.facts["mgmt_ipaddr"]) == 15:
        system_list.append({"id": s.id, "location": "evpn_mlag_001_leaf2"})
    elif get_last_octet(s.facts["mgmt_ipaddr"]) == 14:
        system_list.append({"id": s.id, "location": "evpn_single_001_leaf1"})
    else:
        print(f"{s.facts['mgmt_ipaddr']} unknown device")
```

## Build Payload
```python
for s in system_list:
    for v in bp_nodes.values():
        if v["label"] == s["location"]:
            node_assignment.append(
                {"system_id": s["id"], "id": v["id"], "deploy_mode": "deploy"}
            )
```

## Assign Devices
```python
aos.blueprint.assign_devices_from_json(bp.id, node_assignment)
```