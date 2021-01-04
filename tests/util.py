# Copyright 2019-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula

import json
import os
import sys
from collections import defaultdict
from unittest import mock
from unittest.mock import call
from urllib.parse import urlencode

from requests import Response, PreparedRequest


def fixtures_path(path):
    return os.path.join(os.getcwd(), "tests/fixtures", path)


def read_fixture(path):
    with open(fixtures_path(path), "r") as fp:
        return fp.read()


def deserialize_fixture(path):
    if not path.endswith(".json"):
        path += ".json"
    with open(fixtures_path(path), "r") as fp:
        return json.load(fp)


def errors(resp) -> str:
    """Converts erroneous HTTP response JSON payload to string by joining together
    all error messages"""

    messages = str(resp)

    if resp and resp.is_json and resp.data:
        messages = (
            resp.json
            if "errors" not in resp.json
            else ". ".join(m["message"] for m in resp.json["errors"])
        )

    return f"errors: {messages}"


RESP_IGNORED = object()


def make_session():
    m = mock.Mock()
    m.response_store = defaultdict(list)

    def get_params(params):
        return urlencode(params) if params is not None else None

    def key(method, url, params):
        return method, url, get_params(params)

    def matching_responses(method, url, params):
        for (method_, url_, params_) in m.response_store:
            p = get_params(params)

            if call(method_, url_, params_) == call(method, url, p):
                yield method_, url_, params_

    def remove_response(method, url, params=None, status=200, resp=RESP_IGNORED):
        for k in matching_responses(method, url, params):
            responses = m.response_store[k]
            new_responses = [
                r
                for r in responses
                if not (
                    r.status_code == status
                    and (resp == RESP_IGNORED or r.data == resp)
                )
            ]
            m.response_store[k] = new_responses

    def add_response(method, url, params=None, status=200, resp=None):
        if callable(resp):
            resp = resp()

        resp = "" if resp is None else resp
        if not isinstance(resp, bytearray):
            resp = bytearray(resp, encoding=sys.getdefaultencoding())

        r = Response()
        r.status_code = status
        r.url = url
        r.request = PreparedRequest()
        # pylint: disable=protected-access
        r._content = resp
        m.response_store[key(method, url, params)].append(r)

    # pylint: disable=redefined-outer-name
    def request(method, url, params, json, *_args, **_kwargs):
        def exact_match():
            k_ = key(method, url, params)
            return k_ if k_ in m.response_store else None

        def partial_match():
            results = [k_ for k_ in matching_responses(method, url, params)]

            assert len(results) in [0, 1], (
                f"Multiple matching results for {method} {url} {params}; "
                f"results={results}"
            )

            if results:
                return results.pop(0)

        k = exact_match() or partial_match()

        if k:
            if len(m.response_store[k]) > 1:
                return m.response_store[k].pop(0)
            if len(m.response_store[k]) == 1:
                return m.response_store[k][0]

        raise ValueError(
            f"Unexpected request made: "
            f"{method} {url} params={params} data={json}; "
            f"available responses={m.response_store.keys()}. Use `add_response()` "
            f"to add responses."
        )

    m.add_response.side_effect = add_response
    m.remove_response.side_effect = remove_response
    m.request.side_effect = request
    return m
