# Contributing to apstra-api-python
Thank you for contributing to apstra-api-python!

## Bugs?
Please report bugs as issues here on GitLab! 

## Code submission
Submit your code as a new branch based off `main` and submit a Pull 
Request (PR). All tests and approvals of a PR must be meet before merge.

Dont forget to update the version number in [setup.py](./setup.py)

### Developers
### Setup Development Environment
Create a virtual environment and install apstra-api-python:
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
Black is used to format code pre-commit
```
black aos/
black tests/
```


