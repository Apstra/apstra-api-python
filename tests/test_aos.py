# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
# pylint: disable=redefined-outer-name

import json

import pytest

from aos.client import AosClient
from aos.aos import AosAuthenticationError, AosRestAPI, AosVersion

from tests.util import make_session


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


def test_raises_aos_api_exception_if_login_failed(aos, aos_session):
    aos_session.add_response(
        "POST",
        "http://aos:80/api/aaa/login",
        status=401,
        resp=json.dumps({"errors": "Invalid credentials"}),
    )
    with pytest.raises(AosAuthenticationError):
        aos.auth.login(username="invalid", password="invalid")


def test_login_makes_request_to_aos(aos, aos_session):
    successful_login_resp = {"token": "token", "id": "user-id"}

    aos_session.add_response(
        "POST",
        "http://aos:80/api/aaa/login",
        status=200,
        resp=json.dumps(successful_login_resp),
    )
    resp = aos.auth.login(username="user", password="pass")

    assert resp.token == "token"
    assert resp.user_uuid == "user-id"
    aos_session.request.assert_called_once_with(
        "POST",
        "http://aos:80/api/aaa/login",
        params=None,
        json={"username": "user", "password": "pass"},
        headers=aos.rest.default_headers.copy(),
    )


def test_change_password_makes_request_to_aos(
    aos_logged_in, aos_session, expected_auth_headers
):
    aos = aos_logged_in
    successful_change_password_resp = {}

    aos_session.add_response(
        "PUT",
        "http://aos:80/api/aaa/users/user-id/change-password",
        status=200,
        resp=json.dumps(successful_change_password_resp),
    )
    resp = aos.auth.change_password("user-id", "oldpass", "newpass")

    assert resp is None
    aos_session.request.assert_called_once_with(
        "PUT",
        "http://aos:80/api/aaa/users/user-id/change-password",
        params=None,
        json={
            "current_password": "oldpass",
            "new_password": "newpass",
            "new_password2": "newpass",
        },
        headers=expected_auth_headers,
    )


def test_get_aos_version(aos_logged_in, aos_session, expected_auth_headers):

    aos = aos_logged_in
    aos_ver_resp = {"major": "3", "version": "3.3.0", "build": "0", "minor": "3"}
    serv_ver_resp = {
        "version": "3.3.0-730",
        "build_datetime": "2020-08-15_02:00:23_PDT",
    }
    aos_session.add_response(
        "GET",
        "http://aos:80/api/version",
        status=200,
        resp=json.dumps(aos_ver_resp),
    )
    aos_session.add_response(
        "GET",
        "http://aos:80/api/versions/server",
        status=200,
        resp=json.dumps(serv_ver_resp),
    )

    assert aos.rest.get_aos_version() == AosVersion(
        major="3",
        version="3.3.0",
        minor="3",
        build="0",
        full_version="3.3.0-730",
    )
