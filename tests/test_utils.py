
# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
# pylint: disable=redefined-outer-name

from aos.utils import redacted


def test_redacted_null():
    assert redacted(None) is None


def test_redacted_empty():
    assert redacted('') == ''


def test_redacted_sensitive():
    for sensitive in ["password", "token", "AuthToken"]:
        d = {
            'usual': 'usual data',
            sensitive: '{sensitive} data',
        }
        assert redacted(d) == {
                'usual': 'usual data',
                sensitive: '<REDACTED>',
            }
