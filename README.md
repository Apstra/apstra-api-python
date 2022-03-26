# Apstra (AOS) RestAPI Python Library
[![CircleCI](https://circleci.com/gh/Apstra/apstra-api-python/tree/main.svg?style=svg)](https://circleci.com/gh/Apstra/apstra-api-python/tree/main)

Educational Python library with the goal to teach users how to 
programmatically interact with apstra and integrate the Apstra 
Rest API.

## Documentation
If you are new to Apstra, this library or looking to get a better understanding of 
the apstra Rest API please start with the 
[documentation](https://apstra-api-python.readthedocs.io/en/latest/api-introduction/).

# Developers
## Testing
### Setup Development Environment

Create a virtual environment and install aos-api-python:

```
$ cd apstra-api-python
$ python3.8 -m venv .venv
$ source .venv/bin/activate
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