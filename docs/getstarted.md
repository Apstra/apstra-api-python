# Getting Started

## Setup
setup python 3.8 virtual environment and install library with pip
```shell
$ python3.8 -m venv .venv
$ source .venv/bin/activate
$ pip install apstra-api-python
```

Working with the apstra-api-python library
```python
from aos.client import AosClient

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
AOS_IP = '<apstra-server-ip>'
AOS_PORT = '443'
AOS_USER = 'admin'
AOS_PW = 'admin'

aos = AosClient(protocol="https", host=AOS_IP, port=AOS_PORT)
aos.auth.login(AOS_USER, AOS_PW)
```