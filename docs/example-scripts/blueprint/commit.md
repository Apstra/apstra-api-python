# Commit Change to Blueprint
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

## Commit Changes to blueprint
```python
aos.blueprint.commit_staging(bp.id, description="My Changes")
```

## Wait for Blueprint error to clear before committing
Depending on what changes you are making to a blueprint, a commit can take
a while to fully converge. Here we are using logic that waits for the
blueprint to fully converge and return no errors before moving on.
```python
repeat_until(lambda: aos.blueprint.has_build_errors(bp.id) is False,
             timeout=500)
aos.blueprint.commit_staging(bp.id, description="Milestone2")
```