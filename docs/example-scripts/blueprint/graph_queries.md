# Graph Queries (QE and QL)
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

## QE Queries
Return all fabric switches (nodes). Notice the use of "is_in" with role
to filter the query.
```python
switch_query = (
                "match(node('system', name='switches', "
                "role=is_in(['spine', 'leaf', 'superspine'])))"
)
resp = aos.blueprint.qe_query(bp.id, query=switch_query)
```

`aos.blueprint.get_all_tor_nodes()` uses two queries to return all top of
rack (ToR) nodes and their properties. It calls two methods to do this.

`aos.blueprint.get_bp_system_leaf_nodes()` returns all nodes of type system
with a role of 'leaf'.
```python
leaf_query = "match(node('system', name='leaf', role='leaf'))"
resp = aos.blueprint.qe_query(bp.id, query=leaf_query)
```

`aos.blueprint.get_bp_system_redundancy_group()` returns the
redundancy_group details a given system is a member of.
```python
system_id = 'foo'
rg_query = (
            "match(node('redundancy_group', name='rg')"
            ".out('composed_of_systems')"
            ".node('system', role='leaf',"
            f" id='{system_id}'))"
)
resp = aos.blueprint.qe_query(bp.id, query=rg_query)
```

Query the Blueprint for all fabric links between leafs and spines
```python
link_query = (
              "match(node('system', role='leaf', name='system')"
              ".out('hosted_interfaces')"
              ".node('interface', name='iface').out('link')"
              ".node('link', role='spine_leaf'))"
            ),
resp = aos.blueprint.qe_query(bp.id, query=link_query)
```

Query the Blueprint for all links in the fabric belonging to a specific
routing-zone (VRF). We are using routing-zone 'blue' in this example.
```python
link_query = (
              "match(node('system', role='spine', deploy_mode='deploy')"
              ".out('hosted_interfaces')"
              ".node('interface', name='leaf_intf')"
              ".out('link')"
              ".node('link', role='spine_leaf')"
              ".in_('link')"
              ".node('interface')"
              ".in_('hosted_interfaces')"
              ".node('system', role='leaf'),"
              "node(name='leaf_intf')"
              ".in_('member_interfaces')"
              ".node('sz_instance')"
              ".in_('instantiated_by')"
              ".node('security_zone', vrf_name='blue')"
)
resp = aos.blueprint.qe_query(bp.id, query=link_query)
```

# QL Queries
:(