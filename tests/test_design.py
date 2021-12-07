# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
# pylint: disable=redefined-outer-name

import json
import pytest
from unittest import mock

from aos.client import AosClient
from aos.aos import AosRestAPI, AosAPIError
from aos.design import RackType, Template, InterfaceMap

from tests.util import make_session, read_fixture, deserialize_fixture


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


# Rack-types
def test_rack_type_iter_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_rack_types.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/design/rack-types",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert list(aos_logged_in.design.rack_types.iter_all()) == [
        RackType(
            id="evpn-mlag",
            display_name="evpn-mlag",
            description="",
            leafs=mock.ANY,
            logical_devices=mock.ANY,
            access_switches=mock.ANY,
            generic_systems=mock.ANY,
            servers=mock.ANY,
        ),
        RackType(
            id="evpn-single",
            display_name="evpn-single",
            description="",
            leafs=mock.ANY,
            logical_devices=mock.ANY,
            access_switches=mock.ANY,
            generic_systems=mock.ANY,
            servers=mock.ANY,
        ),
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/design/rack-types",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_find_rack_type_by_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_rack_types.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/design/rack-types",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert aos_logged_in.design.rack_types.find_by_name("evpn-single") == [
        RackType(
            id="evpn-single",
            display_name="evpn-single",
            description="",
            leafs=mock.ANY,
            logical_devices=mock.ANY,
            access_switches=mock.ANY,
            generic_systems=mock.ANY,
            servers=mock.ANY,
        ),
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/design/rack-types",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_rack_type_create(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_rack_type_id.json"
    rt_id = "test-id"

    aos_session.add_response(
        "POST",
        "http://aos:80/api/design/rack-types",
        status=202,
        resp=json.dumps({"id": rt_id}),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/rack-types/{rt_id}",
        resp=read_fixture(fixture_path),
    )

    rt = deserialize_fixture(fixture_path)

    created = aos_logged_in.design.rack_types.create(rt)

    if aos_api_version.startswith("4"):
        gs = rt["generic_systems"]
    else:
        gs = None

    assert created == RackType(
        id="evpn-single",
        display_name="evpn-single",
        description=rt["description"],
        leafs=rt["leafs"],
        logical_devices=rt["logical_devices"],
        access_switches=rt["access_switches"],
        generic_systems=gs,
        servers=rt["servers"],
    )


# Templates
def test_templates_iter_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_templates.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/design/templates",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert list(aos_logged_in.design.templates.iter_all()) == [
        Template(
            id="lab_evpn_mlag",
            display_name="lab_evpn_mlag",
            external_routing_policy=mock.ANY,
            virtual_network_policy=mock.ANY,
            fabric_addressing_policy=mock.ANY,
            spine=mock.ANY,
            rack_type_counts=mock.ANY,
            dhcp_service_intent=mock.ANY,
            rack_types=mock.ANY,
            asn_allocation_policy=mock.ANY,
            type="rack_based",
        ),
        Template(
            id="pod1",
            display_name="L2 Pod External",
            external_routing_policy=mock.ANY,
            virtual_network_policy=mock.ANY,
            fabric_addressing_policy=mock.ANY,
            spine=mock.ANY,
            rack_type_counts=mock.ANY,
            dhcp_service_intent=mock.ANY,
            rack_types=mock.ANY,
            asn_allocation_policy=mock.ANY,
            type="rack_based",
        ),
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/design/templates",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_find_templates_by_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_templates.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/design/templates",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert aos_logged_in.design.templates.find_by_name("lab_evpn_mlag") == [
        Template(
            id="lab_evpn_mlag",
            display_name="lab_evpn_mlag",
            external_routing_policy=mock.ANY,
            virtual_network_policy=mock.ANY,
            fabric_addressing_policy=mock.ANY,
            spine=mock.ANY,
            rack_type_counts=mock.ANY,
            dhcp_service_intent=mock.ANY,
            rack_types=mock.ANY,
            asn_allocation_policy=mock.ANY,
            type="rack_based",
        ),
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/design/templates",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_templates_create(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_template_id.json"
    t_id = "test-id"

    aos_session.add_response(
        "POST",
        "http://aos:80/api/design/templates",
        status=202,
        resp=json.dumps({"id": t_id}),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/templates/{t_id}",
        resp=read_fixture(fixture_path),
    )

    t = deserialize_fixture(fixture_path)

    created = aos_logged_in.design.templates.create(t)

    assert created == Template(
        id="lab_evpn_mlag",
        display_name="lab_evpn_mlag",
        external_routing_policy=t["external_routing_policy"],
        virtual_network_policy=t["virtual_network_policy"],
        fabric_addressing_policy=t["fabric_addressing_policy"],
        spine=t["spine"],
        rack_type_counts=t["rack_type_counts"],
        dhcp_service_intent=t["dhcp_service_intent"],
        rack_types=t["rack_types"],
        asn_allocation_policy=t["asn_allocation_policy"],
        type="rack_based",
    )


# Interface-Maps
def test_interface_map_iter_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_ims.json"

    aos_session.add_response(
        "GET",
        "http://aos:80/api/design/interface-maps",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert list(aos_logged_in.design.interface_maps.iter_all()) == [
        InterfaceMap(
            id="Arista_vEOS__slicer-7x10-1",
            display_name="Arista_vEOS__slicer-7x10-1",
            device_profile_id="Arista_vEOS",
            interfaces=mock.ANY,
            logical_device_id="slicer-7x10-1",
            label="Arista_vEOS__slicer-7x10-1",
        ),
        InterfaceMap(
            id="Cumulus_VX__slicer-7x10-1",
            display_name="Cumulus_VX__slicer-7x10-1",
            device_profile_id="Cumulus_VX",
            interfaces=mock.ANY,
            logical_device_id="slicer-7x10-1",
            label="Cumulus_VX__slicer-7x10-1",
        ),
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/design/interface-maps",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_find_interface_map_by_name(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_ims.json"
    im_name = "Arista_vEOS__slicer-7x10-1"
    aos_session.add_response(
        "GET",
        "http://aos:80/api/design/interface-maps",
        status=200,
        resp=read_fixture(fixture_path),
    )

    assert aos_logged_in.design.interface_maps.find_by_name(im_name) == [
        InterfaceMap(
            id="Arista_vEOS__slicer-7x10-1",
            display_name="Arista_vEOS__slicer-7x10-1",
            device_profile_id="Arista_vEOS",
            interfaces=mock.ANY,
            logical_device_id="slicer-7x10-1",
            label="Arista_vEOS__slicer-7x10-1",
        )
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/design/interface-maps",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_interface_map_create(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    fixture_path = f"aos/{aos_api_version}/design/get_im_id.json"
    im_id = "test-id"

    aos_session.add_response(
        "POST",
        "http://aos:80/api/design/interface-maps",
        status=202,
        resp=json.dumps({"id": im_id}),
    )
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/design/interface-maps/{im_id}",
        resp=read_fixture(fixture_path),
    )

    im = deserialize_fixture(fixture_path)

    created = aos_logged_in.design.interface_maps.create(im)

    assert created == InterfaceMap(
        id="Arista_vEOS__slicer-7x10-1",
        display_name="Arista_vEOS__slicer-7x10-1",
        device_profile_id="Arista_vEOS",
        interfaces=im["interfaces"],
        logical_device_id="slicer-7x10-1",
        label="Arista_vEOS__slicer-7x10-1",
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
