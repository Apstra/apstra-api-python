# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
# pylint: disable=redefined-outer-name

import json
import pytest

from aos.client import AosClient
from aos.aos import AosRestAPI, AosAPIError

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


# ASN Pools
def test_asn_get_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_asn_pools.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/asn-pools",
        status=200,
        resp=read_fixture(fixture_path),
    )

    asn_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.resources.asn_pools.get_all() == asn_dict

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/asn-pools",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_asn_get_pool(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_asn_pool_id.json"
    pool_id = "test-id"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/resources/asn-pools/{pool_id}",
        status=200,
        resp=read_fixture(fixture_path),
    )

    asn_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.resources.asn_pools.get_pool(pool_id=pool_id) == asn_dict

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/resources/asn-pools/{pool_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_asn_get_pool_invalid(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_resource_id_invalid.json"
    pool_id = "test-id-invalid"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/resources/asn-pools/{pool_id}",
        status=404,
        resp=read_fixture(fixture_path),
    )

    with pytest.raises(AosAPIError):
        aos_logged_in.resources.asn_pools.get_pool(pool_id=pool_id)

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/resources/asn-pools/{pool_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_asn_add_pool(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    new_pool = {
        "display_name": "test-pool1",
        "tags": [],
        "ranges": [{"last": 2232, "first": 2222}],
        "id": "test-pool1",
    }

    aos_session.add_response(
        "POST",
        "http://aos:80/api/resources/asn-pools",
        status=202,
        resp=json.dumps({"id": "test-pool1"}),
    )

    resp = aos_logged_in.resources.asn_pools.add_pool([new_pool])
    assert resp == [{"id": new_pool["id"]}]

    aos_session.request.assert_called_once_with(
        "POST",
        "http://aos:80/api/resources/asn-pools",
        params=None,
        json=new_pool,
        headers=expected_auth_headers,
    )

def test_asn_delete(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    pool_id = 'test-pool1'

    aos_session.add_response(
        "DELETE",
        f"http://aos:80/api/resources/asn-pools/{pool_id}",
        status=202,
        resp=json.dumps({}),
    )

    assert aos_logged_in.resources.asn_pools.delete_pool([pool_id]) == [pool_id]

    aos_session.request.assert_called_once_with(
        "DELETE",
        f"http://aos:80/api/resources/asn-pools/{pool_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


# VNI Pools
def test_vni_get_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_vni_pools.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/vni-pools",
        status=200,
        resp=read_fixture(fixture_path),
    )

    asn_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.resources.vni_pools.get_all() == asn_dict

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/vni-pools",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_vni_get_pool(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_vni_pool_id.json"
    pool_id = "test-id"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/resources/vni-pools/{pool_id}",
        status=200,
        resp=read_fixture(fixture_path),
    )

    asn_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.resources.vni_pools.get_pool(pool_id=pool_id) == asn_dict

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/resources/vni-pools/{pool_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_vni_get_pool_invalid(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_resource_id_invalid.json"
    pool_id = "test-id-invalid"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/resources/vni-pools/{pool_id}",
        status=404,
        resp=read_fixture(fixture_path),
    )

    with pytest.raises(AosAPIError):
        aos_logged_in.resources.vni_pools.get_pool(pool_id=pool_id)

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/resources/vni-pools/{pool_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_vni_add_pool(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    new_pool = {
        "display_name": "test-pool1",
        "tags": [],
        "ranges": [{"last": 22000, "first": 23000}],
        "id": "test-pool1",
    }

    aos_session.add_response(
        "POST",
        "http://aos:80/api/resources/vni-pools",
        status=202,
        resp=json.dumps({"id": "test-pool1"}),
    )

    resp = aos_logged_in.resources.vni_pools.add_pool([new_pool])
    assert resp == [{"id": new_pool["id"]}]

    aos_session.request.assert_called_once_with(
        "POST",
        "http://aos:80/api/resources/vni-pools",
        params=None,
        json=new_pool,
        headers=expected_auth_headers,
    )

def test_vni_delete(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    pool_id = 'test-pool1'

    aos_session.add_response(
        "DELETE",
        f"http://aos:80/api/resources/vni-pools/{pool_id}",
        status=202,
        resp=json.dumps({}),
    )

    assert aos_logged_in.resources.vni_pools.delete_pool([pool_id]) == [pool_id]

    aos_session.request.assert_called_once_with(
        "DELETE",
        f"http://aos:80/api/resources/vni-pools/{pool_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )



# IPv4 Pools
def test_ipv4_get_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_ip_pools.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/ip-pools",
        status=200,
        resp=read_fixture(fixture_path),
    )

    asn_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.resources.ipv4_pools.get_all() == asn_dict

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/ip-pools",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_ipv4_get_pool(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_ip_pool_id.json"
    pool_id = "test-id"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/resources/ip-pools/{pool_id}",
        status=200,
        resp=read_fixture(fixture_path),
    )

    asn_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.resources.ipv4_pools.get_pool(pool_id=pool_id) == asn_dict

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/resources/ip-pools/{pool_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_ipv4_get_pool_invalid(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_resource_id_invalid.json"
    pool_id = "test-id-invalid"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/resources/ip-pools/{pool_id}",
        status=404,
        resp=read_fixture(fixture_path),
    )

    with pytest.raises(AosAPIError):
        aos_logged_in.resources.ipv4_pools.get_pool(pool_id=pool_id)

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/resources/ip-pools/{pool_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_ipv4_add_pool(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    new_pool = {
        "display_name": "test-pool1",
        "tags": [],
        "subnets": [{"network": "192.168.59.0/24"}],
        "id": "test-pool1",
    }

    aos_session.add_response(
        "POST",
        "http://aos:80/api/resources/ip-pools",
        status=202,
        resp=json.dumps({"id": "test-pool1"}),
    )

    resp = aos_logged_in.resources.ipv4_pools.add_pool([new_pool])
    assert resp == [{"id": new_pool["id"]}]

    aos_session.request.assert_called_once_with(
        "POST",
        "http://aos:80/api/resources/ip-pools",
        params=None,
        json=new_pool,
        headers=expected_auth_headers,
    )

def test_ipv4_delete(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    pool_id = 'test-pool1'

    aos_session.add_response(
        "DELETE",
        f"http://aos:80/api/resources/ip-pools/{pool_id}",
        status=202,
        resp=json.dumps({}),
    )

    assert aos_logged_in.resources.ipv4_pools.delete_pool([pool_id]) == [pool_id]

    aos_session.request.assert_called_once_with(
        "DELETE",
        f"http://aos:80/api/resources/ip-pools/{pool_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )



# IPv6 Pools
def test_ipv6_get_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_ipv6_pools.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/ipv6-pools",
        status=200,
        resp=read_fixture(fixture_path),
    )

    asn_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.resources.ipv6_pools.get_all() == asn_dict

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/ipv6-pools",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_ipv6_get_pool(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_ipv6_pool_id.json"
    pool_id = "test-id"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/resources/ipv6-pools/{pool_id}",
        status=200,
        resp=read_fixture(fixture_path),
    )

    asn_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.resources.ipv6_pools.get_pool(pool_id=pool_id) == asn_dict

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/resources/ipv6-pools/{pool_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_ipv6_get_pool_invalid(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_resource_id_invalid.json"
    pool_id = "test-id-invalid"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/resources/ipv6-pools/{pool_id}",
        status=404,
        resp=read_fixture(fixture_path),
    )

    with pytest.raises(AosAPIError):
        aos_logged_in.resources.ipv6_pools.get_pool(pool_id=pool_id)

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/resources/ipv6-pools/{pool_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_ipv6_add_pool(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    new_pool = {
        "display_name": "test-pool1",
        "tags": [],
        "subnets": [{"network": "fc01:a05:beef::/48"}],
        "id": "test-pool1",
    }

    aos_session.add_response(
        "POST",
        "http://aos:80/api/resources/ipv6-pools",
        status=202,
        resp=json.dumps({"id": "test-pool1"}),
    )

    resp = aos_logged_in.resources.ipv6_pools.add_pool([new_pool])
    assert resp == [{"id": new_pool["id"]}]

    aos_session.request.assert_called_once_with(
        "POST",
        "http://aos:80/api/resources/ipv6-pools",
        params=None,
        json=new_pool,
        headers=expected_auth_headers,
    )

def test_ipv6_delete(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    pool_id = 'test-pool1'

    aos_session.add_response(
        "DELETE",
        f"http://aos:80/api/resources/ipv6-pools/{pool_id}",
        status=202,
        resp=json.dumps({}),
    )

    assert aos_logged_in.resources.ipv6_pools.delete_pool([pool_id]) == [pool_id]

    aos_session.request.assert_called_once_with(
        "DELETE",
        f"http://aos:80/api/resources/ipv6-pools/{pool_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )
