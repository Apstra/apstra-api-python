# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
# pylint: disable=redefined-outer-name

import json

import pytest

from aos.client import AosClient
from aos.aos import AosRestAPI, AosAPIError
from aos.blueprint import Blueprint, Device


from tests.util import make_session, read_fixture, deserialize_fixture


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


def test_get_bp_by_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    bp_name = "evpn-cvx-virtual"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/blueprints",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/blueprints/blueprints.json"),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_name}",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/blueprints/single_blueprint.json"),
    )

    resp = aos_logged_in.blueprint.get_bp(bp_name=bp_name)

    assert resp["label"] == bp_name
    assert resp["id"] == bp_name
    assert resp["design"] == "two_stage_l3clos"


def test_get_bp_by_name_invalid(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    bp_name = "BP-does-not-exist"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/blueprints",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/blueprints/blueprints.json"),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_name}",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/blueprints/single_blueprint.json"),
    )

    with pytest.raises(AosAPIError):
        aos_logged_in.blueprint.get_bp(bp_name=bp_name)


def test_get_bp_by_id(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    bp_id = "evpn-cvx-virtual"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/blueprints",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/blueprints/blueprints.json"),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/blueprints/single_blueprint.json"),
    )

    resp = aos_logged_in.blueprint.get_bp(bp_id=bp_id)

    assert resp["label"] == bp_id
    assert resp["id"] == bp_id
    assert resp["design"] == "two_stage_l3clos"


def test_get_bp_by_id_invalid(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    bp_id = "BP-does-not-exist"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/blueprints",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/blueprints/blueprints.json"),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}",
        status=404,
        resp=read_fixture(f"aos/{aos_api_version}/blueprints/blueprint_404.json"),
    )

    with pytest.raises(AosAPIError):
        aos_logged_in.blueprint.get_bp(bp_id=bp_id)


def test_commit_staging(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    bp_id = "evpn-cvx-virtual"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/diff-status",
        status=202,
        resp=read_fixture(
            f"aos/{aos_api_version}/blueprints/bp_staging_version.json"
        ),
    )
    aos_session.add_response(
        "PUT",
        f"http://aos:80/api/blueprints/{bp_id}/deploy",
        status=202,
        resp=json.dumps(""),
    )

    assert aos_logged_in.blueprint.commit_staging(bp_id, "test_test") == ""

    aos_session.request.assert_called_with(
        "PUT",
        f"http://aos:80/api/blueprints/{bp_id}/deploy",
        params=None,
        json={"version": 3, "description": "test_test"},
        headers=expected_auth_headers,
    )


def test_get_deployed_devices(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    bp_id = "evpn-cvx-virtual"

    aos_session.add_response(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/qe",
        status=200,
        resp=read_fixture(
            f"aos/{aos_api_version}/blueprints/get_deployed_devices_devices.json"
        ),
    )
    aos_session.add_response(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/qe",
        status=200,
        resp=read_fixture(
            f"aos/{aos_api_version}/blueprints/get_deployed_devices_MLAG.json"
        ),
    )

    assert aos_logged_in.blueprint.get_deployed_devices(bp_id) == [
        Device(
            label="leaf3-leaf-switch",
            system_id="84819c8a-a402-424e-94fd-90c459f046d9",
        ),
        Device(
            label="evpn_mlag_001_leaf_pair1",
            system_id="d120c55b-4f40-4b10-8376-021fe099d632",
        ),
    ]


def test_get_security_zone(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    all_fixture = f"aos/{aos_api_version}/blueprints/get_security_zones.json"
    sz_fixture = f"aos/{aos_api_version}/blueprints/get_security_zone_id.json"
    bp_id = "evpn-cvx-virtual"
    sz_id = "78eff7d7-e936-4e6e-a9f7-079b9aa45f98"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/security-zones",
        status=200,
        resp=read_fixture(all_fixture),
    )

    sz_dict = deserialize_fixture(sz_fixture)

    assert (
        aos_logged_in.blueprint.get_security_zone(bp_id=bp_id, sz_id=sz_id)
        == sz_dict
    )

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/security-zones",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_get_virtual_network(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    all_fixture = f"aos/{aos_api_version}/blueprints/get_virtual_networks.json"
    vn_fixture = f"aos/{aos_api_version}/blueprints/get_virtual_network_id.json"
    bp_id = "evpn-cvx-virtual"
    vn_id = "678f0440-0eef-4e9a-9f59-3b69a913aef2"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/virtual-networks",
        status=200,
        resp=read_fixture(all_fixture),
    )

    vn_dict = deserialize_fixture(vn_fixture)

    assert (
        aos_logged_in.blueprint.get_virtual_network(bp_id=bp_id, vn_id=vn_id)
        == vn_dict
    )

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/virtual-networks",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )
