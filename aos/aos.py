# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
import requests
from collections import namedtuple
from .utils import redacted

logger = logging.getLogger(__name__)


class AosAPIError(RuntimeError):
    pass


class AosAPIUnprocessableResponse(AosAPIError):
    pass


class AosAuthenticationError(AosAPIError):
    pass


class AosInputError(AosAPIError):
    pass


class AosAPIResourceNotFound(AosAPIError):
    pass


def err_message(resp: requests.Response) -> str:
    try:
        return resp.json().get("errors", "Unknown error")
    except (TypeError, ValueError):
        return f"{resp.text}"


AosVersion = namedtuple(
    "AosVersion", ["major", "version", "build", "minor", "full_version"]
)


class AosRestAPI:
    """
    The core class for rest api integration with AOS
    """

    default_headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    def __init__(self, protocol, host, port, session=None, verify=False):
        """

        Parameters
        ----------
        protocol
            (str) https or http connection to AOS api
        host
            (str) AOS server url or ip address
        port
            (int) AOS server port (ex 80, 443)
        session
            (obj) Established session with AOS server
        verify
            (bool)
        """
        assert protocol in ["http", "https"]

        self.protocol = protocol
        self.host = host
        self.port = port
        self.token = None

        self.session = session or requests.Session()
        self.session.verify = verify

    @property
    def base_url(self):
        return f"{self.protocol}://{self.host}:{self.port}"

    def raw_request(self, method, uri, params, data, headers):
        if headers is None:
            headers = self.default_headers.copy()
        if self.token is not None:
            headers["AuthToken"] = self.token

        resp = None
        try:
            uri = f"{self.base_url}/{uri.lstrip('/')}"

            resp = self.session.request(
                method,
                uri,
                params=params,
                json=data,
                headers=headers,
            )
        except requests.RequestException as e:
            raise AosAPIError(str(e)) from e
        finally:
            logger.debug(
                f"AosRequest<{method} {uri} params={params} json={redacted(data)} "
                f"headers={redacted(headers)}; response={resp}"
            )

        if resp.status_code == 401:
            raise AosAuthenticationError(
                f"Authentication failed: {err_message(resp)}"
            )
        elif resp.status_code >= 400:
            raise AosAPIError(err_message(resp))

        return resp

    def raw_request_json(self, method, uri, params, data, headers):
        resp = self.raw_request(method, uri, params, data, headers)

        try:
            if method == "GET" and resp.status_code == 404:
                return None
            if method == "PUT" and resp.status_code == 204:
                return None
            if resp.ok:
                return resp.json()
        except (TypeError, ValueError) as e:
            msg = (
                f"JSON deserialization failed for '{method} {uri} "
                f"params={params} data={data}'. Error {type(e)}: {e}"
            )
            logger.warning(msg)
            raise AosAPIUnprocessableResponse(msg) from e

    def try_raw_request_json(self, method, uri, params, data, headers):
        try:
            return self.raw_request_json(method, uri, params, data, headers)
        except AosAPIUnprocessableResponse:
            pass

    def json_resp_post(self, uri: str, params=None, data=None, headers=None):
        """
        AOS rest API GET using json formatted payload.
        Parameters
        ----------
        uri - (str) API endpoint ex: /api/blueprints
        params - Optional rest api parameters
        data - (json) Optional data payload
        headers - Optional rest api headers

        Returns
        -------
            (obj) - Rest Api Response object
        """
        return self.raw_request_json("POST", uri, params, data, headers)

    def put(self, uri: str, params=None, data=None, headers=None):
        """
        AOS rest API PUT.
        Parameters
        ----------
        uri - (str) API endpoint ex: /api/blueprints
        params - Optional rest api parameters
        data - (json) Optional data payload
        headers - Optional rest api headers

        Returns
        -------
            (obj) - Rest Api Response object
        """
        return self.raw_request("PUT", uri, params, data, headers)

    def json_resp_put(self, uri: str, params=None, data=None, headers=None):
        """
        AOS rest API PUT using json formatted payload.
        Parameters
        ----------
        uri - (str) API endpoint ex: /api/blueprints
        params - Optional rest api parameters
        data - (json) Optional data payload
        headers - Optional rest api headers

        Returns
        -------
            (obj) - Rest Api Response object
        """
        return self.raw_request_json("PUT", uri, params, data, headers)

    def patch(self, uri: str, params=None, data=None, headers=None):
        """
        AOS rest API PATCH using json formatted payload.
        Parameters
        ----------
        uri - (str) API endpoint ex: /api/blueprints
        params - Optional rest api parameters
        data - (json) Optional data payload
        headers - Optional rest api headers

        Returns
        -------
            (obj) - Rest Api Response object
        """
        return self.raw_request("PATCH", uri, params, data, headers)

    def json_resp_patch(self, uri: str, params=None, data=None, headers=None):
        """
        AOS rest API PATCH using json formatted payload.
        Parameters
        ----------
        uri - (str) API endpoint ex: /api/blueprints
        params - Optional rest api parameters
        data - (json) Optional data payload
        headers - Optional rest api headers

        Returns
        -------
            (obj) - Rest Api Response object
        """
        return self.raw_request_json("PATCH", uri, params, data, headers)

    def json_resp_get(self, uri: str, params=None, data=None, headers=None):
        """
        AOS rest API GET using json formatted payload.
        Parameters
        ----------
        uri - (str) API endpoint ex: /api/blueprints
        params - Optional rest api parameters
        data - (json) Optional data payload
        headers - Optional rest api headers

        Returns
        -------
            (obj) - Rest Api Response object
        """
        return self.raw_request_json("GET", uri, params, data, headers)

    def delete(self, uri, params=None, data=None, headers=None):
        return self.raw_request("DELETE", uri, params, data, headers)

    def get_aos_version(self):
        """
        Get AOS server version installed

        Returns
        -------
            (obj) - "AosVersion": ("major", "version",
                                    "build", "minor", "
                                    server_version")
        """
        v_path = "/api/version"
        server_path = "/api/versions/server"

        aos_ver = self.json_resp_get(v_path)
        server_ver = self.json_resp_get(server_path)

        return AosVersion(
            major=aos_ver["major"],
            version=aos_ver["version"],
            build=aos_ver["build"],
            minor=aos_ver["minor"],
            full_version=server_ver["version"],
        )


class AosSubsystem:
    def __init__(self, rest: AosRestAPI):
        self.rest = rest


LoginResp = namedtuple("LoginResp", ["token", "user_uuid"])


class AosAuth:
    """
    Authenticate against AOS server
    """

    def __init__(self, rest: AosRestAPI):
        self.rest = rest

    def login(self, username: str, password: str) -> LoginResp:
        """

        Parameters
        ----------
        username
        password

        Returns
        -------
            (obj) Session token
        """
        resp = self.rest.json_resp_post(
            "/api/aaa/login", data={"username": username, "password": password}
        )
        self.rest.token = resp["token"]

        return LoginResp(token=resp["token"], user_uuid=resp["id"])

    def change_password(
        self, user_uuid: str, current_password: str, new_password: str
    ) -> None:
        """

        Parameters
        ----------
        user_uuid
            (str) AOS uuid of user
        current_password
            (str) Current password of AOS user
        new_password
            (str) New password of AOS user

        Returns
        -------
            (obj) New session token
        """
        self.rest.json_resp_put(
            f"/api/aaa/users/{user_uuid}/change-password",
            data={
                "current_password": current_password,
                "new_password": new_password,
                "new_password2": new_password,
            },
        )
