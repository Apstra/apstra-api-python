# Create External Generic Systems
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

## Create External Generic System
```python
ext_rtr = aos.blueprint.create_ext_generic_systems(
    bp_id=bp.id,
    hostname="external-router",
    asn="10",
    loopback_ip="9.0.0.1/32",
    tags=["Router"],
)
```

## Create links from fabric to external system
```python
bp_nodes = aos.blueprint.get_bp_system_nodes(bp.id)
rtr_leaf_map = [
    ("evpn-mlag-001-leaf1", "swp7", "router", "eth1"),
    ("evpn-mlag-001-leaf2", "swp7", "router", "eth2"),
]
links = dict()
for node in bp_nodes.values():
    if node["role"] == "leaf" and node["group_label"] == "evpn-mlag":
        links[node["hostname"]] = {}
        links[node["hostname"]]["id"] = node["id"]
        links[node["hostname"]]["label"] = node["label"]
        for i in rtr_leaf_map:
            if i[0] == node["hostname"]:
                links[node["hostname"]]["if_name"] = i[1]

node_links = list()
for link in links.values():
    node_links.append(
        {
            "link_group_label": f"ext-rtr-{link['label']}",
            "lag_mode": None,
            "tags": ["Router"],
            "switch": {
                "system_id": link["id"],
                "transformation_id": 1,
                "if_name": link["if_name"],
            },
            "system": {"system_id": ext_rtr["id"]},
        }
    )


ext_rtr_links = {"links": node_links}

aos.blueprint.create_switch_system_links(bp.id, data=ext_rtr_links)
```