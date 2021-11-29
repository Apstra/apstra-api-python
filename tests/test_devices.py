# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
# pylint: disable=redefined-outer-name

import json

import pytest
from unittest import mock

from aos.client import AosClient
from aos.aos import AosAPIError, AosRestAPI
from aos.devices import Anomaly, System, SystemAgent, DevicePackage, DeviceOSImage

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


# Managed Devices
def test_get_managed_devices_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    aos = aos_logged_in.devices.managed_devices
    devices_all = json.loads(read_fixture(f"aos/{aos_api_version}/devices/"
                                          "get_managed_devices_all.json"))
    aos_session.add_response(
        "GET",
        "http://aos:80/api/systems",
        status=200,
        resp=json.dumps(devices_all)
    )

    devices = devices_all["items"]
    assert aos.get_all() == [
        System(id=devices[0]["id"],
               container_status=devices[0].get("container_status", {}),
               device_key=devices[0]["device_key"],
               facts=devices[0]["facts"],
               services=[],
               status=devices[0]["status"],
               user_config=devices[0]["user_config"]
               ),
        System(id=devices[1]["id"],
               container_status=devices[1].get("container_status", {}),
               device_key=devices[1]["device_key"],
               facts=devices[1]["facts"],
               services=[],
               status=devices[1]["status"],
               user_config=devices[1]["user_config"]
               ),
        System(id=devices[2]["id"],
               container_status=devices[2].get("container_status", {}),
               device_key=devices[2]["device_key"],
               facts=devices[2]["facts"],
               services=[],
               status=devices[2]["status"],
               user_config=devices[2]["user_config"]
               )
    ]

    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/systems",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_get_managed_devices_by_id(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    aos = aos_logged_in.devices.managed_devices
    test_id = "5254009E7083"
    device = json.loads(read_fixture(f"aos/{aos_api_version}/devices/"
                                     "get_managed_devices_id.json"))

    aos_session.add_response(
        "GET",
        f"http://aos:80/api/systems/{test_id}",
        status=200,
        resp=json.dumps(device)
    )

    assert aos.get_system_by_id(test_id) == System(
        id=test_id,
        container_status=device.get("container_status", {}),
        device_key=device["device_key"],
        facts=device["facts"],
        services=device["services"],
        status=device["status"],
        user_config=device["user_config"]
        )

    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/systems/{test_id}",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_accept_running_config_as_golden_posts_request(
    aos_logged_in, aos_session, expected_auth_headers
):
    aos = aos_logged_in.devices.managed_devices
    system_id = "system_id"
    aos_session.add_response(
        "POST",
        f"http://aos:80/api/systems/{system_id}/accept-running-config-as-golden",
        status=200,
        resp=json.dumps({}),
    )

    resp = aos.accept_running_config_as_golden(system_id)

    assert resp is None
    aos_session.request.assert_called_once_with(
        "POST",
        f"http://aos:80/api/systems/{system_id}/" f"accept-running-config-as-golden",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


@pytest.mark.parametrize("status", [401, 412, 422, 500])
def test_accept_running_config_as_golden_raises_exception_on_failure(
    aos_logged_in, aos_session, status, expected_auth_headers
):
    aos = aos_logged_in.devices.managed_devices
    system_id = "system_id"
    aos_session.add_response(
        "POST",
        f"http://aos:80/api/systems/{system_id}/accept-running-config-as-golden",
        status=status,
        resp=json.dumps({"errors": f"HTTP {status}"}),
    )

    with pytest.raises(AosAPIError):
        aos.accept_running_config_as_golden(system_id)
        aos_session.request.assert_called_once_with(
            "POST",
            f"http://aos:80/api/systems/{system_id}/"
            "accept-running-config-as-golden",
            params=None,
            json=None,
            headers=expected_auth_headers,
        )


def test_get_managed_device_anomalies(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    aos = aos_logged_in.devices.managed_devices
    system_id = "system_id"
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/systems/{system_id}/anomalies",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/devices/anomalies.json"),
    )

    assert aos.get_anomalies(system_id) == [
        Anomaly(
            type="config",
            id="aa6723a7-5f8c-40af-a486-5f16d0b9ea6c",
            system_id="505400B45628",
            severity="critical",
        )
    ]
    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/systems/{system_id}/anomalies",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


@pytest.mark.parametrize(
    "anomaly_type, expected", [("config", True), ("bgp", False), ("arp", False)]
)
def test_has_anomalies_of_type(
    aos_logged_in,
    aos_session,
    expected_auth_headers,
    aos_api_version,
    anomaly_type,
    expected,
):
    aos = aos_logged_in.devices.managed_devices
    system_id = "system_id"
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/systems/{system_id}/anomalies",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/devices/anomalies.json"),
    )

    has_anomalies = aos.has_anomalies_of_type(
        system_id,
        anomaly_type,
    )
    assert has_anomalies is expected
    aos_session.request.assert_called_once_with(
        "GET",
        f"http://aos:80/api/systems/{system_id}/anomalies",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


# System Agents
def test_get_system_agents_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    aos = aos_logged_in.devices.system_agents
    aos_session.add_response(
        "GET",
        "http://aos:80/api/system-agents",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/devices/"
                          f"get_sys_agents_all.json"),
    )

    assert aos.get_all() == [
        SystemAgent(
            agent_uuid='01f2057b-931b-4610-8579-4a1097ee2f32',
            management_ip='172.20.20.14',
            operation_mode='full_control',
            platform='junos',
            system_id='5254001BF851',
            hostname='evpn-single-001-leaf1',
            username=mock.ANY,
            password=mock.ANY,
            is_offbox=True
        ),
        SystemAgent(
            agent_uuid='77f8ed4e-eb6f-4378-aac0-9f5a6358a6be',
            management_ip='172.20.19.12',
            operation_mode='full_control',
            platform='cumulus',
            system_id='525400553CFC',
            hostname='spine2',
            username=mock.ANY,
            password=mock.ANY,
            is_offbox=False
        ),
        SystemAgent(
            agent_uuid='13e0de32-e99d-460b-abb8-c207b7041e8c',
            management_ip='172.20.19.14',
            operation_mode='full_control',
            platform='eos',
            system_id='505400E24540',
            hostname='leaf3',
            username=mock.ANY,
            password=mock.ANY,
            is_offbox=False
        ),
    ]
    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/system-agents",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_get_packages(aos_logged_in, aos_session, expected_auth_headers):

    aos = aos_logged_in.devices.system_agents
    package_resp = {
        "items": [
            {"version": "0.1.0", "name": "aosstdcollectors-builtin-linux"},
            {"version": "0.1.0", "name": "aosstdcollectors-custom-cumulus"},
        ]
    }

    aos_session.add_response(
        "GET",
        "http://aos:80/api/packages",
        status=200,
        resp=json.dumps(package_resp),
    )

    assert aos.get_packages() == [
        DevicePackage(
            version="0.1.0",
            name="aosstdcollectors-builtin-linux",
        ),
        DevicePackage(
            version="0.1.0",
            name="aosstdcollectors-custom-cumulus",
        ),
    ]


def test_get_packages_empty(aos_logged_in, aos_session, expected_auth_headers):

    aos = aos_logged_in.devices.system_agents
    package_resp = {"items": []}

    aos_session.add_response(
        "GET",
        "http://aos:80/api/packages",
        status=200,
        resp=json.dumps(package_resp),
    )

    assert aos.get_packages() == []


def test_get_os_images(aos_logged_in, aos_session, expected_auth_headers):

    aos = aos_logged_in.devices.system_agents
    img_resp = {
        "items": [
            {
                "description": "Testtest",
                "checksum": "string",
                "image_name": "test_os_image",
                "platform": "EOS",
                "image_url": "test_url",
                "type": "string",
                "id": "111111",
            },
            {
                "description": "Testtest2",
                "checksum": "string2",
                "image_name": "test_os_image2",
                "platform": "EOS",
                "image_url": "test_url2",
                "type": "string2",
                "id": "222222",
            },
        ]
    }

    aos_session.add_response(
        "GET",
        "http://aos:80/api/device-os/images",
        status=200,
        resp=json.dumps(img_resp),
    )

    assert aos.get_os_images() == [
        DeviceOSImage(
            description="Testtest",
            checksum="string",
            image_name="test_os_image",
            platform="EOS",
            image_url="test_url",
            type="string",
            id="111111",
        ),
        DeviceOSImage(
            description="Testtest2",
            checksum="string2",
            image_name="test_os_image2",
            platform="EOS",
            image_url="test_url2",
            type="string2",
            id="222222",
        ),
    ]


def test_get_os_images_empty(aos_logged_in, aos_session, expected_auth_headers):

    aos = aos_logged_in.devices.system_agents
    img_resp = {"items": []}

    aos_session.add_response(
        "GET",
        "http://aos:80/api/device-os/images",
        status=200,
        resp=json.dumps(img_resp),
    )

    assert aos.get_os_images() == []
