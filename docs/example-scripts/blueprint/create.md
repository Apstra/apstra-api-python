# Create Blueprint
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

## Find Template by Name
```python
template_name = "apstra-evpn-mlag"
template = aos.design.templates.find_by_name(template_name=template_name).pop()
```

## Create Blueprint
Blueprint id is returned when creating and we will use that throughout.
```python
bp_name = "apstra-pod1"
bp = aos.blueprint.add_blueprint(label=bp_name, template_id=template.id)
```

## Get Blueprint details
```python
aos.blueprint.get_bp(bp_id=bp["id"])
```

## Find Blueprint by Name
```python
aos.blueprint.get_bp(bp_name=bp_name)
```

## Get Blueprint ID by Name
```python
bp = aos.blueprint.get_id_by_name(label=bp_name)
```