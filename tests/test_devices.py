# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
# pylint: disable=redefined-outer-name

import json

import pytest

from aos.client import AosClient
from aos.aos import AosAPIError, AosRestAPI
from aos.devices import Anomaly, SystemAgent, DevicePackage, DeviceOSImage

from tests.util import make_session, read_fixture


@pytest.fixture(params=["3.2.1"])
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


def test_system_agent_get_all(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    aos = aos_logged_in.devices.managed_devices
    aos_session.add_response(
        "GET",
        "http://aos:80/api/systems",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/system_agents/list.json"),
    )

    assert aos.get_all() == [
        SystemAgent(
            id="525400F03ECE",
            fqdn="leaf2",
            operation_mode="full_control",
            vendor="Cumulus",
        ),
        SystemAgent(
            id="5254008E9D94",
            fqdn="leaf1",
            operation_mode="full_control",
            vendor="Cumulus",
        ),
        SystemAgent(
            id="5254005162A2",
            fqdn="spine2",
            operation_mode="full_control",
            vendor="Cumulus",
        ),
        SystemAgent(
            id="505400B45628",
            fqdn="leaf3",
            operation_mode="full_control",
            vendor="Arista",
        ),
        SystemAgent(
            id="52540006FE33",
            fqdn="spine1",
            operation_mode="full_control",
            vendor="Cumulus",
        ),
    ]
    aos_session.request.assert_called_once_with(
        "GET",
        "http://aos:80/api/systems",
        params=None,
        json=None,
        headers=expected_auth_headers,
    )


def test_system_agent_anomalies(
    aos_logged_in, aos_session, expected_auth_headers, aos_api_version
):
    aos = aos_logged_in.devices.managed_devices
    system_id = "system_id"
    aos_session.add_response(
        "GET",
        f"http://aos:80/api/systems/{system_id}/anomalies",
        status=200,
        resp=read_fixture(f"aos/{aos_api_version}/system_agents/anomalies.json"),
    )

    assert aos.get_anomalies(system_id) == [
        Anomaly(
            type="config",
            id="aa6723a7-5f8c-40af-a486-5f16d0b9ea6c",
            agent_id="505400B45628",
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
        resp=read_fixture(f"aos/{aos_api_version}/system_agents/anomalies.json"),
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
