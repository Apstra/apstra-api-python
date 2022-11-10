# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
from dataclasses import dataclass
from typing import Optional, List, Generator, Dict

from .aos import AosSubsystem, AosAPIError
from aos.repeat import repeat_until

logger = logging.getLogger(__name__)


class AosDesign(AosSubsystem):
    """
    Management of AOS design elements:
    - Logical Devices
    - Interface Maps
    - Rack Types
    - Templates
    - Configlets
    - Property Sets
    - TCP/UDP Ports
    """

    def __init__(self, rest):
        super().__init__(rest)
        self.logical_devices = AosLogicalDevices(rest)
        self.interface_maps = AosInterfaceMap(rest)
        self.rack_types = AosRackType(rest)
        self.templates = AosTemplate(rest)
        self.configlets = AosConfiglets(rest)
        self.property_sets = AosPropertySets(rest)


@dataclass
class Design:
    display_name: str
    id: str


class AosLogicalDevices(AosSubsystem):
    """
    Manage AOS Logical Devices.
    This does not apply the logical device to a blueprint
    Use `blueprint.apply_configlet` to apply to blueprint
    """

    def get_all(self):
        """
        Return all logical devices configured from AOS

        Returns
        -------
            (obj) json response
        """
        ld_path = "/api/design/logical-devices"
        resp = self.rest.json_resp_get(ld_path)
        return resp["items"]

    def get_logical_device(self, ld_id: str = None, ld_name: str = None):
        """
        Return an existing logical device by id or name
        Parameters
        ----------
        ld_id
            (str) ID of AOS logical device (optional)
        ld_name
            (str) Name or label of AOS logical device (optional)


        Returns
        -------
            (obj) json response
        """

        if ld_name:
            log_dev = self.get_all()
            if log_dev:
                for ld in log_dev:
                    if ld.get("display_name") == ld_name:
                        return ld
                raise AosAPIError(f"Logical Device {ld_name} not found")

        return self.rest.json_resp_get(f"/api/design/logical-devices/{ld_id}")

    def add_logical_device(self, ld_list: list):
        """
        Add one or more logical devices to AOS

        Parameters
        ----------
        ld_list
            (list) - list of json payloads

        Returns
        -------
            (list) logical device IDs
        """
        p_path = "/api/design/logical-devices"

        ids = []
        for ld in ld_list:
            item_id = self.rest.json_resp_post(uri=p_path, data=ld)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_logical_device(self, ld_list: str):
        """
        Delete one or more logical devices from AOS

        Parameters
        ----------
        ld_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/design/logical-devices"

        ids = []
        for ld_id in ld_list:
            self.rest.delete(f"{p_path}/{ld_id}")
            ids.append(ld_id)

        return ids


@dataclass
class InterfaceMap(Design):
    device_profile_id: str
    interfaces: list
    logical_device_id: str
    label: str

    @classmethod
    def from_json(cls, d):
        if d is None:
            return None
        return InterfaceMap(
            id=d["id"],
            device_profile_id=d.get("device_profile_id"),
            interfaces=d.get("interfaces"),
            logical_device_id=d.get("logical_device_id"),
            label=d.get("label", ""),
            display_name=d.get("label"),
        )


class AosInterfaceMap(AosSubsystem):
    def create(self, interface_map: dict) -> InterfaceMap:

        im_data = {
            "id": interface_map.get("id", None),
            "device_profile_id": interface_map["device_profile_id"],
            "interfaces": interface_map["interfaces"],
            "logical_device_id": interface_map["logical_device_id"],
            "label": interface_map["label"],
        }

        created = self.rest.json_resp_post(
            "/api/design/interface-maps", data=im_data
        )
        return self.get(created["id"])

    def delete(self, im_id: str) -> None:
        self.rest.delete(f"/api/design/interface-maps/{im_id}")

    def get(self, im_id: str) -> Optional[InterfaceMap]:
        return InterfaceMap.from_json(
            self.rest.json_resp_get(f"/api/design/interface-maps/{im_id}")
        )

    def iter_all(self) -> Generator[InterfaceMap, None, None]:
        ims = self.rest.json_resp_get("/api/design/interface-maps")
        if ims:
            for i in ims["items"]:
                yield InterfaceMap.from_json(i)

    def find_by_name(self, im_name: str) -> List[InterfaceMap]:
        return [i for i in self.iter_all() if i.label == im_name]


@dataclass
class RackType(Design):
    description: str
    leafs: list
    logical_devices: list
    access_switches: list
    generic_systems: list
    servers: list

    @classmethod
    def from_json(cls, d):
        if d is None:
            return None
        return RackType(
            id=d["id"],
            display_name=d.get("display_name", ""),
            description=d.get("description"),
            leafs=d.get("leafs"),
            logical_devices=d.get("logical_devices"),
            access_switches=d.get("access_switches"),
            generic_systems=d.get("generic_systems"),
            servers=d.get("servers"),
        )

    def to_json(self):
        return {
            "id": self.id,
            "display_name": self.display_name,
            "description": self.description,
            "leafs": self.leafs,
            "logical_devices": self.logical_devices,
            "access_switches": self.access_switches,
            "generic_systems": self.generic_systems,
            "servers": self.servers,
        }


class AosRackType(AosSubsystem):
    def get_all(self) -> Dict:
        """
        Return all rack types configured from AOS

        Returns
        -------
            (dict) json response
        """
        t_path = "/api/design/rack-types"
        resp = self.rest.json_resp_get(t_path)
        return resp["items"]

    def create(self, rack_type: dict) -> RackType:
        rt_data = {
            "display_name": rack_type["display_name"],
            "id": rack_type.get("id", None),
            "description": rack_type["description"],
            "leafs": rack_type["leafs"],
            "logical_devices": rack_type["logical_devices"],
            "access_switches": rack_type["access_switches"],
            # New in 4.4.0
            "generic_systems": rack_type.get("generic_systems"),
            "fabric_connectivity_design": rack_type.get(
                "fabric_connectivity_design"
            ),
        }

        created = self.rest.json_resp_post("/api/design/rack-types", data=rt_data)
        return self.get(created["id"])

    def delete(self, rack_type_id: str) -> None:
        self.rest.delete(f"/api/design/rack-types/{rack_type_id}")

    def delete_sync(self, rack_type_id: str, timeout: int = 60) -> None:
        self.delete(rack_type_id)
        repeat_until(lambda: self.get(rack_type_id) is None, timeout=timeout)

    def get(self, rt_id: str) -> Optional[RackType]:
        return RackType.from_json(
            self.rest.json_resp_get(f"/api/design/rack-types/{rt_id}")
        )

    def iter_all(self) -> Generator[RackType, None, None]:
        rts = self.rest.json_resp_get("/api/design/rack-types")
        if rts:
            for r in rts["items"]:
                yield RackType.from_json(r)

    def find_by_name(self, rt_name: str) -> List[RackType]:
        return [r for r in self.iter_all() if r.display_name == rt_name]


@dataclass
class Template(Design):
    external_routing_policy: dict
    virtual_network_policy: dict
    fabric_addressing_policy: dict
    spine: dict
    rack_type_counts: list
    dhcp_service_intent: dict
    rack_types: list
    asn_allocation_policy: dict
    type: str

    @classmethod
    def from_json(cls, d):
        if d is None:
            return None
        return Template(
            id=d["id"],
            display_name=d.get("display_name", ""),
            external_routing_policy=d.get("external_routing_policy"),
            virtual_network_policy=d.get("virtual_network_policy"),
            fabric_addressing_policy=d.get("fabric_addressing_policy"),
            spine=d.get("spine"),
            rack_type_counts=d.get("rack_type_counts"),
            dhcp_service_intent=d.get("dhcp_service_intent"),
            rack_types=d.get("rack_types"),
            asn_allocation_policy=d.get("asn_allocation_policy"),
            type=d.get("type"),
        )


class AosTemplate(AosSubsystem):
    def create(self, template: dict) -> Template:

        temp_data = {
            "display_name": template["display_name"],
            "id": template.get("id", None),
            "external_routing_policy": template["external_routing_policy"],
            "virtual_network_policy": template["virtual_network_policy"],
            "fabric_addressing_policy": template["fabric_addressing_policy"],
            "spine": template["spine"],
            "rack_type_counts": template["rack_type_counts"],
            "dhcp_service_intent": template["dhcp_service_intent"],
            "rack_types": template["rack_types"],
            "asn_allocation_policy": template["asn_allocation_policy"],
            "type": template["type"],
        }

        created = self.rest.json_resp_post("/api/design/templates", data=temp_data)
        return self.get(created["id"])

    def delete(self, template_id: str) -> None:
        self.rest.delete(f"/api/design/templates/{template_id}")

    def delete_sync(self, template_id: str, timeout: int = 60) -> None:
        self.delete(template_id)
        repeat_until(lambda: self.get(template_id) is None, timeout=timeout)

    def get(self, template_id: str) -> Optional[Template]:
        return Template.from_json(
            self.rest.json_resp_get(f"/api/design/templates/{template_id}")
        )

    def iter_all(self) -> Generator[Template, None, None]:
        temps = self.rest.json_resp_get("/api/design/templates")
        if temps:
            for t in temps["items"]:
                yield Template.from_json(t)

    def find_by_name(self, template_name: str) -> List[Template]:
        return [t for t in self.iter_all() if t.display_name == template_name]


class AosConfiglets(AosSubsystem):
    """
    Manage AOS configlets.
    This does not apply the configlet to a blueprint
    Use `blueprint.apply_configlet` to apply to blueprint
    """

    def get_all(self):
        """
        Return all configlets configured from AOS

        Returns
        -------
            (obj) json response
        """
        t_path = "/api/design/configlets"
        resp = self.rest.json_resp_get(t_path)
        return resp["items"]

    def get_configlet(self, conf_id: str = None, conf_name: str = None):
        """
        Return an existing configlet by id or name
        Parameters
        ----------
        conf_id
            (str) ID of AOS configlet (optional)
        conf_name
            (str) Name or label of AOS configlet (optional)


        Returns
        -------
            (obj) json response
        """

        if conf_name:
            configlets = self.get_all()
            if configlets:
                for configlet in configlets:
                    if configlet.get("display_name") == conf_name:
                        return configlet
                raise AosAPIError(f"Configlet {conf_name} not found")

        return self.rest.json_resp_get(f"/api/design/configlets/{conf_id}")

    def add_configlet(self, conf_list):
        """
        Add one or more vni pools to AOS

        Parameters
        ----------
        conf_list
            (list) - list of json payloads

        Returns
        -------
            (list) configlet IDs
        """
        p_path = "/api/design/configlets"

        ids = []
        for conf in conf_list:
            item_id = self.rest.json_resp_post(uri=p_path, data=conf)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_configlet(self, conf_list: str):
        """
        Delete one or more configlets from AOS

        Parameters
        ----------
        conf_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/design/configlets"

        ids = []
        for conf_id in conf_list:
            self.rest.delete(f"{p_path}/{conf_id}")
            ids.append(conf_id)

        return ids


class AosPropertySets(AosSubsystem):
    """
    Manage AOS property-set.
    This does not apply the property-set to a blueprint
    Use `blueprint.apply_property_set` to apply to blueprint
    """

    def get_all(self):
        """
        Return all property sets configured from AOS

        Returns
        -------
            (obj) json response
        """
        ps_path = "/api/property-sets"
        resp = self.rest.json_resp_get(ps_path)
        return resp["items"]

    def get_property_set(self, ps_id: str = None, ps_name: str = None):
        """
        Return an existing property set by id or name
        Parameters
        ----------
        ps_id
            (str) ID of AOS property set (optional)
        ps_name
            (str) Name or label of AOS property set (optional)


        Returns
        -------
            (obj) json response
        """

        if ps_name:
            property_sets = self.get_all()
            if property_sets:
                for ps in property_sets:
                    if ps.get("label") == ps_name:
                        return ps
                raise AosAPIError(f"Property set {ps_name} not found")

        return self.rest.json_resp_get(f"/api/property-sets/{ps_id}")

    def add_property_set(self, ps_list):
        """
        Add one or more vni pools to AOS

        Parameters
        ----------
        ps_list
            (list) - list of json payloads

        Returns
        -------
            (list) property set IDs
        """
        p_path = "/api/property-sets"

        ids = []
        for ps in ps_list:
            item_id = self.rest.json_resp_post(uri=p_path, data=ps)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_property_set(self, ps_list: str):
        """
        Delete one or more property sets from AOS

        Parameters
        ----------
        ps_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/property-sets"

        ids = []
        for ps_id in ps_list:
            self.rest.delete(f"{p_path}/{ps_id}")
            ids.append(ps_id)

        return ids
