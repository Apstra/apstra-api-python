# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
# pylint: disable=redefined-outer-name

import json

import pytest

from aos.client import AosClient
from aos.aos import AosRestAPI, AosAPIError, AosInputError
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

    with pytest.raises(AosAPIError):
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
