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
### Fabric Nodes
Return all fabric nodes (switches). Notice the use of `is_in` to filter 
the query by role.
```python
switch_query = (
                "match(node('system', name='switches', "
                "role=is_in(['spine', 'leaf', 'superspine'])))"
)
resp = aos.blueprint.qe_query(bp.id, 
                              query=switch_query, 
                              params={"type": "staging"})
```
In the query above `{"type": "staging"}` is included as a params 
argument. This allows you to specify either the `staging` or `operation`
(active) blueprint graph.
This parameter is supported for both QE and QL queries. The default is 
`staging`

### Get all ToR Nodes
A good example of QE queries in action is the
`aos.blueprint.get_all_tor_nodes()` method which uses two queries to 
return all top of rack (ToR) nodes and their properties. It calls two 
methods to collect the data it needs.

- `aos.blueprint.get_bp_system_leaf_nodes()` returns all nodes of type 
`system` with a role of `leaf`.
    ```python
    leaf_query = "match(node('system', name='leaf', role='leaf'))"
    resp = aos.blueprint.qe_query(bp.id, 
                                  query=leaf_query,
                                  params={"type": "staging"})
    ```

- `aos.blueprint.get_bp_system_redundancy_group()` returns the
redundancy_group (ESI/MLAG) details for a given system. Notice `system_id`
is passed in as a variable for this query which is done for each system returned in
the above query to determine if the system belongs to a redundancy_group.
    ```python
    system_id = 'foo'
    rg_query = (
                "match(node('redundancy_group', name='rg')"
                ".out('composed_of_systems')"
                ".node('system', role='leaf',"
                f" id='{system_id}'))"
    )
    resp = aos.blueprint.qe_query(bp.id, 
                                  query=rg_query,
                                  params={"type": "staging"})
    ```

### Links in fabric
Query the Blueprint for all fabric links between leafs and spines
```python
link_query = (
              "match(node('system', role='leaf', name='system')"
              ".out('hosted_interfaces')"
              ".node('interface', name='iface').out('link')"
              ".node('link', role='spine_leaf'))"
            ),
resp = aos.blueprint.qe_query(bp.id, 
                              query=link_query,
                              params={"type": "staging"})
```

### Routing-zone fabric links
Query the Blueprint for all links in the fabric belonging to a specific
routing-zone (VRF). We are using routing-zone `blue` in this example.

You will also notice there are two queries combined here, the second query
starting with `node('system, role='leaf')`. This allows you to take the 
output of the first query and pass it into a new query.
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
resp = aos.blueprint.qe_query(bp.id, 
                              query=link_query,
                              params={"type": "staging"})
```

## QL Queries
### Leaf nodes interface details
Query the blueprint for all system leaf nodes and their current interface 
details. This query also includes the connected links for each node. 
Notice `(role: \"leaf\")` is used to filter by role. 
```python
leaf_node_query = (
                "{"
                    "system_nodes (role: \"leaf\"){"
                        "role " 
                        "id " 
                        "hostname "
                        "hosted_interfaces_targets {"
                            "ipv4_addr "
                            "if_name "
                            "link_targets {"
                                "link_type "
                                "id "
                                "speed "
                                "tags "
                            "}"
                        "}"
                    "}"
                "}"
)

resp = aos.blueprint.ql_query(bp.id, 
                              query=leaf_node_query, 
                              params={"type": "staging"})
```

### Routing-zone interface details
Query the blueprint for all Routing-zones and their current interface 
details. This query also includes the DHCP relay configured.
`instantiated_by_targets` is used to order the interfaces by type, first 
by `loopback`, then by `subinterface`.
```python
sz_query = (
           "{"
                "security_zone_nodes {"
                    "id "
                    "label "
                    "sz_type "
                    "vrf_name "
                    "vni_id "
                    "vlan_id "
                    "instantiated_by_targets {"
                        "loopback : member_interfaces_targets(if_type:\"loopback\") {"
                            "if_name "
                            "ipv4_addr "
                            "ipv6_addr "
                        "}"
                        "subinterface : member_interfaces_targets(if_type:\"subinterface\") {"
                            "if_name "
                            "ipv4_addr "
                            "ipv6_addr "
                            "ipv6_enabled link : link_targets {role}"
                        "}"
                    "}"
                    "policy_policy_targets(policy_type:\"dhcp_relay\") {"
                        "dhcp_servers"
                    "}"
                "}"
           "}"   
)
resp = aos.blueprint.ql_query(bp.id, 
                              query=sz_query, 
                              params={"type": "operations"})
```