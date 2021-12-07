# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
# pylint: disable=redefined-outer-name

import json
import pytest

from aos.client import AosClient
from aos.aos import AosRestAPI
from aos.external_systems import ExternalRouter

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


def test_external_router_iter_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/external_systems/get_ext_rtrs.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/external-routers",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert list(aos_logged_in.external_systems.external_router.iter_all()) == [
        ExternalRouter(
            display_name="example_router1",
            id="example_router1",
            asn=65534,
            address="198.51.100.1",
        ),
        ExternalRouter(
            display_name="dualstack_example_router2",
            id="dualstack_example_router2",
            asn=65533,
            address="198.51.100.2",
        ),
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/external-routers",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_find_external_router_by_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/external_systems/get_ext_rtrs.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/external-routers",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert aos_logged_in.external_systems.external_router.find_by_name(
        "example_router1"
    ) == [
        ExternalRouter(
            display_name="example_router1",
            id="example_router1",
            asn=65534,
            address="198.51.100.1",
        ),
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/external-routers",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_external_router_create(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/external_systems/get_ext_rtr_id.json"
    rtr_id = "example_router1"

    aos_session.add_response(
        "POST",
        "http://aos:80/api/resources/external-routers",
        status=202,
        resp=json.dumps({"id": rtr_id}),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/resources/external-routers/{rtr_id}",
        resp=read_fixture(fixture_path),
    )

    created = aos_logged_in.external_systems.external_router.create(
        name="example_router1", address="198.51.100.1", asn=65534
    )

    assert created == ExternalRouter(
        display_name="example_router1",
        id="example_router1",
        asn=65534,
        address="198.51.100.1",
    )
