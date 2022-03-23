# Assign Blueprint Interface-maps
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

## Get Blueprint System Nodes
The ID of each system is different within the blueprint (/nodes) compared
to globally (/systems). We will need to correlate these two, so they can be
assigned appropriately.
```python
bp_nodes = aos.blueprint.get_bp_system_nodes(bp.id)
```

## Define IM mapping
```python
im_assignment = {
    "spine1": "Juniper_vQFX__slicer-7x10-1",
    "spine2": "Juniper_vQFX__slicer-7x10-1",
    "evpn_mlag_001_leaf1": "VS_SONiC_BUZZNIK_PLUS__slicer-7x10-1",
    "evpn_mlag_001_leaf2": "VS_SONiC_BUZZNIK_PLUS__slicer-7x10-1",
    "evpn_single_001_leaf1": "Arista_vEOS__slicer-7x10-1",
}
```

## Map Node to System ID
```python
assignment = dict()
for device, im in im_assignment.items():
    for value in bp_nodes.values():
        if value["label"] == device:
            assignment[value["id"]] = im
```

## Assign Interface Maps to Nodes
```python
data = {"assignments": assignment}
aos.blueprint.assign_interface_maps_raw(bp_id=bp.id, assignments=data)
```

## Bulk Assign Interface Maps
This method finds all system nodes in blueprint and assigns them the given IM.
```python
sys_nodes = ["spine1", "spine2", "leaf1"]
aos.blueprint.assign_interface_map_by_name(
    bp.id, node_names=sys_nodes, im_name="Arista_vEOS__slicer-7x10-1"
)
```