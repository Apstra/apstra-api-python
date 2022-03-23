# Rack Types
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

## Import Rack Type template
```python
rt_mlag = deserialize_fixture("rack_type_evpn_mlag.json")
```

## Create Rack-Type
```python
aos.design.rack_types.create(rt_mlag)
```

## Find Rack-Type by name
```python
aos.design.rack_types.find_by_name("apstra-mlag")
```