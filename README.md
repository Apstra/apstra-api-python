# AOS RestAPI Python Library

Python library used to programmatically interact with AOS and integrate the AOS 
RestAPI.

## Getting started
```
>>> from aos.client import AosClient
>>> 
>>> AOS_IP = '192.168.100.1'
>>> AOS_PORT = '443'
>>> AOS_USER = 'admin'
>>> AOS_PW = 'admin'
>>> 
>>> aos = AosClient(protocol="https", host=AOS_IP, port=AOS_PORT)
>>> aos.auth.login(AOS_USER, AOS_PW)

```
## Documentation
Documentation is currently found in [/docs](./docs/_build/html). 

### Scripts and Examples
Standalone scripts along with a number of end-to-end examples can be
found in [/scripts](./scripts). Make sure to check out the [Readme](./scripts/README.md)


## Testing
### Setup Development Environment

Create a virtual environment and install aos-api:

```
$ cd aos-api
$ python3.8 -m venv .venv
$ source .venv/bin/activate
$ python setup.py install
$ pip install -r dev-requirements.txt
```

### Running Tests
- Run full test suite
```
$ tox
``` 

 - Run unit tests:
```
$ tox -e py38
```

 - Run linters:
```
$ tox -e flake8
```

### Format code
Black is used to format code
```
black aos/
black tests/
```