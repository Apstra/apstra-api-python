# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
# pylint: disable=redefined-outer-name

import json
import pytest

from aos.client import AosClient
from aos.aos import AosRestAPI
from aos.resources import Range, PoolSubnet, AsnPool, IPPool, VniPool

from tests.util import make_session, read_fixture


@pytest.fixture(params=["3.3.0", "4.0.0"])
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
def test_asn_pool_iter_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_asn_pools.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/asn-pools",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert list(aos_logged_in.resources.asn_pools.iter_all()) == [
        AsnPool(
            display_name="Private-4200000000-4294967294",
            id="Private-4200000000-4294967294",
            ranges=[Range(first=4200000000, last=4294967294)],
        ),
        AsnPool(
            display_name="Private-64512-65534",
            id="Private-64512-65534",
            ranges=[Range(first=64512, last=65534)],
        ),
        AsnPool(
            display_name="test",
            id="1358b68b-9505-4641-82a1-8e350dc49576",
            ranges=[Range(first=100, last=1000), Range(first=5000, last=10000)],
        ),
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/asn-pools",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_find_asn_pool_by_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_asn_pools.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/asn-pools",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert aos_logged_in.resources.asn_pools.find_by_name("test") == [
        AsnPool(
            display_name="test",
            id="1358b68b-9505-4641-82a1-8e350dc49576",
            ranges=[Range(first=100, last=1000), Range(first=5000, last=10000)],
        ),
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/asn-pools",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_asn_pool_create(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_asn_pool_id.json"
    pool_id = "asn_pool_uuid"

    aos_session.add_response(
        "POST",
        "http://aos:80/api/resources/asn-pools",
        status=202,
        resp=json.dumps({"id": pool_id}),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/resources/asn-pools/{pool_id}",
        resp=read_fixture(fixture_path),
    )

    created = aos_logged_in.resources.asn_pools.create(
        "test", [Range(1000, 2000), Range(5000, 6000)]
    )

    assert created == AsnPool(
        display_name="test",
        ranges=[Range(1000, 2000), Range(5000, 6000)],
        id=pool_id,
    )


# VNI Pools
def test_vni_pool_iter_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_vni_pools.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/vni-pools",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert list(aos_logged_in.resources.vni_pools.iter_all()) == [
        VniPool(
            display_name="Default-10000-20000",
            id="Default-10000-20000",
            ranges=[Range(first=10000, last=20000)],
        ),
        VniPool(
            display_name="evpn-vni",
            id="evpn-vni",
            ranges=[Range(first=5000, last=5500)],
        ),
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/vni-pools",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_find_vni_pool_by_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_vni_pools.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/vni-pools",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert aos_logged_in.resources.vni_pools.find_by_name("evpn-vni") == [
        VniPool(
            display_name="evpn-vni",
            id="evpn-vni",
            ranges=[Range(first=5000, last=5500)],
        )
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/vni-pools",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_vni_pool_create(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_vni_pool_id.json"
    pool_id = "test-pool"

    aos_session.add_response(
        "POST",
        "http://aos:80/api/resources/vni-pools",
        status=202,
        resp=json.dumps({"id": pool_id}),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/resources/vni-pools/{pool_id}",
        resp=read_fixture(fixture_path),
    )

    created = aos_logged_in.resources.vni_pools.create(
        "test-pool", [Range(10000, 20000)]
    )

    assert created == VniPool(
        display_name="test-pool",
        ranges=[Range(10000, 20000)],
        id=pool_id,
    )


# IPv4 Pools
def test_ipv4_pool_iter_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_ip_pools.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/ip-pools",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert list(aos_logged_in.resources.ipv4_pools.iter_all()) == [
        IPPool(
            display_name="spine-leaf",
            id="adb5641b-3182-4092-bcc4-85c49befe122",
            subnets=[PoolSubnet(network="10.10.0.0/22")],
        ),
        IPPool(
            display_name="virtual-networks",
            id="e772e121-594c-48dc-a801-5a17f643c237",
            subnets=[PoolSubnet(network="10.30.40.0/21")],
        ),
        IPPool(
            display_name="leaf-loopback",
            id="2f278c1b-78bd-4b6f-8aef-052e984a9fa7",
            subnets=[PoolSubnet(network="10.20.30.0/24")],
        ),
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/ip-pools",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_find_ipv4_pool_by_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_ip_pools.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/ip-pools",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert aos_logged_in.resources.ipv4_pools.find_by_name("spine-leaf") == [
        IPPool(
            display_name="spine-leaf",
            id="adb5641b-3182-4092-bcc4-85c49befe122",
            subnets=[PoolSubnet(network="10.10.0.0/22")],
        )
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/ip-pools",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_ipv4_pool_create(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_ip_pool_id.json"
    pool_id = "spine-leaf"

    aos_session.add_response(
        "POST",
        "http://aos:80/api/resources/ip-pools",
        status=202,
        resp=json.dumps({"id": pool_id}),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/resources/ip-pools/{pool_id}",
        resp=read_fixture(fixture_path),
    )

    created = aos_logged_in.resources.ipv4_pools.create(
        "spine-leaf", ["10.10.0.0/22"]
    )

    assert created == IPPool(
        display_name="spine-leaf",
        id=pool_id,
        subnets=[PoolSubnet(network="10.10.0.0/22")],
    )


# IPv6 Pools
def test_ipv6_pool_iter_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_ipv6_pools.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/ipv6-pools",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert list(aos_logged_in.resources.ipv6_pools.iter_all()) == [
        IPPool(
            display_name="Private-fc01:a05:fab::/48",
            id="Private-fc01-a05-fab-48",
            subnets=[PoolSubnet(network="fc01:a05:fab::/48")],
        ),
        IPPool(
            display_name="evpn-ipv6-pool",
            id="580d287c-b0c6-49a8-89b6-fce94f69dfc1",
            subnets=[PoolSubnet(network="fc01:a11:abc::/48")],
        ),
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/ipv6-pools",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_find_ipv6_pool_by_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_ipv6_pools.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/ipv6-pools",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert aos_logged_in.resources.ipv6_pools.find_by_name("evpn-ipv6-pool") == [
        IPPool(
            display_name="evpn-ipv6-pool",
            id="580d287c-b0c6-49a8-89b6-fce94f69dfc1",
            subnets=[PoolSubnet(network="fc01:a11:abc::/48")],
        )
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/resources/ipv6-pools",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_ipv6_pool_create(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/resources/get_ipv6_pool_id.json"
    pool_id = "evpn-ipv6-pool"

    aos_session.add_response(
        "POST",
        "http://aos:80/api/resources/ipv6-pools",
        status=202,
        resp=json.dumps({"id": pool_id}),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/resources/ipv6-pools/{pool_id}",
        resp=read_fixture(fixture_path),
    )

    created = aos_logged_in.resources.ipv6_pools.create(
        "evpn-ipv6-pool", ["fc01:a11:abc::/48"]
    )

    assert created == IPPool(
        display_name="evpn-ipv6-pool",
        id="580d287c-b0c6-49a8-89b6-fce94f69dfc1",
        subnets=[PoolSubnet(network="fc01:a11:abc::/48")],
    )
