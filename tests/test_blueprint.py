# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
# pylint: disable=redefined-outer-name

import json

import pytest
from unittest import mock
from unittest.mock import call

from aos.client import AosClient
from aos.aos import AosRestAPI, AosAPIError, AosInputError
from aos.blueprint import (
    Blueprint,
    Device,
    AosBPCommitError,
    Anomaly,
    SecurityZone,
    VirtualNetwork,
)

from requests.utils import requote_uri
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


def test_add_bp_by_temp_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    template_name = "lab_evpn_mlag"
    bp_body = {
        "design": "two_stage_l3clos",
        "init_type": "template_reference",
        "label": "test-bp",
        "template_id": template_name,
    }
    bp_resp = {"id": "test-bp", "task_id": "test-bp"}

    aos_session.add_response(
        "GET",
        "http://aos:80/api/design/templates",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/design/get_templates.json"),
    )
    aos_session.add_response(
        "POST",
        "http://aos:80/api/blueprints/",
        status=201,
        resp=json.dumps(bp_resp),
    )

    resp = aos_logged_in.blueprint.add_blueprint(
        label="test-bp", template_name=template_name
    )
    assert resp == bp_resp

    aos_session.request.assert_called_with(
        "POST",
        "http://aos:80/api/blueprints/",
        params=None,
        json=bp_body,
        headers=expected_auth_headers,
    )


def test_add_bp_by_temp_name_invalid(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    template_name = "test-name-bad"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/design/templates",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/design/get_templates.json"),
    )

    with pytest.raises(AosInputError):
        aos_logged_in.blueprint.add_blueprint(
            label="test-bp", template_name=template_name
        )

    aos_session.request.assert_called_with(
        "GET",
        "http://aos:80/api/design/templates",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_add_bp_by_temp_id(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    template_id = "lab_evpn_mlag"
    bp_body = {
        "design": "two_stage_l3clos",
        "init_type": "template_reference",
        "label": "test-bp",
        "template_id": template_id,
    }
    bp_resp = {"id": "test-bp", "task_id": "test-bp"}

    aos_session.add_response(
        "POST",
        "http://aos:80/api/blueprints/",
        status=201,
        resp=json.dumps(bp_resp),
    )

    resp = aos_logged_in.blueprint.add_blueprint(
        label="test-bp", template_id=template_id
    )
    assert resp == bp_resp

    aos_session.request.assert_called_with(
        "POST",
        "http://aos:80/api/blueprints/",
        params=None,
        json=bp_body,
        headers=expected_auth_headers,
    )


def test_add_bp_by_temp_id_invalid(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    template_id = "1111-bad-id"
    bp_body = {
        "design": "two_stage_l3clos",
        "init_type": "template_reference",
        "label": "test-bp",
        "template_id": template_id,
    }
    bp_resp = {"errors": {"template_id": "Design template not found: template_id"}}

    aos_session.add_response(
        "POST",
        "http://aos:80/api/blueprints/",
        status=422,
        resp=json.dumps(bp_resp),
    )

    with pytest.raises(AosAPIError):
        aos_logged_in.blueprint.add_blueprint(
            label="test-bp", template_id=template_id
        )

    aos_session.request.assert_called_with(
        "POST",
        "http://aos:80/api/blueprints/",
        params=None,
        json=bp_body,
        headers=expected_auth_headers,
    )


# TODO (Ryan): Parameterize all resource_type and group_name options
def test_assign_asn_pool_to_bp(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    bp_id = "evpn-cvx-virtual"
    resource_type = "asn"
    group_name = "spine_asns"
    asn_pool_id = "evpn-asn"

    aos_session.add_response(
        "PUT",
        f"http://aos:80/api/blueprints/{bp_id}/resource_groups/"
        f"{resource_type}/{group_name}",
        status=202,
        resp=json.dumps(""),
    )

    assert (
        aos_logged_in.blueprint.apply_resource_groups(
            bp_id=bp_id,
            resource_type=resource_type,
            group_name=group_name,
            pool_ids=[asn_pool_id],
        )
        == ""
    )

    rg_body = {
        "pool_ids": [asn_pool_id],
    }

    aos_session.request.assert_called_once_with(
        "PUT",
        f"http://aos:80/api/blueprints/{bp_id}/resource_groups/"
        f"{resource_type}/{group_name}",
        params=None,
        json=rg_body,
        headers=expected_auth_headers,
    )


def test_commit_staging_errors(
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
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/errors",
        status=202,
        resp=read_fixture(f"aos/{aos_api_version}/blueprints/bp_errors_active.json"),
    )

    with pytest.raises(AosBPCommitError):
        aos_logged_in.blueprint.commit_staging(bp_id, "test_test")
        aos_session.request.assert_called_with(
            "PUT",
            f"http://aos:80/api/blueprints/{bp_id}/deploy",
            params=None,
            json={"version": 3, "description": "test_test"},
            headers=expected_auth_headers,
        )


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
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/errors",
        status=202,
        resp=read_fixture(f"aos/{aos_api_version}/blueprints/bp_errors_clear.json"),
    )
    aos_session.add_response(
        "PUT",
        f"http://aos:80/api/blueprints/{bp_id}/deploy",
        status=202,
        resp=json.dumps(""),
    )

    aos_logged_in.blueprint.commit_staging(bp_id, "test_test")

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
            f"aos/{aos_api_version}/blueprints/get_deployed_devices_mlag.json"
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


def test_get_security_zone_id(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    sz_fixture = f"aos/{aos_api_version}/blueprints/get_security_zone_id.json"
    bp_id = "evpn-cvx-virtual"
    sz_id = "78eff7d7-e936-4e6e-a9f7-079b9aa45f98"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/security-zones/{sz_id}",
        status=200,
        resp=read_fixture(sz_fixture),
    )

    sz_dict = deserialize_fixture(sz_fixture)

    assert aos_logged_in.blueprint.get_security_zone(
        bp_id=bp_id, sz_id=sz_id
    ) == SecurityZone(
        label=sz_dict["label"],
        id=sz_id,
        routing_policy=sz_dict["routing_policy"],
        vni_id=sz_dict["vni_id"],
        sz_type=sz_dict["sz_type"],
        vrf_name=sz_dict["vrf_name"],
        rt_policy=sz_dict["rt_policy"],
        route_target=sz_dict["route_target"],
        vlan_id=sz_dict["vlan_id"],
    )

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/security-zones/{sz_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_get_security_zone_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    sz_fixture = f"aos/{aos_api_version}/blueprints/get_security_zone_id.json"
    sz_all_fixture = f"aos/{aos_api_version}/blueprints/get_security_zones.json"
    bp_id = "evpn-cvx-virtual"
    sz_name = "blue"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/security-zones",
        status=200,
        resp=read_fixture(sz_all_fixture),
    )

    sz_dict = deserialize_fixture(sz_fixture)

    assert aos_logged_in.blueprint.find_sz_by_name(
        bp_id=bp_id, name=sz_name
    ) == SecurityZone(
        label=sz_name,
        id=sz_dict["id"],
        routing_policy=sz_dict["routing_policy"],
        vni_id=sz_dict["vni_id"],
        sz_type=sz_dict["sz_type"],
        vrf_name=sz_dict["vrf_name"],
        rt_policy=sz_dict["rt_policy"],
        route_target=sz_dict["route_target"],
        vlan_id=sz_dict["vlan_id"],
    )

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/security-zones",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_create_security_zone(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    sz_fixture = f"aos/{aos_api_version}/blueprints/get_security_zone_id.json"
    all_fixture = f"aos/{aos_api_version}/blueprints/get_security_zones.json"
    bp_id = "evpn-cvx-virtual"
    sz_name = "blue"
    sz_id = "78eff7d7-e936-4e6e-a9f7-079b9aa45f98"
    resource_type = "ip"
    group_name = "leaf_loopback_ips"
    group_path = requote_uri(f"sz:{sz_id} {group_name}")
    pool_id = "leaf-loopback-pool-id"

    aos_session.add_response(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/security-zones",
        status=200,
        resp=json.dumps({"id": sz_id}),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/security-zones",
        status=200,
        resp=read_fixture(all_fixture),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/security-zones/{sz_id}",
        status=200,
        resp=read_fixture(sz_fixture),
    )
    aos_session.add_response(
        "PUT",
        f"http://aos:80/api/blueprints/{bp_id}/resource_groups/"
        f"{resource_type}/{group_path}",
        status=202,
        resp=json.dumps(""),
    )
    aos_session.add_response(
        "PUT",
        f"http://aos:80/api/blueprints/{bp_id}/security-zones/{sz_id}/dhcp-servers",
        status=204,
        resp=json.dumps(""),
    )

    resp = aos_logged_in.blueprint.create_security_zone(
        bp_id=bp_id,
        name=sz_name,
        import_policy="all",
        leaf_loopback_ip_pools=[pool_id],
        dhcp_servers=["1.1.1.1"],
    )

    sz_dict = deserialize_fixture(sz_fixture)

    assert resp == SecurityZone(
        label=sz_name,
        id=sz_dict["id"],
        routing_policy=sz_dict["routing_policy"],
        vni_id=sz_dict["vni_id"],
        sz_type=sz_dict["sz_type"],
        vrf_name=sz_dict["vrf_name"],
        rt_policy=sz_dict["rt_policy"],
        route_target=sz_dict["route_target"],
        vlan_id=sz_dict["vlan_id"],
    )


def test_get_virtual_network_id(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    vn_fixture = f"aos/{aos_api_version}/blueprints/get_virtual_network_id.json"
    bp_id = "evpn-cvx-virtual"
    vn_name = "test-blue15"
    vn_id = "307944e0-8aa5-4108-9253-0c453a653bde"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/virtual-networks/{vn_id}",
        status=200,
        resp=read_fixture(vn_fixture),
    )

    vn_dict = deserialize_fixture(vn_fixture)

    assert aos_logged_in.blueprint.get_virtual_network(
        bp_id=bp_id, vn_id=vn_id
    ) == VirtualNetwork(
        label=vn_name,
        id=vn_id,
        description=None,
        ipv4_enabled=vn_dict["ipv4_enabled"],
        ipv4_subnet=vn_dict["ipv4_subnet"],
        virtual_gateway_ipv4=vn_dict["virtual_gateway_ipv4"],
        ipv6_enabled=False,
        ipv6_subnet=None,
        virtual_gateway_ipv6=None,
        vn_id=vn_dict["vn_id"],
        security_zone_id=vn_dict["security_zone_id"],
        svi_ips=vn_dict["svi_ips"],
        virtual_mac=vn_dict["virtual_mac"],
        default_endpoint_tag_types={},
        endpoints=vn_dict["endpoints"],
        bound_to=vn_dict["bound_to"],
        vn_type=vn_dict["vn_type"],
        rt_policy=vn_dict["rt_policy"],
        dhcp_service=vn_dict["dhcp_service"],
    )
    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/virtual-networks/{vn_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_get_virtual_network_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    vn_fixture = f"aos/{aos_api_version}/blueprints/get_virtual_network_id.json"
    all_fixture = f"aos/{aos_api_version}/blueprints/get_virtual_networks.json"
    bp_id = "evpn-cvx-virtual"
    vn_name = "test-blue15"
    vn_id = "307944e0-8aa5-4108-9253-0c453a653bde"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/virtual-networks",
        status=200,
        resp=read_fixture(all_fixture),
    )

    vn_dict = deserialize_fixture(vn_fixture)

    assert aos_logged_in.blueprint.find_vn_by_name(
        bp_id=bp_id, name=vn_name
    ) == VirtualNetwork(
        label=vn_name,
        id=vn_id,
        description=None,
        ipv4_enabled=vn_dict["ipv4_enabled"],
        ipv4_subnet=vn_dict["ipv4_subnet"],
        virtual_gateway_ipv4=vn_dict["virtual_gateway_ipv4"],
        ipv6_enabled=False,
        ipv6_subnet=None,
        virtual_gateway_ipv6=None,
        vn_id=vn_dict["vn_id"],
        security_zone_id=vn_dict["security_zone_id"],
        svi_ips=vn_dict["svi_ips"],
        virtual_mac=vn_dict["virtual_mac"],
        default_endpoint_tag_types={},
        endpoints=vn_dict["endpoints"],
        bound_to=vn_dict["bound_to"],
        vn_type=vn_dict["vn_type"],
        rt_policy=vn_dict["rt_policy"],
        dhcp_service=vn_dict["dhcp_service"],
    )

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/virtual-networks",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_create_virtual_network(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    vn_fixture = f"aos/{aos_api_version}/blueprints/get_virtual_network_id.json"
    sz_all_fixture = f"aos/{aos_api_version}/blueprints/get_security_zones.json"
    bp_id = "evpn-cvx-virtual"
    sz_name = "blue"
    sz_id = "78eff7d7-e936-4e6e-a9f7-079b9aa45f98"
    vn_id = "307944e0-8aa5-4108-9253-0c453a653bde"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/security-zones",
        status=200,
        resp=read_fixture(sz_all_fixture),
    )
    aos_session.add_response(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/virtual-networks",
        status=202,
        params=None,
        resp=json.dumps({"id": vn_id}),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/virtual-networks/{vn_id}",
        status=200,
        resp=read_fixture(vn_fixture),
    )
    aos_logged_in.blueprint.create_virtual_network(
        bp_id=bp_id,
        name="blue-test1",
        bound_to=mock.ANY,
        sz_name=sz_name,
    )

    bound_to = deserialize_fixture(vn_fixture)["bound_to"]
    expected_body = {
        "label": "blue-test1",
        "security_zone_id": sz_id,
        "vn_type": "vxlan",
        "vn_id": None,
        "default_endpoint_tag_types": {
            "single-link": "vlan_tagged",
            "dual-link": "vlan_tagged",
        },
        "bound_to": bound_to,
        "ipv4_enabled": True,
        "dhcp_service": "dhcpServiceEnabled",
        "ipv4_subnet": None,
        "ipv4_gateway": None,
    }

    aos_session.request.assert_has_calls(
        [
            call(
                "POST",
                "http://aos:80/api/aaa/login",
                json=mock.ANY,
                params=None,
                headers=mock.ANY,
            ),
            call(
                "GET",
                f"http://aos:80/api/blueprints/{bp_id}/security-zones",
                params=None,
                json=None,
                headers=mock.ANY,
            ),
            call(
                "POST",
                f"http://aos:80/api/blueprints/{bp_id}/virtual-networks",
                params=None,
                json=expected_body,
                headers=mock.ANY,
            ),
            call(
                "GET",
                f"http://aos:80/api/blueprints/{bp_id}/virtual-networks/{vn_id}",
                params=None,
                json=None,
                headers=mock.ANY,
            ),
            call(
                "GET",
                f"http://aos:80/api/blueprints/{bp_id}/virtual-networks/{vn_id}",
                params=None,
                json=None,
                headers=mock.ANY,
            ),
        ]
    )


def test_apply_configlet(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    bp_id = "evpn-cvx-virtual"
    conf_id = "test-conf-id"
    conf_fixture = f"aos/{aos_api_version}/design/get_configlet_id.json"
    conf_role = ["spine", "leaf"]

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/configlets/{conf_id}",
        status=200,
        resp=read_fixture(conf_fixture),
    )

    aos_session.add_response(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/configlets",
        status=202,
        resp=json.dumps({"id": conf_id}),
    )

    resp_payload = {"id": conf_id}

    assert (
        aos_logged_in.blueprint.apply_configlet(
            bp_id=bp_id, configlet_id=conf_id, role=conf_role
        )
        == resp_payload
    )

    conf_dict = deserialize_fixture(conf_fixture)

    json_body = {
        "configlet": conf_dict,
        "label": conf_dict["display_name"],
        "condition": f"role in {conf_role}",
    }

    aos_session.request.assert_called_with(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/configlets",
        params=None,
        json=json_body,
        headers=expected_auth_headers,
    )


def test_apply_configlet_invalid_roles(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    bp_id = "evpn-cvx-virtual"
    conf_id = "test-conf-id"
    conf_fixture = f"aos/{aos_api_version}/design/get_configlet_id.json"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/configlets/{conf_id}",
        status=200,
        resp=read_fixture(conf_fixture),
    )

    with pytest.raises(AosInputError):
        aos_logged_in.blueprint.apply_configlet(bp_id=bp_id, configlet_id=conf_id)

    aos_session.request.assert_called_with(
        "GET",
        f"http://aos:80/api/design/configlets/{conf_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_apply_configlet_combined_conditions(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    bp_id = "evpn-cvx-virtual"
    conf_id = "test-conf-id"
    conf_fixture = f"aos/{aos_api_version}/design/get_configlet_id.json"
    conf_role = ["spine", "leaf"]
    conf_ids = ["foo", "bar", "monkey"]

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/configlets/{conf_id}",
        status=200,
        resp=read_fixture(conf_fixture),
    )

    aos_session.add_response(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/configlets",
        status=202,
        resp=json.dumps({"id": conf_id}),
    )

    resp_payload = {"id": conf_id}

    assert (
        aos_logged_in.blueprint.apply_configlet(
            bp_id=bp_id, configlet_id=conf_id, role=conf_role, system_id=conf_ids
        )
        == resp_payload
    )

    conf_dict = deserialize_fixture(conf_fixture)

    json_body = {
        "configlet": conf_dict,
        "label": conf_dict["display_name"],
        "condition": f"role in {conf_role} and id in {conf_ids}",
    }

    aos_session.request.assert_called_with(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/configlets",
        params=None,
        json=json_body,
        headers=expected_auth_headers,
    )


def test_apply_property_set(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    bp_id = "evpn-cvx-virtual"
    ps_id = "test-ps-id"
    ps_fixture = f"aos/{aos_api_version}/design/get_property_set_id.json"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/property-sets/{ps_id}",
        status=200,
        resp=read_fixture(ps_fixture),
    )

    aos_session.add_response(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/property-sets",
        status=202,
        resp=json.dumps({"id": ps_id}),
    )

    resp_payload = {"id": ps_id}

    assert (
        aos_logged_in.blueprint.apply_property_set(bp_id=bp_id, ps_id=ps_id)
        == resp_payload
    )

    ps_dict = deserialize_fixture(ps_fixture)

    ps_keys = []
    for k in ps_dict["values"]:
        ps_keys.append(k)

    json_body = {"keys": ps_keys, "id": ps_dict["id"]}

    aos_session.request.assert_called_with(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/property-sets",
        params=None,
        json=json_body,
        headers=expected_auth_headers,
    )


def test_apply_property_set_keys(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    bp_id = "evpn-cvx-virtual"
    ps_id = "test-ps-id"
    ps_fixture = f"aos/{aos_api_version}/design/get_property_set_id.json"
    ps_keys = ["ntp_server"]

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/property-sets/{ps_id}",
        status=200,
        resp=read_fixture(ps_fixture),
    )

    aos_session.add_response(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/property-sets",
        status=202,
        resp=json.dumps({"id": ps_id}),
    )

    resp_payload = {"id": ps_id}

    assert (
        aos_logged_in.blueprint.apply_property_set(
            bp_id=bp_id, ps_id=ps_id, ps_keys=ps_keys
        )
        == resp_payload
    )

    ps_dict = deserialize_fixture(ps_fixture)

    json_body = {"keys": ps_keys, "id": ps_dict["id"]}

    aos_session.request.assert_called_with(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/property-sets",
        params=None,
        json=json_body,
        headers=expected_auth_headers,
    )


def test_assign_interface_map_by_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    bp_id = "evpn-cvx-virtual"
    node_name = ["spine1", "spine2"]
    im_name = "Cumulus_VX__slicer-7x10-1"
    node_fixture = f"aos/{aos_api_version}/blueprints/get_bp_nodes.json"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/nodes?node_type=system",
        status=200,
        resp=read_fixture(node_fixture),
    )

    aos_session.add_response(
        "PATCH",
        f"http://aos:80/api/blueprints/{bp_id}/interface-map-assignments",
        status=204,
        resp=json.dumps({"id": im_name}),
    )

    test_json = {
        "assignments": {
            "83a3a17e-e2f1-4027-ae3c-ebf56dcfaaf5": im_name,
            "1717ee47-f0be-4877-8341-18709048e237": im_name,
        }
    }

    assert (
        aos_logged_in.blueprint.assign_interface_map_by_name(
            bp_id=bp_id, node_names=node_name, im_name=im_name
        )
        == test_json
    )

    aos_session.request.assert_called_with(
        "PATCH",
        f"http://aos:80/api/blueprints/{bp_id}/interface-map-assignments",
        params=None,
        json=test_json,
        headers=expected_auth_headers,
    )


def test_apply_external_router_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    bp_id = "evpn-cvx-virtual"
    bp_rtr_name = "example_router1"
    bp_rtr_id = "92797c82-ff36-4575-9fe2-9e84d998c7b7"
    ext_rtr_fixture = f"aos/{aos_api_version}/external_systems/get_ext_rtrs.json"
    ext_rlinks = f"aos/{aos_api_version}/blueprints/get_ext_rlinks.json"
    ext_rlinks_id = f"aos/{aos_api_version}/blueprints/get_ext_rlinks_id.json"
    bp_ext_rtr_fixture = f"aos/{aos_api_version}/blueprints/get_bp_ext_rtr.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/resources/external-routers",
        status=200,
        resp=read_fixture(ext_rtr_fixture),
    )
    aos_session.add_response(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/external-routers",
        status=200,
        resp=json.dumps({"id": bp_rtr_id}),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/external-router-links",
        status=200,
        resp=read_fixture(ext_rlinks),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/external-router-links/{bp_rtr_id}",
        status=200,
        resp=read_fixture(ext_rlinks_id),
    )
    aos_session.add_response(
        "PUT",
        f"http://aos:80/api/blueprints/{bp_id}/external-routers/{bp_rtr_id}",
        status=204,
        resp=json.dumps({"id": bp_rtr_id}),
    )
    aos_session.add_response(
        "PUT",
        f"http://aos:80/api/blueprints/{bp_id}/external-router-links/{bp_rtr_id}",
        status=204,
        resp=json.dumps({"id": bp_rtr_id}),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/external-routers/{bp_rtr_id}",
        status=200,
        resp=read_fixture(bp_ext_rtr_fixture),
    )

    resp = aos_logged_in.blueprint.apply_external_router(
        bp_id=bp_id, ext_rtr_name=bp_rtr_name
    )
    assert resp == bp_rtr_id


def test_get_anomalies_list_clear(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    bp_id = "evpn-cvx-virtual"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/anomalies",
        status=200,
        params={"exclude_anomaly_type": []},
        resp=json.dumps({"items": [], "count": 0}),
    )

    assert aos_logged_in.blueprint.anomalies_list(bp_id=bp_id) == []

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/anomalies",
        params={"exclude_anomaly_type": []},
        json=None,
        headers=expected_auth_headers,
    )


def test_get_anomalies_list(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    a_fixture = f"aos/{aos_api_version}/blueprints/bp_anomalies.json"
    bp_id = "evpn-cvx-virtual"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/anomalies",
        status=200,
        params={"exclude_anomaly_type": []},
        resp=read_fixture(a_fixture),
    )

    expected = [
        Anomaly(
            type="config",
            id="c43fcab1-0c74-4b2c-85de-c0cda9c32bd7",
            system_id="525400CFDEB3",
            severity="critical",
        )
    ]

    assert aos_logged_in.blueprint.anomalies_list(bp_id=bp_id) == expected

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/blueprints/{bp_id}/anomalies",
        params={"exclude_anomaly_type": []},
        json=None,
        headers=expected_auth_headers,
    )


def test_get_all_tor_nodes(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    node_fixture = f"aos/{aos_api_version}/blueprints/qe_get_nodes.json"
    rd_node_fixture = f"aos/{aos_api_version}/blueprints/qe_get_rd_nodes.json"
    bp_id = "evpn-cvx-virtual"
    mlag_node1 = "d704d6f7-6070-4fef-ae99-99a94e08bf62"
    mlag_node2 = "ef9b2dfb-3e12-4f73-8ec5-7c23911f3b99"
    single_node = "9e75966c-bfad-4ed1-83f9-282f552b24b2"

    aos_session.add_response(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/qe",
        status=200,
        params=None,
        resp=read_fixture(node_fixture),
    )
    aos_session.add_response(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/qe",
        status=200,
        params=None,
        resp=read_fixture(rd_node_fixture),
    )
    aos_session.add_response(
        "POST",
        f"http://aos:80/api/blueprints/{bp_id}/qe",
        status=200,
        params=None,
        resp=read_fixture(rd_node_fixture),
    )

    assert aos_logged_in.blueprint.get_all_tor_nodes(bp_id)

    aos_session.request.assert_has_calls(
        [
            call(
                "POST",
                "http://aos:80/api/aaa/login",
                json=mock.ANY,
                params=None,
                headers=mock.ANY,
            ),
            call(
                "POST",
                f"http://aos:80/api/blueprints/{bp_id}/qe",
                params=None,
                json={"query": "match(node('system', name='leaf', role='leaf'))"},
                headers=mock.ANY,
            ),
            call(
                "POST",
                f"http://aos:80/api/blueprints/{bp_id}/qe",
                params=None,
                json={
                    "query": "match(node('redundancy_group', name='rg')"
                    ".out('composed_of_systems')"
                    ".node('system', role='leaf',"
                    f" id='{mlag_node1}'))"
                },
                headers=mock.ANY,
            ),
            call(
                "POST",
                f"http://aos:80/api/blueprints/{bp_id}/qe",
                params=None,
                json={
                    "query": "match(node('redundancy_group', name='rg')"
                    ".out('composed_of_systems')"
                    ".node('system', role='leaf',"
                    f" id='{single_node}'))"
                },
                headers=mock.ANY,
            ),
            call(
                "POST",
                f"http://aos:80/api/blueprints/{bp_id}/qe",
                params=None,
                json={
                    "query": "match(node('redundancy_group', name='rg')"
                    ".out('composed_of_systems')"
                    ".node('system', role='leaf',"
                    f" id='{mlag_node2}'))"
                },
                headers=mock.ANY,
            ),
        ]
    )
