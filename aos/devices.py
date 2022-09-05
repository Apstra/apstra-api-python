# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
import time
from collections import namedtuple
from dataclasses import dataclass
from typing import List, Generator, Optional
from .aos import AosSubsystem, AosAPIError

logger = logging.getLogger(__name__)


@dataclass
class Anomaly:
    type: str
    id: str
    system_id: str
    severity: str

    @classmethod
    def from_json(cls, anomaly: dict):
        if anomaly is None:
            return NullAnomaly
        return Anomaly(
            type=anomaly["anomaly_type"],
            id=anomaly["id"],
            system_id=anomaly.get("identity", {}).get("system_id"),
            severity=anomaly["severity"],
        )


NullAnomaly = Anomaly(type="", id="", system_id="", severity="")


DevicePackage = namedtuple("Package", ["name", "version"])
DeviceOSImage = namedtuple(
    "DeviceOsImage",
    ["description", "checksum", "image_name", "platform", "image_url", "type", "id"],
)


@dataclass
class System:
    id: str
    container_status: dict
    device_key: str
    facts: dict
    services: list
    status: dict
    user_config: dict

    @classmethod
    def from_json(cls, d: Optional[dict]):
        if d is None:
            return NullSystem
        return System(
            id=d["id"],
            container_status=d.get("container_status", {}),
            device_key=d["device_key"],
            facts=d["facts"],
            services=d.get("services", []),
            status=d["status"],
            user_config=d.get("user_config", {}),
        )


NullSystem = System(
    id="",
    container_status={},
    device_key="",
    facts={},
    services=[],
    status={},
    user_config={},
)


@dataclass
class SystemAgent:
    agent_uuid: str
    management_ip: str
    operation_mode: str
    platform: str
    system_id: str
    hostname: str = None
    username: str = None
    password: str = None
    is_offbox: bool = False

    @classmethod
    def from_json(cls, s: dict):
        if s is None:
            return NullSystemAgent
        config = s.get("config", {})
        device_facts = s.get("device_facts", {})
        status = s.get("status", {})

        return SystemAgent(
            agent_uuid=s["id"],
            hostname=device_facts.get("hostname"),
            is_offbox=config.get("agent_type", "onbox") == "offbox",
            management_ip=config.get("management_ip"),
            operation_mode=status.get("operation_mode"),
            # AOS 3.2.1 keeps platform in "status", while 3.3.0+ - in config
            platform=config.get("platform") or status.get("platform"),
            system_id=status.get("system_id"),
        )

    def telemetry_only(self) -> bool:
        return self.operation_mode == "telemetry_only"


NullSystemAgent = SystemAgent(
    agent_uuid="",
    hostname="",
    is_offbox=False,
    management_ip="",
    operation_mode="",
    platform="",
    system_id="",
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
    Management of AOS controlled devices
    """

    def accept_running_config_as_golden(self, system_id: str):
        self.rest.json_resp_post(
            f"/api/systems/{system_id}/accept-running-config-as-golden"
        )

    def get_all(self) -> List[System]:
        return list(self.iter_all())

    def iter_all(self) -> Generator[System, None, None]:
        systems = self.rest.json_resp_get("/api/systems")

        for s in systems.get("items", []):
            yield System.from_json(s)

    def get_system_by_id(self, system_id: str) -> Optional[System]:
        return System.from_json(self.rest.json_resp_get(f"/api/systems/{system_id}"))

    def iter_anomalies(self, system_id: str) -> Generator[Anomaly, None, None]:
        anomalies = self.rest.json_resp_get(f"api/systems/{system_id}/anomalies")
        if anomalies is None:
            return

        for anomaly in anomalies["items"]:
            yield Anomaly.from_json(anomaly)

    def get_anomalies(self, system_id: str) -> List[Anomaly]:
        return list(self.iter_anomalies(system_id))

    def has_anomalies(self, system_id: str) -> bool:
        return self.get_anomalies(system_id) != []

    def has_anomalies_of_type(self, system_id: str, anomaly_type: str) -> bool:
        for anomaly in self.iter_anomalies(system_id):
            if anomaly.type == anomaly_type:
                return True
        return False

    def find_system_with_ip(self, ip_addr: str) -> Optional[System]:
        for system in self.iter_all():
            if system.facts["mgmt_ipaddr"] == ip_addr:
                return system
        return NullSystem

    def delete(self, agent_uuid: str) -> None:
        self.rest.delete(f"/api/system-agents/{agent_uuid}")

    def get_by_id(self, agent_uuid: str) -> Optional[SystemAgent]:
        resp = self.rest.json_resp_get(f"/api/system-agents/{agent_uuid}")
        if resp:
            return SystemAgent.from_json(resp)


class AosSystemAgents(AosSubsystem):
    """
    Management of system-agent for AOS controlled devices
    """

    def create_system_agent(self, data) -> bool:
        return self.rest.json_resp_post("/api/system-agents", data=data)

    def get_all(self) -> List[SystemAgent]:
        return list(self.iter_all())

    def iter_all(self) -> Generator[SystemAgent, None, None]:
        system_agents = self.rest.json_resp_get("/api/system-agents")

        for s in system_agents.get("items", []):
            yield SystemAgent.from_json(s)

    def get_agent_by_id(self, system_id: str) -> Optional[SystemAgent]:
        return SystemAgent.from_json(
            self.rest.json_resp_get(f"/api/system-agents/{system_id}")
        )

    def find_agent_with_ip(self, ip_addr: str) -> Optional[SystemAgent]:
        for agent in self.iter_all():
            if agent.management_ip == ip_addr:
                return agent
        return NullSystemAgent

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

    def create(
        self,
        management_ip: str,
        label: str,
        username: str,
        password: str,
        platform: Optional[str] = None,
        telemetry_only: bool = False,
        is_offbox: bool = False,
    ) -> str:
        """
        Creates system agent in AOS.
        Parameters
        ----------
        management_ip
            (str) management IP address for system
        label
            (str) unique device identifier or name
        username
            (str) username for authentication on target device
        password
            (str) password for authentication on target device
        platform
            (str) (optional) system platform of target device can be one of:
            [junos, nxos, eos]
            Only applicable to offbox agents, ignored for onbox agents.
            default: None
        telemetry_only
            (bool) (optional) AOS agent operation mode, Default sets agent
            to full_control
            default: False
        is_offbox
            (bool) (optional) setup offbox agent instead of directly on target device
            default: False
        Return
        ------
        UUID of created system agent
        """
        sys_agent = {
            "agent_type": "offbox" if is_offbox else "onbox",
            "job_on_create": "check",
            "management_ip": management_ip,
            "label": label,
            "open_options": {},
            "operation_mode": (
                "telemetry_only" if telemetry_only else "full_control"
            ),
            "password": password,
            "username": username,
        }

        if is_offbox:
            sys_agent["platform"] = platform

        resp = self.rest.json_resp_post("/api/system-agents", data=sys_agent)
        return resp["id"]


class AosDeviceProfiles(AosSubsystem):
    """
    Manage AOS device profiles.
    This does not apply the resource to a rack type, template or
    existing blueprint. See `aos.rack_type`, `aos.template` or `aos.blueprint`
    to apply to the respective resource.
    """

    def get_all(self):
        """
        Return all device profiles configured from AOS

        Returns
        -------
            (obj) json response
        """
        dp_path = "/api/device-profiles"
        return self.rest.json_resp_get(dp_path)

    def get_device_profile(self, dp_id: str = None, dp_name: str = None):
        """
        Return an existing rack type by id or name
        Parameters
        ----------
        dp_id
            (str) ID of AOS external router (optional)
        dp_name
            (str) Name or label of AOS external router (optional)


        Returns
        -------
            (obj) json response
        """

        if dp_name:
            dev_profs = self.get_all()
            if dev_profs:
                for dp in dev_profs:
                    if dp.get("display_name") == dp_name:
                        return dp
                raise AosAPIError(f"External Router {dp_name} not found")

        return self.rest.json_resp_get(f"/api/device-profiles/{dp_id}")

    def add_device_profiles(self, dp_list):
        """
        Add one or more device profiles to AOS

        Parameters
        ----------
        dp_list
            (list) - list of json payloads

        Returns
        -------
            (list) device profile IDs
        """
        p_path = "/api/device-profiles"

        ids = []
        i = 0
        while i < len(dp_list):
            resp = self.rest.json_resp_post(uri=p_path, data=dp_list[i])
            if resp:
                ids.append(resp["id"])
            i += 1
            if i % 30 == 0:
                time.sleep(3)

        return ids

    def delete_device_profiles(self, dp_list: str):
        """
        Delete one or more device profiles from AOS

        Parameters
        ----------
        dp_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/device-profiles"

        ids = []
        for dp_id in dp_list:
            self.rest.delete(f"{p_path}/{dp_id}")
            ids.append(dp_id)

        return ids
