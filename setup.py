# Copyright 2019-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula

from os.path import dirname, abspath
from setuptools import setup, find_packages

NAME = "aos-api-client"

# VERSION_FILE_PATH = dirname(abspath(__file__)) + "/VERSION"
# with open(VERSION_FILE_PATH, "r", encoding="utf-8") as f:
#    VERSION = f.readline().strip()
VERSION = 0.1


REQUIRES = ["requests==2.24.0"],

setup(
    name=NAME,
    version=VERSION,
    description="Apstra AOS API Client",
    url="https://github.com/Apstra/aos-api-python",
    author="Apstra Inc",
    author_email="support@apstra.com",
    packages=find_packages(include=['aos']),
    include_package_data=True,
    python_requires=">=3.5",
    install_requires=REQUIRES,
    license="Proprietary",
    keywords="aos apstra",
)