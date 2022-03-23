# Apstra Login
## Imports
```python
from aos.client import AosClient
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
```
You will need to update the connection details below with your
specific AOS instance
```python
AOS_IP = "<aos-IP>"
AOS_PORT = 443
AOS_USER = "admin"
AOS_PW = "admin"
```

```python
aos = AosClient(protocol="https", host=AOS_IP, port=AOS_PORT)
aos.auth.login(AOS_USER, AOS_PW)
```
Once authenticated successfully your client session `aos` will
handle authentication headers for each request. 
