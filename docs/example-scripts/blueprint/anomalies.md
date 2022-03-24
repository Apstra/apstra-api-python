# Get Blueprint Anomalies
## Imports
```python
from aos.client import AosClient
from aos.repeat import repeat_until
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

## Get all anomalies
```python
aos.blueprint.anomalies_list(bp.id)
```

## Check if anomalies exist 
Here we are using logic that waits for the blueprint to fully converge
with no anomalies reported before moving onto the next action of the 
workflow. This is a powerful heath check, as it encompasses all points of
telemetry and intent of the fabric built into a single call.
```python
repeat_until(lambda: aos.blueprint.has_anomalies(bp.id) is False,
             timeout=500)
```