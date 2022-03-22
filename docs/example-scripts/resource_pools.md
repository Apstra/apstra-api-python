# Resources
## Imports
```python
from aos.client import AosClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from aos.resources import Range
```

You will need to update the connection details below with your
specific AOS instance
```python
AOS_IP = "<aos-IP>"
AOS_PORT = 443
AOS_USER = "admin"
AOS_PW = "aos-aos"
```

# Login
```python
aos = AosClient(protocol="https", host=AOS_IP, port=AOS_PORT)
aos.auth.login(AOS_USER, AOS_PW)
```

## Create Resource Pools
### IPv4 pool
```python
aos.resources.ipv4_pools.create(
    name="ip-pool", 
    subnets=["4.0.0.0/24", "4.0.1.0/24"]
)
```

### ASN Pool
```python
aos.resources.asn_pools.create(
    name="asn-pool", 
    ranges=[Range(100, 1000)]
)
```

### VNI Pool
```python
aos.resources.vni_pools.create(
    name="vni-pool", 
    ranges=[Range(5600, 5700)]
)
```


## Find Resource Pool by Name
```python
vni_pool = aos.resources.vni_pools.find_by_name("vni-pool").pop()
```

## Get resource pool details
```python
aos.resources.vni_pools.get(vni_pool.id)
```python