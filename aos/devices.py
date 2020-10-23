# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
from collections import namedtuple
from typing import List, Generator
from .aos import AosSubsystem

logger = logging.getLogger(__name__)

SystemAgent = namedtuple("SystemAgent", ["id", "fqdn", "operation_mode", "vendor"])
Anomaly = namedtuple("Anomaly", ["type", "id", "agent_id", "severity"])
DevicePackage = namedtuple("Package", ["name", "version"])
DeviceOSImage = namedtuple(
    "DeviceOsImage",
    ["description", "checksum", "image_name", "platform", "image_url", "type", "id"],
)


class AosDevices(AosSubsystem):
    """
    Management of AOS managed device and system-agents:
    - Managed Devices
    - System Agents
    - Device Profiles
    """
    def __init__(self, rest):
        self.managed_devices = AosManagedDevices(rest)
        self.system_agents = AosSystemAgents(rest)
        self.device_profiles = AosDeviceProfiles(rest)


class AosManagedDevices(AosSubsystem):
    """
    Management of system-agent for AOS controlled devices
    """

    def accept_running_config_as_golden(self, system_agent_id: str):
        """
        Accept current running configuration of device as AOS golden config
        Parameters
        ----------
        system_agent_id
            (str) ID of system_agent

        Returns
        -------

        """
        self.rest.json_resp_post(
            f"/api/systems/{system_agent_id}/accept-running-config-as-golden"
        )

    def get_all(self) -> List[SystemAgent]:
        """
        Return all system-agents configured in AOS
        Returns
        -------
            (obj) "SystemAgent", ["id", "fqdn", "operation_mode", "vendor"]
        """
        systems = self.rest.json_resp_get("/api/systems")
        if systems is None:
            return []

        return [
            SystemAgent(
                id=s["id"],
                fqdn=s.get("status", {}).get("fqdn"),
                operation_mode=s.get("status", {}).get("operation_mode"),
                vendor=s.get("facts", {}).get("vendor"),
            )
            for s in systems["items"]
        ]

    def iter_anomalies(self, system_agent_id: str) -> Generator[Anomaly, None, None]:
        anomalies = self.rest.json_resp_get(
            f"api/systems/{system_agent_id}/anomalies"
        )
        if anomalies is None:
            return

        for anomaly in anomalies["items"]:
            yield Anomaly(
                type=anomaly["anomaly_type"],
                id=anomaly["id"],
                agent_id=anomaly.get("identity", {}).get("system_id"),
                severity=anomaly["severity"],
            )

    def get_anomalies(self, system_agent_id: str) -> List[Anomaly]:
        """
        Return list of all anomalies and errors for a specific device
        Parameters
        ----------
        system_agent_id
            (str) ID of system_agent

        Returns
        -------
            (obj) ["Anomaly", ["type", "id", "agent_id", "severity"], ...]
        """
        return list(self.iter_anomalies(system_agent_id))

    def has_anomalies(self, system_agent_id: str) -> bool:
        """
        Returns True if given device has anomalies or errors.
        False if none are returned
        Parameters
        ----------
        system_agent_id
            (str) ID of system_agent
        Returns
        -------
            (bool) True or False
        """
        return self.get_anomalies(system_agent_id) != []

    def has_anomalies_of_type(self, system_agent_id: str, anomaly_type: str) -> bool:
        """
        Returns True if an anomaly of a specific type is returned for the
        specified device. False if none are returned
        Parameters
        ----------
        system_agent_id
            (str) ID of system_agent
        anomaly_type
            (str) Type of anomaly to filter on
        Returns
        -------
            (bool) True or False
        """
        for anomaly in self.iter_anomalies(system_agent_id):
            if anomaly.type == anomaly_type:
                return True
        return False


class AosSystemAgents(AosSubsystem):
    """
    Management of system-agent for AOS controlled devices
    """

    def get_packages(self):
        """
        Get a list of all device packages imported into AOS
        """
        p_path = "/api/packages"

        resp = self.rest.json_resp_get(p_path)

        return [
            DevicePackage(name=package["name"], version=package["version"])
            for package in resp["items"]
        ]

    def get_os_images(self):
        """
        Get a list of all OS images imported into AOS
        """
        p_path = "/api/device-os/images"

        resp = self.rest.json_resp_get(p_path)

        return [
            DeviceOSImage(
                description=image["description"],
                checksum=image["checksum"],
                image_name=image["image_name"],
                platform=image["platform"],
                image_url=image["image_url"],
                type=image["type"],
                id=image["id"],
            )
            for image in resp["items"]
        ]


class AosDeviceProfiles(AosSubsystem):
    """
    Manage AOS device profiles.
    This does not apply the resource to a rack type, template or
    existing blueprint. See `aos.rack_type`, `aos.template` or `aos.blueprint`
    to apply to the respective resource.
    """
    def get_device_profiles(self):
        """
        Return all device profiles configured from AOS

        Returns
        -------
            (obj) json response
        """
        dp_path = '/api/device-profiles'
        return self.rest.json_resp_get(dp_path)
