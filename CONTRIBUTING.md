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

## Building Releases
This function is currently handled by the project admin team. GitHub 
releases is currently used for release management. Git tags are used to
manage release version numbers. 
### steps
1. `git tag v0.x.y`
2. `git push --tags`
3. From Github validate the new tag is present with the correct commit.
4. From Github create a new release based on the new tag.
5. Github actions will then pick up the new release and trigger a release 
build and publish to pypi using the tagged version number

