#!python3
# Copyright 2019-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula

import os
from setuptools import setup, find_packages

NAME = "aos-api-client"

from aos._version import __version__
VERSION = __version__


REQUIRES = (["requests==2.24.0"],)

setup(
    name=NAME,
    version=VERSION,
    description="Apstra AOS API Client",
    url="https://github.com/Apstra/aos-api-python",
    author="Apstra Inc",
    author_email="support@apstra.com",
    packages=find_packages(include=["aos"]),
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=REQUIRES,
    license="Proprietary",
    keywords="aos apstra",
)
