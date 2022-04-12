# Welcome to apstra-api-python's documentation!

## What is apstra-api-python?
The apstra-api-python library is an example python library built for
learning how to integrate with the Apsta API programmatically. This
library also includes examples to common solutions faced when building and
managing an Apstra managed fabric.

## What apstra-api-python is not
While the apstra-api-python library can be used to build integrations with
Apstra, it is not intended to be a production-ready solution.
apstra-api-python does not include 100% coverage of the Apstra API and all
use-cases available.

Our hope is to provide enough working examples and documentation to get a
developer started with building client libraries based on the Apstra API.

## Organization and Structure
The apstra-api-python library is structured and organized in the same manor
as the Apstra User-Interface (UI). This is done to allow easy and
intuitive navigation of the library code in relation to the UI. You will
notice sub-modules within the 'aos' module line up with the Apstra UI menu
for each specific area.

The client.py module is used to build and organize the actual client. The
aos.py module defines how REST API requests are built and used along with
handling authentication and session setup.

Doc-Strings are used as much as possible within each module to document
usage and also build the module documentation found in this guide.

## Supported Python Versions
The bulk of the library is built and tested using Python 3.8. You should
be safe to use any Python 3 version above 3.6 but it is recommended to
stick with python 3.8 or above to have a smooth experience.
