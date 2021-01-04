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


# Logical Devices
def test_logical_devices_get_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_logical_devices.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/design/logical-devices",
        status=200,
        resp=read_fixture(fixture_path),
    )

    ld_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.design.logical_devices.get_all() == ld_dict["items"]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/design/logical-devices",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_logical_devices_get_ld(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_logical_device_id.json"
    ld_id = "AOS-7x10-Leaf"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/logical-devices/{ld_id}",
        status=200,
        resp=read_fixture(fixture_path),
    )

    ld_dict = deserialize_fixture(fixture_path)

    assert (
        aos_logged_in.design.logical_devices.get_logical_device(ld_id=ld_id)
        == ld_dict
    )

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/design/logical-devices/{ld_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_logical_devices_ld_invalid(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_invalid_ld.json"
    ld_id = "test-id-invalid"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/logical-devices/{ld_id}",
        status=422,
        resp=read_fixture(fixture_path),
    )

    with pytest.raises(AosAPIError):
        aos_logged_in.design.logical_devices.get_logical_device(ld_id=ld_id)

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/design/logical-devices/{ld_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_logical_devices_add_ld(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    fixture_path = f"aos/{aos_api_version}/design/get_logical_device_id.json"
    ld_dict = deserialize_fixture(fixture_path)

    aos_session.add_response(
        "POST",
        "http://aos:80/api/design/logical-devices",
        status=202,
        resp=json.dumps({"id": "AOS-7x10-Leaf"}),
    )

    resp = aos_logged_in.design.logical_devices.add_logical_device([ld_dict])
    assert resp == [{"id": ld_dict["id"]}]

    aos_session.request.assert_called_once_with(
        "POST",
        "http://aos:80/api/design/logical-devices",
        params=None,
        json=ld_dict,
        headers=expected_auth_headers,
    )


def test_logical_devices_delete(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    ld_id = "AOS-7x10-Leaf"

    aos_session.add_response(
        "DELETE",
        f"http://aos:80/api/design/logical-devices/{ld_id}",
        status=202,
        resp=json.dumps({}),
    )

    assert aos_logged_in.design.logical_devices.delete_logical_device([ld_id]) == [
        ld_id
    ]

    aos_session.request.assert_called_once_with(
        "DELETE",
        f"http://aos:80/api/design/logical-devices/{ld_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


# Rack Types
def test_rack_types_get_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_rack_types.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/design/rack-types",
        status=200,
        resp=read_fixture(fixture_path),
    )

    rt_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.design.rack_types.get_all() == rt_dict["items"]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/design/rack-types",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_rack_types_get_rt(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_rack_type_id.json"
    rt_id = "evpn-single"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/rack-types/{rt_id}",
        status=200,
        resp=read_fixture(fixture_path),
    )

    rt_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.design.rack_types.get_rack_type(rt_id=rt_id) == rt_dict

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/design/rack-types/{rt_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_rack_types_ld_invalid(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_invalid.json"
    rt_id = "test-id-invalid"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/rack-types/{rt_id}",
        status=404,
        resp=read_fixture(fixture_path),
    )

    with pytest.raises(AosAPIError):
        aos_logged_in.design.rack_types.get_rack_type(rt_id=rt_id)

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/design/rack-types/{rt_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_rack_types_add_rt(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    fixture_path = f"aos/{aos_api_version}/design/get_rack_type_id.json"
    rt_dict = deserialize_fixture(fixture_path)

    aos_session.add_response(
        "POST",
        "http://aos:80/api/design/rack-types",
        status=202,
        resp=json.dumps({"id": "evpn-single"}),
    )

    resp = aos_logged_in.design.rack_types.add_rack_type([rt_dict])
    assert resp == [{"id": rt_dict["id"]}]

    aos_session.request.assert_called_once_with(
        "POST",
        "http://aos:80/api/design/rack-types",
        params=None,
        json=rt_dict,
        headers=expected_auth_headers,
    )


def test_rack_types_delete(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    rt_id = "evpn-single"

    aos_session.add_response(
        "DELETE",
        f"http://aos:80/api/design/rack-types/{rt_id}",
        status=202,
        resp=json.dumps({}),
    )

    assert aos_logged_in.design.rack_types.delete_rack_type([rt_id]) == [rt_id]

    aos_session.request.assert_called_once_with(
        "DELETE",
        f"http://aos:80/api/design/rack-types/{rt_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


# Rack Types
def test_templates_get_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_templates.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/design/templates",
        status=200,
        resp=read_fixture(fixture_path),
    )

    temp_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.design.templates.get_all() == temp_dict["items"]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/design/templates",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_templates_get_template(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_template_id.json"
    temp_id = "evpn-single"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/templates/{temp_id}",
        status=200,
        resp=read_fixture(fixture_path),
    )

    temp_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.design.templates.get_template(temp_id=temp_id) == temp_dict

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/design/templates/{temp_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_templates_ld_invalid(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_invalid.json"
    temp_id = "test-id-invalid"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/templates/{temp_id}",
        status=404,
        resp=read_fixture(fixture_path),
    )

    with pytest.raises(AosAPIError):
        aos_logged_in.design.templates.get_template(temp_id=temp_id)

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/design/templates/{temp_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_templates_add_template(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    fixture_path = f"aos/{aos_api_version}/design/get_template_id.json"
    temp_dict = deserialize_fixture(fixture_path)

    aos_session.add_response(
        "POST",
        "http://aos:80/api/design/templates",
        status=202,
        resp=json.dumps({"id": "lab_evpn_mlag"}),
    )

    resp = aos_logged_in.design.templates.add_template([temp_dict])
    assert resp == [{"id": temp_dict["id"]}]

    aos_session.request.assert_called_once_with(
        "POST",
        "http://aos:80/api/design/templates",
        params=None,
        json=temp_dict,
        headers=expected_auth_headers,
    )


def test_templates_delete(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    temp_id = "lab_evpn_mlag"

    aos_session.add_response(
        "DELETE",
        f"http://aos:80/api/design/templates/{temp_id}",
        status=202,
        resp=json.dumps({}),
    )

    assert aos_logged_in.design.templates.delete_templates([temp_id]) == [temp_id]

    aos_session.request.assert_called_once_with(
        "DELETE",
        f"http://aos:80/api/design/templates/{temp_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


# Configlets
def test_configlets_get_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_configlets.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/design/configlets",
        status=200,
        resp=read_fixture(fixture_path),
    )

    conf_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.design.configlets.get_all() == conf_dict["items"]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/design/configlets",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_configlets_get_configlet(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_configlet_id.json"
    conf_id = "ntp_configlet"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/configlets/{conf_id}",
        status=200,
        resp=read_fixture(fixture_path),
    )

    conf_dict = deserialize_fixture(fixture_path)

    assert (
        aos_logged_in.design.configlets.get_configlet(conf_id=conf_id) == conf_dict
    )

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/design/configlets/{conf_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_configlets_ld_invalid(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_invalid.json"
    conf_id = "test-id-invalid"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/configlets/{conf_id}",
        status=404,
        resp=read_fixture(fixture_path),
    )

    with pytest.raises(AosAPIError):
        aos_logged_in.design.configlets.get_configlet(conf_id=conf_id)

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/design/configlets/{conf_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_configlets_add_configlet(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    fixture_path = f"aos/{aos_api_version}/design/get_configlet_id.json"
    conf_dict = deserialize_fixture(fixture_path)

    aos_session.add_response(
        "POST",
        "http://aos:80/api/design/configlets",
        status=202,
        resp=json.dumps({"id": "ntp_configlet"}),
    )

    resp = aos_logged_in.design.configlets.add_configlet([conf_dict])
    assert resp == [{"id": conf_dict["id"]}]

    aos_session.request.assert_called_once_with(
        "POST",
        "http://aos:80/api/design/configlets",
        params=None,
        json=conf_dict,
        headers=expected_auth_headers,
    )


def test_configlets_delete(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    conf_id = "ntp_configlet"

    aos_session.add_response(
        "DELETE",
        f"http://aos:80/api/design/configlets/{conf_id}",
        status=202,
        resp=json.dumps({}),
    )

    assert aos_logged_in.design.configlets.delete_configlet([conf_id]) == [conf_id]

    aos_session.request.assert_called_once_with(
        "DELETE",
        f"http://aos:80/api/design/configlets/{conf_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


# Configlets
def test_property_sets_get_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_property_sets.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/property-sets",
        status=200,
        resp=read_fixture(fixture_path),
    )

    ps_dict = deserialize_fixture(fixture_path)

    assert aos_logged_in.design.property_sets.get_all() == ps_dict["items"]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/property-sets",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_property_sets_get_ps(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_configlet_id.json"
    ps_id = "b9b1c7ee-205e-406c-8155-57ad3ece8a1f"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/property-sets/{ps_id}",
        status=200,
        resp=read_fixture(fixture_path),
    )

    ps_dict = deserialize_fixture(fixture_path)

    assert (
        aos_logged_in.design.property_sets.get_property_set(ps_id=ps_id) == ps_dict
    )

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/property-sets/{ps_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_property_sets_ld_invalid(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_invalid.json"
    ps_id = "test-id-invalid"

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/property-sets/{ps_id}",
        status=404,
        resp=read_fixture(fixture_path),
    )

    with pytest.raises(AosAPIError):
        aos_logged_in.design.property_sets.get_property_set(ps_id=ps_id)

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/property-sets/{ps_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_property_sets_add_ps(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):

    fixture_path = f"aos/{aos_api_version}/design/get_property_set_id.json"
    ps_dict = deserialize_fixture(fixture_path)
    ps_id = "b9b1c7ee-205e-406c-8155-57ad3ece8a1f"

    aos_session.add_response(
        "POST",
        "http://aos:80/api/property-sets",
        status=202,
        resp=json.dumps({"id": ps_id}),
    )

    resp = aos_logged_in.design.property_sets.add_property_set([ps_dict])
    assert resp == [{"id": ps_dict["id"]}]

    aos_session.request.assert_called_once_with(
        "POST",
        "http://aos:80/api/property-sets",
        params=None,
        json=ps_dict,
        headers=expected_auth_headers,
    )


def test_property_sets_delete(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    ps_id = "b9b1c7ee-205e-406c-8155-57ad3ece8a1f"

    aos_session.add_response(
        "DELETE",
        f"http://aos:80/api/property-sets/{ps_id}",
        status=202,
        resp=json.dumps({}),
    )

    assert aos_logged_in.design.property_sets.delete_property_set([ps_id]) == [ps_id]

    aos_session.request.assert_called_once_with(
        "DELETE",
        f"http://aos:80/api/property-sets/{ps_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )
