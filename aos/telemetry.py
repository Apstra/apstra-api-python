# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
from dataclasses import dataclass
from typing import List

from requests import Response
from aos.aos import AosSubsystem


@dataclass
class AosTelemetryEndpointStatus:
    """
    Represent the AosTelemetry Endpoint.
    This is used to build out the Endpoint structure
    """

    connected: bool
    connection_log: List[dict]
    connection_time: str
    last_tx_time: str
    epoch: str
    connection_reset_count: int
    dns_log: List[dict]
    disconnection_time: str

    @classmethod
    def from_json(cls, d: dict) -> "AosTelemetryEndpointStatus":
        return AosTelemetryEndpointStatus(
            connected=d.get("connected"),
            connection_log=d.get("connectionLog"),
            connection_time=d.get("connectionTime"),
            last_tx_time=d.get("lastTransmitedTime"),
            epoch=d.get("epoch"),
            connection_reset_count=d.get("connectionResetCount"),
            dns_log=d.get("dnsLog"),
            disconnection_time=d.get("disconnectionTime"),
        )


@dataclass
class AosTelemetryEndpoint:
    """
    Represents the AosTelemetryEndpoint
    """

    id: str
    host: str
    port: int
    streaming_type: str
    protocol: str
    sequencing_mode: str
    ep_status: AosTelemetryEndpointStatus

    @classmethod
    def from_json(cls, d: dict) -> "AosTelemetryEndpoint":
        return AosTelemetryEndpoint(
            id=d.get("id"),
            host=d.get("host"),
            port=d.get("port"),
            streaming_type=d.get("streaming_type"),
            protocol=d.get("protocol"),
            sequencing_mode=d.get("sequencing_mode"),
            ep_status=AosTelemetryEndpointStatus.from_json(d.get("status")),
        )


class AosTelemetryManager(AosSubsystem):
    """
    Telemetry manager class used to manage the telemetry endpoints
    """

    def add_endpoint(
        self,
        host: str,
        port: int,
        streaming_type: str,
        protocol: str = "protoBufOverTcp",
        mode: str = "sequenced",
    ) -> Response:
        """
        Parameters
        ----------
        host
            (str) AOS server url or ip address
        port
            (int) AOS server port (ex 80, 443)
        streaming_type
            (str) Type of telemetry to stream (alerts/events/perfmon)
        protocol
            (str) Protocol for data default is protoBufOverTcp
        mode
            (str) sequenced/unsequenced. default is sequenced

        """
        body = {
            "hostname": host,
            "port": port,
            "streaming_type": streaming_type,
            "sequencing_mode": mode,
            "protocol": protocol,
        }
        return self.rest.json_resp_post(uri="/api/streaming-config", data=body)

    def get_endpoints(self) -> List[AosTelemetryEndpoint]:
        """
        Get the existing streaming endpoints as AosTelemetryEndpoint objects
        """
        r = self.rest.json_resp_get(uri="/api/streaming-config")
        return [AosTelemetryEndpoint.from_json(i) for i in r.get("items")]

    def delete_endpoint(self, id: str) -> Response:
        """
        Delete a single endpoint
        Parameters
        ----------
        id
            (str) id of the endpoint
        """
        return self.rest.delete(uri="/api/streaming-config/" + id)

    def delete_all_endpoints(self) -> List[bool]:
        """
        Cycle through and delete all the streaming endpoints.
        """
        eps = self.get_endpoints()
        ret = []
        for ep in eps:
            ret.append(self.delete_endpoint(ep.id))
        return True
