# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging

logger = logging.getLogger(__name__)


def redacted(d):
    if d is None or d == "":
        return d

    h = d.copy()
    for sensitive in ["password", "token", "AuthToken"]:
        if sensitive in d:
            h[sensitive] = "<REDACTED>"
    return h
