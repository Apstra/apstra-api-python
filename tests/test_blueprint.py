# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
# pylint: disable=redefined-outer-name

import json

import pytest

from aos.client import AosClient
from aos.aos import AosRestAPI
from aos.blueprint import Blueprint


from tests.util import make_session, read_fixture


@pytest.fixture(params=["3.3.0"])
def aos_api_version(request):
    return request.param


@pytest.fixture
def aos_session():
    return make_session()


@pytest.fixture
def aos(aos_session):
    return AosClient(protocol="http", host="aos", port=80, session=aos_session)


@pytest.fixture
def expected_auth_headers():
    headers = AosRestAPI.default_headers.copy()
    headers["AuthToken"] = "token"
    return headers


@pytest.fixture
def aos_logged_in(aos, aos_session):
    successful_login_resp = {"token": "token", "id": "user-id"}

    aos_session.add_response(
        "POST",
        "http://aos:80/api/aaa/login",
        status=200,
        resp=json.dumps(successful_login_resp),
    )
    resp = aos.auth.login(username="user", password="pass")
    assert resp.token == "token"

    aos_session.request.call_args_list.pop()
    aos_session.request.call_count = aos_session.request.call_count - 1

    return aos


def test_get_all_ids(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    aos_session.add_response(
        "GET",
        "http://aos:80/api/blueprints",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/blueprints/blueprints.json"),
    )

    assert aos_logged_in.blueprint.get_all_ids() == [
        Blueprint(
            id="evpn-cvx-virtual",
            label="evpn-cvx-virtual",
        ),
        Blueprint(
            id="37e5bf9d-46e6-4479-85e9-96ecf47e00e0",
            label="test",
        ),
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/blueprints",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_find_by_label(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    bp_id = "evpn-cvx-virtual"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/blueprints",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/blueprints/blueprints.json"),
    )

    assert aos_logged_in.blueprint.find_id_by_label(bp_id) == Blueprint(
        id=bp_id, label=bp_id
    )

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/blueprints",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_get_staging_version(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    bp_id = "evpn-cvx-virtual"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/diff-status",
        status=202,
        resp=read_fixture(
            f"aos/{aos_api_version}/blueprints/bp_staging_version.json"),
    )

    assert aos_logged_in.blueprint.get_staging_version(bp_id) == {
        "version": 3,
        "status": "undeployed",
        "deploy_error": None,
    }

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/diff-status",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )
