# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
from enum import Enum
import json
import logging
from collections import namedtuple
from dataclasses import dataclass
from typing import Dict, Optional, List, Generator
import requests
from requests.utils import requote_uri
from .aos import AosSubsystem, AosAPIError, AosInputError, AosAPIResourceNotFound
from .design import AosConfiglets, AosPropertySets, AosTemplate
from .devices import AosDevices
from .external_systems import AosExternalRouter
from .repeat import repeat_until


logger = logging.getLogger(__name__)


class AosBPCommitError(AosAPIError):
    pass


def response(resp: Optional[requests.Response]) -> str:
    if resp is None:
        return ""
    return f"{resp.status_code} {resp.content}"


Blueprint = namedtuple("Blueprint", ["label", "id"])
Device = namedtuple("Device", ["label", "system_id"])
StagingVersion = namedtuple("Staging", ["version", "status", "deploy_error"])


class Anomaly(namedtuple("Anomaly", ["type", "id", "system_id", "severity"])):
    @classmethod
    def from_json(cls, anomaly: dict):
        return cls(
            type=anomaly["anomaly_type"],
            id=anomaly["id"],
            system_id=anomaly.get("identity", {}).get("system_id"),
            severity=anomaly["severity"],
        )


class CommitStatus(Enum):
    undeployed = "undeployed"
    in_progress = "in_progress"
    completed = "completed"
    deploying = "deploying"
    initializing = "initializing"


class TaskStatus(Enum):
    in_progress = "in_progress"
    initializing = "init"
    failed = "failed"
    succeeded = "succeeded"
    timeout = "timeout"


class VNType(Enum):
    vlan = "vlan"
    vxlan = "vxlan"


class VNTagType(Enum):
    vlan_tagged = "vlan_tagged"
    untagged = "untagged"
    unassigned = "unassigned"


@dataclass
class SecurityZone:
    label: str
    id: str
    routing_policy: dict
    routing_policy_id: str
    vni_id: str
    sz_type: str
    vrf_name: str
    rt_policy: dict
    route_target: dict
    vlan_id: int

    @classmethod
    def from_json(cls, sz: Optional[dict]):
        if sz is None:
            return NullSecurityZone
        return SecurityZone(
            label=sz.get("label", ""),
            id=sz["id"],
            routing_policy=sz.get("routing_policy", {}),
            routing_policy_id=sz.get("routing_policy_id", ""),
            vni_id=sz.get("vni_id", ""),
            sz_type=sz.get("sz_type", ""),
            vrf_name=sz.get("vrf_name", ""),
            rt_policy=sz.get("rt_policy", None),
            route_target=sz.get("route_target", None),
            vlan_id=sz.get("vlan_id", None),
        )


NullSecurityZone = SecurityZone(
    label="",
    id="",
    routing_policy={},
    routing_policy_id="",
    vni_id="",
    sz_type="",
    vrf_name="",
    rt_policy={},
    route_target={},
    vlan_id=0,
)


@dataclass
class VirtualNetwork:
    label: str
    id: str
    description: str
    ipv4_enabled: bool
    ipv4_subnet: str
    virtual_gateway_ipv4: str
    ipv6_enabled: bool
    ipv6_subnet: str
    virtual_gateway_ipv6: str
    vn_id: str
    security_zone_id: str
    svi_ips: list
    virtual_mac: str
    default_endpoint_tag_types: {}
    endpoints: list
    bound_to: list
    vn_type: str
    rt_policy: dict
    dhcp_service: str
    tagged_ct: bool
    untagged_ct: bool

    @classmethod
    def from_json(cls, vn: Optional[dict]):
        if vn is None:
            return NullVirtualNetwork
        return VirtualNetwork(
            label=vn.get("label", ""),
            id=vn["id"],
            description=vn["description"],
            ipv4_enabled=vn["ipv4_enabled"],
            ipv4_subnet=vn["ipv4_subnet"],
            virtual_gateway_ipv4=vn["virtual_gateway_ipv4"],
            ipv6_enabled=vn["ipv6_enabled"],
            ipv6_subnet=vn["ipv6_subnet"],
            virtual_gateway_ipv6=vn["virtual_gateway_ipv6"],
            vn_id=vn["vn_id"],
            security_zone_id=vn["security_zone_id"],
            svi_ips=vn.get("svi_ips", []),
            virtual_mac=vn["virtual_mac"],
            default_endpoint_tag_types=vn.get("default_endpoint_tag_types", {}),
            endpoints=vn.get("endpoints", []),
            bound_to=vn["bound_to"],
            vn_type=vn["vn_type"],
            rt_policy=vn["rt_policy"],
            dhcp_service=vn["dhcp_service"],
            tagged_ct=vn.get("create_policy_tagged", False),
            untagged_ct=vn.get("create_policy_untagged", False),
        )


NullVirtualNetwork = VirtualNetwork(
    label="",
    id="",
    description="",
    ipv4_enabled=True,
    ipv4_subnet="",
    virtual_gateway_ipv4="",
    ipv6_enabled=False,
    ipv6_subnet="",
    virtual_gateway_ipv6="",
    vn_id="",
    security_zone_id="",
    svi_ips=[],
    virtual_mac="",
    default_endpoint_tag_types={},
    endpoints=[],
    bound_to=[],
    vn_type="",
    rt_policy={},
    dhcp_service="",
    tagged_ct=False,
    untagged_ct=False,
)


@dataclass
class ResourceGroup:
    type: str
    name: str
    group_name: str
    pool_ids: list

    @classmethod
    def from_json(cls, rg: Optional[dict]):
        if rg is None:
            return NullResourceGroup

        group_name = rg["name"]
        if rg["name"].startswith("sz:"):
            group_name = rg["name"].partition(",")[2]

        return ResourceGroup(
            type=rg["type"],
            name=rg["name"],
            group_name=group_name,
            pool_ids=rg.get("pool_ids", []),
        )


NullResourceGroup = ResourceGroup(type="", name="", group_name="", pool_ids=[])


class AosBlueprint(AosSubsystem):
    """
    AOS blueprint specific actions
    """

    def get_all(self):
        """
        Return all blueprints configured
        Returns
        -------
            (obj) json object
        """

        return self.rest.json_resp_get("/api/blueprints")

    def get_all_ids(self):
        """
        Returns all blueprint names and IDs
        Returns
        -------
            (obj) "[Blueprint", ("label", "id"),...]
        """
        blueprints = self.get_all()

        return [
            Blueprint(label=bp["label"], id=bp["id"]) for bp in blueprints["items"]
        ]

    def get_id_by_name(self, label: str) -> Optional[Blueprint]:
        """
        returns blueprint id of specified blueprint by name
        Parameters
        ----------
        label
            (str) Name of AOS blueprint

        Returns
        -------
            (obj) "Blueprint", ("label", "id")
        """
        blueprints = self.get_all()

        if blueprints is not None:
            for bp in blueprints["items"]:
                if bp["label"] == label:
                    return Blueprint(label=bp["label"], id=bp["id"])

    def get_bp(self, bp_id: str = None, bp_name: str = None) -> Optional[Blueprint]:
        """
        returns blueprint by id or name

        Parameters
        ----------
        bp_id
            (str) ID of AOS blueprint (optional)
        bp_name
            (str) Name or label of AOS Blueprint (optional)

        Returns
        -------
            (obj) json object
        """

        if bp_name:
            blueprint = self.get_id_by_name(bp_name)
            if blueprint:
                bp_id = blueprint.id
            else:
                raise AosAPIError(f"Blueprint {bp_name} not found")

        return self.rest.json_resp_get(f"/api/blueprints/{bp_id}")

    def add_blueprint(self, label, template_id=None, template_name=None):
        """
        Creates new blueprint based on template. Template ID or Name required
        Parameters
        ----------
        label
            (str) Name of Blueprint
        template_id
            (str) Template ID to build blueprint from (optional)
        template_name
            (str) Template name to build blueprint from (optional)

        Returns
        -------
            (obj) json object
        """

        bp_path = "/api/blueprints/"

        if template_name:
            aos_temps = AosTemplate(self.rest)
            template = aos_temps.find_by_name(template_name)
            if len(template) > 1:
                raise AosInputError(
                    "Multiple templates with name " f"{template_name} found"
                )
            if template:
                template_id = template[0].id
            else:
                raise AosInputError(f"Template with name {template_name} not found")

        data = {
            "design": "two_stage_l3clos",
            "init_type": "template_reference",
            "label": label,
            "template_id": template_id,
        }

        return self.rest.json_resp_post(uri=bp_path, data=data)

    def delete_blueprint(self, bp_id: str):
        """
        Deletes blueprint by id
        Parameters
        ----------
        bp_id
            (str) ID of AOS blueprint

        Returns
        -------
            (obj) json object
        """

        return self.rest.delete(f"/api/blueprints/{bp_id}")

    def delete_all(self):
        """
        Deletes all AOS blueprint

        Returns
        -------
            (obj) json object
        """
        deleted_ids = []
        bp_ids = self.get_all_ids()
        if bp_ids:
            for bp in bp_ids:
                self.delete_blueprint(bp.id)
                deleted_ids.append(bp.id)

        return deleted_ids

    def anomalies(
        self, bp_id: str, exclude_anomaly_type: Optional[List[str]] = None
    ) -> Generator[Anomaly, None, None]:
        if exclude_anomaly_type is None:
            exclude_anomaly_type = []

        anomalies = self.rest.json_resp_get(
            f"/api/blueprints/{bp_id}/anomalies",
            params={"exclude_anomaly_type": exclude_anomaly_type},
        )
        for a in anomalies["items"]:
            yield Anomaly.from_json(a)

    def anomalies_list(
        self, bp_id: str, exclude_anomaly_type: Optional[List[str]] = None
    ) -> List[Anomaly]:
        """
        Return list of all active anomalies in a given blueprint.
        Parameters
        ----------
        bp_id
            (str) ID of AOS blueprint
        exclude_anomaly_type
            (list) - anomaly type to exclude from returned list

        Returns
        -------
            List[Anomaly]
        """
        return list(self.anomalies(bp_id, exclude_anomaly_type))

    def has_anomalies(self, bp_id: str) -> bool:
        """
        Returns True if blueprint has active anomalies and False if none.
        Parameters
        ----------
        bp_id
            (str) ID of AOS blueprint
        Returns
        -------
            bool
        """
        return len(self.anomalies_list(bp_id)) > 0

    # Commit, staging and rollback
    def get_build_errors(self, bp_id: str):
        """
        Returns all active build errors for a given blueprint
        Parameters
        ----------
        bp_id
            (str) ID of AOS blueprint
        Returns
        -------
            dict
        """
        return self.rest.json_resp_get(f"/api/blueprints/{bp_id}/errors")

    def has_build_errors(self, bp_id: str) -> bool:
        """
        Returns True if blueprint has active build errors and False if none.
        Parameters
        ----------
        bp_id
            (str) ID of AOS blueprint
        Returns
        -------
            bool
        """
        bp_errs = self.get_build_errors(bp_id)

        for v in bp_errs.values():
            if v:
                return True
        return False

    def is_committed(self, bp_id: str, version: int) -> bool:
        """
        Returns True if blueprint staging version has been successfully committed.
        Parameters
        ----------
        bp_id
            (str) ID of AOS blueprint
        version
            (int) version of the staging blueprint
        Returns
        -------

        """
        cpath = f"/api/blueprints/{bp_id}/diff-status"
        commit = self.rest.json_resp_get(cpath)

        if (
            commit["deployed_version"] == version
            and commit["status"] == CommitStatus.completed.value
        ):
            return True
        return False

    def commit_staging(self, bp_id: str, description: str = ""):
        """
        Deploy latest staging version of the blueprint.
        Parameters
        ----------
        bp_id
            (srt_ ID of AOS Blueprint
        description
            (str) User description of changes being made or notes (Optional)

        Returns
        -------

        """
        commit_diff_path = f"/api/blueprints/{bp_id}/diff-status"
        commit_path = f"/api/blueprints/{bp_id}/deploy"

        staging_ver = self.rest.json_resp_get(commit_diff_path)

        if staging_ver["deployed_version"] == staging_ver["staging_version"]:
            logging.info(f"No changes to commit in Blueprint {bp_id}")
            return

        if self.has_build_errors(bp_id):
            bp_errs = self.get_build_errors(bp_id)
            raise AosBPCommitError(
                f"Unable to commit Blueprint {bp_id} "
                f"due to build errors: {bp_errs}"
            )

        payload = {
            "version": int(staging_ver["staging_version"]),
            "description": description,
        }
        self.rest.put(commit_path, data=payload)

    def get_diff_status(self, bp_id: str) -> Dict:
        """
        Retrieve full diff status; useful for determining staging and deployed
        blueprint versions

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint

        Returns
        -------
            (dict) - Diff status
        """

        return self.rest.json_resp_get(f"/api/blueprints/{bp_id}/diff-status")

    # tasks
    def get_tasks(self, bp_id: str, params: dict = None) -> list:
        return self.rest.json_resp_get(
            uri=f"/api/blueprints/{bp_id}/tasks", params=params
        )["items"]

    def get_task_by_id(self, bp_id: str, task_id: str, params: dict = None) -> dict:
        return self.rest.json_resp_get(
            uri=f"/api/blueprints/{bp_id}" f"/tasks/{task_id}", params=params
        )

    def get_active_tasks(self, bp_id: str) -> list:
        resp = self.rest.json_resp_get(
            f"/api/blueprints/{bp_id}/tasks",
            params={"filter": "status in ['init', 'in_progress']"},
        )
        if resp:
            return resp["items"]
        return []

    def has_active_tasks(self, bp_id: str) -> bool:
        if self.get_active_tasks(bp_id):
            return True
        return False

    def is_task_active(self, bp_id: str, task_id: str) -> bool:
        task = self.get_task_by_id(bp_id, task_id)
        if task:
            if task["status"] in [
                TaskStatus.in_progress.value,
                TaskStatus.initializing.value,
            ]:
                return True
            else:
                return False

        else:
            raise AosAPIResourceNotFound(f"Task {task} does not exist")

    # Graph Queries
    def qe_query(self, bp_id: str, query: str, params: dict = None):
        """
        QE query aginst a Blueprint graphDB

        Parameters
        ----------
        bp_id
            (str) (optional) ID of AOS blueprint
        query
            (str) qe query string
        params
            (dict) (optional) query parameters

        Returns
        -------
            (obj) - json object
        """
        qe_path = f"/api/blueprints/{bp_id}/qe"
        data = {"query": query}
        resp = self.rest.json_resp_post(uri=qe_path, data=data, params=params)

        return resp["items"]

    def ql_query(self, bp_id: str, query: str, params: dict = None):
        """
        QL query aginst a Blueprint graphDB

        Parameters
        ----------
        bp_id
            (str) (optional) ID of AOS blueprint
        query
            (str) qe query string
        params
            (dict) (optional) query parameters

        Returns
        -------
            (obj) - json object
        """
        ql_path = f"/api/blueprints/{bp_id}/ql"
        data = {"query": query}
        resp = self.rest.json_resp_post(uri=ql_path, data=data, params=params)

        return resp["data"]

    # Resources
    def get_all_bp_resource_groups(
        self,
        bp_id: str,
    ) -> List[ResourceGroup]:
        """
        Return all resource groups required in a given blueprint.
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        Returns
        -------
        List[ResourceGroup]
        """
        rg_path = f"/api/blueprints/{bp_id}/resource_groups"
        resp = self.rest.json_resp_get(uri=rg_path)["items"]

        return [ResourceGroup.from_json(rg) for rg in resp]

    def apply_resource_groups(
        self, bp_id: str, resource_type: str, group_name: str, pool_ids: list
    ) -> ResourceGroup:
        """
        Assign existing pools to a given resource group in an AOS Blueprint
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        resource_type
            (str) type of resource pool used
            (ex: asn, vni, ip, etc)
        group_name
            (str) group to apply pool to
            (options:
                (asn): spine_asns, leaf_asns, spine_spine_asns,
                (vni): evpn_l3_vnis, vxlan_vn_ids
                (ip): spine_loopback_ips, leaf_loopback_ips,
                spine_superspine_link_ips,
                spine_leaf_link_ips, to_external_router_link_ips,
                mlag_domain_svi_subnets, vtep_ips,
                virtual_network_svi_subnets)
        pool_ids
            (list) IDs of resource pools to apply

        Returns
        -------

        """
        rg_path = (
            f"/api/blueprints/{bp_id}/resource_groups/"
            f"{resource_type}/{group_name}"
        )

        data = {
            "pool_ids": pool_ids,
        }

        self.rest.json_resp_put(uri=rg_path, data=data)
        return ResourceGroup.from_json(self.rest.json_resp_get(rg_path))

    def get_bp_resource_group(
        self, bp_id: str, resource_type: str, group_name: str
    ) -> Optional[ResourceGroup]:
        """
        Return a given resource group in an AOS Blueprint including
        the pools assigned.
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        resource_type
            (str) type of resource pool used
            (ex: asn, vni, ip, etc)
        group_name
            (str) group to apply pool to
            (options:
                (asn): spine_asns, leaf_asns, spine_spine_asns,
                (vni): evpn_l3_vnis, vxlan_vn_ids
                (ip): spine_loopback_ips, leaf_loopback_ips,
                spine_superspine_link_ips,
                spine_leaf_link_ips, to_external_router_link_ips,
                mlag_domain_svi_subnets, vtep_ips,
                virtual_network_svi_subnets)

        Returns
        -------

        """
        rg_path = (
            f"/api/blueprints/{bp_id}/resource_groups/"
            f"{resource_type}/{group_name}"
        )

        return ResourceGroup.from_json(self.rest.json_resp_get(uri=rg_path))

    # configlets, property-sets
    def get_configlets(self, bp_id: str):
        """
        Return all configlets currently imported into blueprint
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        Returns
        -------
            (dict) [{"Configlet": {...}} ...]
        """
        c_path = f"/api/blueprints/{bp_id}/configlets"
        resp = self.rest.json_resp_get(c_path)

        return resp["items"]

    def apply_configlet(
        self,
        bp_id: str,
        configlet_id: str,
        role: list = None,
        system_id: list = None,
    ):
        """
        Import and apply existing configlet to AOS Blueprint
        One of 'role' or 'system_id' is required. If role
        and system_id is provided both (AND) will be applied
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        configlet_id
            (str) ID of AOS configlet to use
        role
            (list) roles: ["spin", "leaf", "access"] (optional)

        system_id
            (list) blueprint system IDs (optional)

        Returns
        -------

        """
        c_path = f"/api/blueprints/{bp_id}/configlets"
        aos_configlets = AosConfiglets(self.rest)
        configlet = aos_configlets.get_configlet(conf_id=configlet_id)
        role_in = f"role in {role}".replace("'", '"')
        id_in = f"id in {system_id}".replace("'", '"')

        if role and system_id:
            condition = f"{role_in} and {id_in}"
        elif role:
            condition = role_in
        elif system_id:
            condition = id_in
        else:
            raise AosInputError(
                "Expected one or both conditions ['role', 'system_id']"
            )

        data = {
            "configlet": configlet,
            "label": configlet["display_name"],
            "condition": condition,
        }

        return self.rest.json_resp_post(uri=c_path, data=data)

    def get_property_set(self, bp_id: str):
        """
        Return all property-sets currently imported into blueprint
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        Returns
        -------
            (dict) [{"Configlet": {...}} ...]
        """
        p_path = f"/api/blueprints/{bp_id}/property-sets"
        resp = self.rest.json_resp_get(p_path)

        return resp["items"]

    def apply_property_set(self, bp_id: str, ps_id: str, ps_keys: list = None):
        """
        Import and apply existing property-set to AOS Blueprint
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        ps_id
            (str) ID of AOS configlet to use
        ps_keys
            (list) configured keys to apply to blueprint. If None provided all
            keys configured will be applied

        Returns
        -------

        """
        ps_path = f"/api/blueprints/{bp_id}/property-sets"
        aos_prop_set = AosPropertySets(self.rest)
        prop_set = aos_prop_set.get_property_set(ps_id=ps_id)

        prop_set_keys = []
        if ps_keys:
            prop_set_keys = ps_keys
        else:
            for k in prop_set["values"]:
                prop_set_keys.append(k)

        data = {
            "id": prop_set["id"],
            "keys": prop_set_keys,
        }

        return self.rest.json_resp_post(uri=ps_path, data=data)

    # Devices
    def get_bp_nodes(self, bp_id: str, node_type: str = None):
        if node_type:
            n_path = f"/api/blueprints/{bp_id}/nodes?node_type={node_type}"
        else:
            n_path = f"/api/blueprints/{bp_id}/nodes"

        return self.rest.json_resp_get(n_path)["nodes"]

    def get_bp_node_by_id(self, bp_id: str, node_id: str):
        return self.rest.json_resp_get(f"/api/blueprints/{bp_id}/nodes/{node_id}")

    def get_bp_system_nodes(self, bp_id: str):

        return self.get_bp_nodes(bp_id, "system")

    def set_bp_node_label(
        self, bp_id: str, node_id: str, label: str, hostname: str = ""
    ) -> None:
        """
        Sets a node's label (and optionally, its hostname)
        Parameters
        ----------
        bp_id
             (str) - ID of AOS Blueprint
        node_id
            (str) - ID of node within blueprint to update
        label
            (str) - Value for updating node label
        hostname
            (str) - Optional value to also update hostname

        Returns
        -------
        """

        data = {
            "label": label,
        }
        if hostname:
            data["hostname"] = hostname
        self.rest.patch(f"/api/blueprints/{bp_id}/nodes/{node_id}", data=data)

    def get_deployed_devices(self, bp_id: str):
        """
        Return all AOS managed devices deployed in the given blueprint

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint

        Returns
        -------
            (obj) - json object
        """
        devices = []
        d_query = (
            "match(node('system', role='leaf', name='system')"
            ".having(node(name='system')"
            ".out('part_of_redundancy_group')"
            ".node('redundancy_group'),at_most=0,))"
        )
        mlag_query = (
            "match(node('redundancy_group', name='system', rg_type='mlag'),)"
        )

        d_items = self.qe_query(bp_id, d_query)
        if d_items:
            for item in d_items:
                i = item.get("system")
                devices.append(
                    Device(
                        label=f'{i["hostname"]}-{i["role"]}' f'-{i["system_type"]}',
                        system_id=i["id"],
                    )
                )

        m_items = self.qe_query(bp_id, mlag_query)
        if m_items:
            for item in m_items:
                i = item.get("system")
                devices.append(Device(label=i["label"], system_id=i["id"]))
        return devices

    def get_bp_system_leaf_nodes(self, bp_id: str):
        """
        Return all nodes with role 'leaf'
        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        Returns
        -------

        """
        leaf_query = "match(node('system', name='leaf', role='leaf'))"

        return self.qe_query(bp_id, query=leaf_query)

    def get_bp_system_redundancy_group(self, bp_id: str, system_id):
        """
        Return the redundancy-group (MLAG) the given sysytem is associated with in
        the given blueprint
        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        system_id
            (str) - ID of the blueprint system node
        Returns
        -------

        """
        rg_query = (
            "match(node('redundancy_group', name='rg')"
            ".out('composed_of_systems')"
            ".node('system', role='leaf',"
            f" id='{system_id}'))"
        )
        return self.qe_query(bp_id, query=rg_query)

    def get_all_tor_nodes(self, bp_id):
        """
        Return all nodes associated with Top of Rack. For redundancy-groups (MLAG)
        this will return the redundancy-group node.
        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        Returns
        -------

        """
        leaf_nodes = self.get_bp_system_leaf_nodes(bp_id)

        nodes = list()
        for leaf in leaf_nodes:
            leaf_id = leaf["leaf"]["id"]
            rg = self.get_bp_system_redundancy_group(bp_id, leaf_id)
            if rg:
                if rg[0]["rg"] not in nodes:
                    nodes.append(rg[0]["rg"])
            else:
                nodes.append(leaf["leaf"])

        return nodes

    def create_switch_system_links(self, bp_id: str, data: dict):
        uri = f"/api/blueprints/{bp_id}/switch-system-links"

        self.rest.json_resp_post(uri, data=data)

    def get_cabling_map(self, bp_id: str) -> Dict:
        """
        Retrieve a blueprint's existing cable map

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint

        Returns
        -------
            (dict) - cable map information
        """
        return self.rest.json_resp_get(f"/api/blueprints/{bp_id}/cabling-map")

    def update_cabling_map(self, bp_id: str, links: List[dict]):
        """
        Update the cabling map for a blueprint

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        links
            (str) - list of dictionaries containing new mapping. Example:

                [
                    {
                        "id": "<link id>",
                        "endpoints": [
                            {
                                "interface": {
                                    "if_name": "xe-0/0/0/"
                                    "id": "<interface id>"
                                }
                            },
                            {
                        ],
                    }
                ]

        Returns
        -------
        """
        self.rest.patch(
            f"/api/blueprints/{bp_id}/cabling-map?comment=cabling-map-update",
            data={"links": links},
        )

    def assign_devices_from_json(self, bp_id: str, node_assignment: list):
        """
        Bulk assignment of AOS managed devices to a Blueprint
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        node_assignment
            (list) [{"id": "system_id", "location": "device_name"}]
            example: [
                        {
                          "system_id": "525400F9B231",
                          "id": "3fdd7c9e-73a2-4509-8514-991b79b95fbc",
                          "deploy_mode": "deploy"
                        }
                     ]

        Returns
        -------

        """
        n_path = f"/api/blueprints/{bp_id}/nodes"
        self.rest.patch(n_path, data=node_assignment)

    def assign_device(
        self, bp_id: str, system_id: str, node_id: str, deploy_mode: str
    ):
        """
        Assign AOS managed devices to a Blueprint and update deployment mode
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        system_id
            (str) ID of AOS managed device
        node_id
            (str) ID of Blueprint node
        deploy_mode
            (str) Device deploy mode [deploy, Ready, Drain, Undeploy]
        Returns
        -------

        """
        node_assignment = [
            {"system_id": system_id, "id": node_id, "deploy_mode": deploy_mode}
        ]

        return self.assign_devices_from_json(bp_id, node_assignment)

    def assign_all_devices_from_location(self, bp_id: str, deploy_mode: str):
        """
        Assign ALL AOS managed devices to a Blueprint based on the location field
        of the system.
        NOTE: Location field must match Blueprint node name
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        deploy_mode
            (str) Device deploy mode [deploy, Ready, Drain, Undeploy]
        Returns
        -------

        """
        aos_devices = AosDevices(self.rest)
        bp_nodes = self.get_bp_system_nodes(bp_id)
        systems = aos_devices.managed_devices.get_all()

        system_list = []
        node_assignment = []

        def _get_system_location(system):
            return system.user_config["location"]

        for s in systems:
            location = _get_system_location(s)
            if location:
                system_list.append({"system_id": s.id, "location": location})

            else:
                raise AosInputError(f"location not configured for {s}")

        for s in system_list:
            for k, v in bp_nodes.items():
                if v["hostname"] == s["location"]:
                    node_assignment.append(
                        {
                            "system_id": s["system_id"],
                            "id": v["id"],
                            "deploy_mode": deploy_mode,
                        }
                    )

        return self.assign_devices_from_json(bp_id, node_assignment)

    def unassign_devices(self, bp_id: str, node_ids: list) -> None:
        """
        Un-assign given AOS managed devices from a Blueprint
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        node_ids
            (list) Blueprint node IDs of the devices to un-assign
        Returns
        -------

        """
        data = [
            {"system_id": "", "id": node_id, "deploy_mode": None}
            for node_id in node_ids
        ]
        self.rest.patch(f"/api/blueprints/{bp_id}/nodes", data=data)

    def get_rendered_config(
        self, bp_id: str, node_id: str, config_type: str = "deployed"
    ) -> Dict:
        """
        Retrieve the rendered configuration from a blueprint for a given node

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        node_id
            (str) - ID of node within AOS blueprint for which to retrieve
                    rendered configuration
        config_type
            (str) - type of configuration to retrieve. Options are
                    "deployed" (default), "staging", "operation"

        Returns
        -------
            (dict) - dictionary containing the rendered config as a key value
        """
        return self.rest.json_resp_get(
            f"/api/blueprints/{bp_id}/nodes/{node_id}/"
            f"config-rendering?type={config_type}"
        )

    # Interface maps
    def assign_interface_maps_raw(self, bp_id: str, assignments: dict):
        """
        Assign interface maps to blueprint system nodes.
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        assignments
            (dict) mapping of blueprint system node IDs and global interface
            maps.
            {
              "assignments": {'bp-node-id': 'Cumulus_VX__AOS-7x10-Spine',
                              'bp-node-id': 'Arista_vEOS__AOS-7x10-Leaf'}
        Returns
        -------

        """
        im_path = f"/api/blueprints/{bp_id}/interface-map-assignments"

        self.rest.patch(uri=im_path, data=assignments)

    def assign_interface_map_by_name(
        self, bp_id: str, node_names: list, im_name: str
    ):
        """
        Assign interface map to one or more blueprint system nodes
        based on system node name.
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        node_names
            (list) Blueprint system node names. Must match
            eg ['spine1', 'spine2']
        im_name
            (str) interface map name to assign to system node
        Returns
        -------

        """
        bp_nodes = self.get_bp_system_nodes(bp_id)
        assignment = dict()
        for node in node_names:
            for value in bp_nodes.values():
                if value["label"] == node:
                    assignment[value["id"]] = im_name

        data = {"assignments": assignment}
        self.assign_interface_maps_raw(bp_id=bp_id, assignments=data)

        return data

    # Connectivity Templates
    def get_connectivity_templates_all(self, bp_id: str) -> dict:
        r_path = f"/api/blueprints/{bp_id}/obj-policy-export"
        return self.rest.json_resp_get(r_path)

    def get_connectivity_template(self, bp_id: str, ct_id: str) -> dict:
        r_path = f"/api/blueprints/{bp_id}/obj-policy-export/{ct_id}"
        return self.rest.json_resp_get(r_path)

    def find_connectivity_template_by_name(self, bp_id: str, ct_name: str) -> dict:
        cts = self.get_connectivity_templates_all(bp_id)
        for ct in cts["policies"]:
            if ct_name in ct["label"] and ct["policy_type_name"] == "batch":
                return ct
        return {}

    def create_connectivity_template_from_json(
        self, bp_id: str, data: dict
    ) -> Optional[response]:
        ct_path = f"/api/blueprints/{bp_id}/obj-policy-import"
        return self.rest.put(ct_path, data=data)

    def update_connectivity_template(
        self, bp_id: str, data: dict
    ) -> Optional[response]:
        ct_path = f"/api/blueprints/{bp_id}/obj-policy-batch-apply"
        return self.rest.patch(ct_path, data=data)

    def delete_connectivity_template(
        self, bp_id: str, ct_id: str
    ) -> Optional[response]:
        r_path = f"/api/blueprints/{bp_id}/policies/{ct_id}"
        params = {"delete_recursive": True}
        self.rest.delete(r_path, params=params)

    def get_endpoint_policy(self, bp_id: str, policy_id: str) -> dict:
        p_path = f"/api/blueprints/{bp_id}/endpoint-policies/{policy_id}"
        return self.rest.json_resp_get(p_path)

    def get_endpoint_policies(self, bp_id: str, ptype: str = "staging") -> Dict:
        """
        Retrieve existing endpoint policies for a given blueprint

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        ptype
            (str) - (optional) type parameter, defaults to "staging"

        Returns
        -------
            (dict) - endpoint policies
        """
        return self.rest.json_resp_get(
            f"/api/blueprints/{bp_id}/experience/web/endpoint-policies?type={ptype}"
        )

    def get_endpoint_policy_app_points(
        self, bp_id: str, policy_id: str = None
    ) -> dict:
        p_path = f"/api/blueprints/{bp_id}/obj-policy-application-points"
        params = {"policy": policy_id}
        return self.rest.json_resp_get(p_path, params=params)

    def get_routing_policies(self, bp_id: str, bp_type="staging") -> Dict:
        """
        Retrieve existing routing policies for a given blueprint

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        bp_type
            (str) - (optional) type parameter, defaults to "staging"

        Returns
        -------
            (dict) - routing policies
        """
        return self.rest.json_resp_get(
            f"/api/blueprints/{bp_id}/routing-policies?type={bp_type}"
        )

    # External Routers
    def get_external_routers_all(self, bp_id: str):
        """
        Returns all external routers imported into a given blueprint
        Parameters
        ----------
        bp_id
            (str) ID of blueprint

        Returns
        -------

        """
        r_path = f"/api/blueprints/{bp_id}/external-routers"

        return self.rest.json_resp_get(r_path)["items"]

    def get_external_router(self, bp_id: str, bp_rtr_id: str):
        """
        Returns given external router node based on external router id
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        bp_rtr_id
            (str) Blueprint node ID of external router
        Returns
        -------

        """
        r_path = f"/api/blueprints/{bp_id}/external-routers/{bp_rtr_id}"

        return self.rest.json_resp_get(r_path)

    def find_external_router_by_name(self, bp_id: str, rtr_name: str):
        """
        Returns all external routers imported into a blueprint matching the
        given name (label).
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        rtr_name
            (str) ID of blueprint

        Returns
        -------
            (list)
        """
        return [
            i
            for i in self.get_external_routers_all(bp_id)
            if i["display_name"] == rtr_name
        ]

    def get_external_router_links(self, bp_id: str):
        """
        Returns all links available for a given external router for fabric
        connectivity
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        Returns
        -------

        """
        rl_path = f"/api/blueprints/{bp_id}/external-router-links"

        links = self.rest.json_resp_get(rl_path)
        return links["links"]

    def apply_external_router(
        self,
        bp_id: str,
        ext_rtr_id: str = None,
        ext_rtr_name: str = None,
        connectivity_type: str = "l3",
        links: list = None,
    ):
        """
        Assigns a given external router to a blueprint and configures
        the fabric connectivity type required for peering with the external
        router.
        ext_rtr_id or ex_rtr_name required
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        ext_rtr_id
            (str) Optional - Blueprint node ID of external router
        ext_rtr_name
            (str) Optional - Name of external router
        connectivity_type
            (str) connectivity type for fabric connections to external router
            ['l3', 'l2', 'bond']
        links
            (list) Optional - List of links to apply to external router connectivity

        Returns
        -------

        """

        rtr_path = f"/api/blueprints/{bp_id}/external-routers"

        if ext_rtr_name:
            external_router = AosExternalRouter(self.rest)
            ext_rtr = external_router.find_by_name(rtr_name=ext_rtr_name)

            if not ext_rtr:
                raise AosAPIResourceNotFound(
                    f"Unable to find external router " f"with name {ext_rtr_name}"
                )

            ext_rtr_id = ext_rtr[0].id

        rtr_data = {"router_id": ext_rtr_id}
        bp_rtr_id = self.rest.json_resp_post(rtr_path, data=rtr_data)["id"]

        if not links:
            links = list(self.get_external_router_links(bp_id))

        r_link_body = {"connectivity_type": connectivity_type, "links": list(links)}

        r_link_path = f"/api/blueprints/{bp_id}/external-router-links/{bp_rtr_id}"

        self.rest.put(r_link_path, data=r_link_body)

        return bp_rtr_id

    def delete_external_router(self, bp_id: str, bp_rtr_id: str):
        r_path = f"/api/blueprints/{bp_id}/external-routers/{bp_rtr_id}"

        self.rest.delete(r_path)

    def create_ext_generic_systems(
        self,
        bp_id: str,
        hostname: str,
        asn: str = None,
        loopback_ip: str = None,
        tags: list = None,
    ):
        """
        Creates external-generic blueprint node for external router usage in
        configuration templates
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        hostname
            (str) Name assigned to the node and device as hostname
        asn
            (str) ASN number assigned to external router for BGP peering
            with the AOS managed fabric
        loopback_ip
            (str) IPv4 address assigned to the external-router for bgp
            loopback peering.
            example: "10.10.11.11/32"
        tags:
            (list) Blueprint tags associated with the node.

        Returns
        -------
        dict
        """
        n_path = f"/api/blueprints/{bp_id}/external-generic-systems"

        data = {"hostname": hostname, "label": hostname, "tags": tags}

        ext_rtr = self.rest.json_resp_post(n_path, data=data)

        n_asn_path = f"/api/blueprints/{bp_id}/systems/{ext_rtr['id']}/domain"
        n_lo_path = f"/api/blueprints/{bp_id}/systems/{ext_rtr['id']}/loopback/0"

        self.rest.patch(n_asn_path, data={"domain_id": asn})
        self.rest.patch(n_lo_path, data={"ipv4_addr": loopback_ip})

        return self.get_bp_node_by_id(bp_id, ext_rtr["id"])

    def delete_external_generic_system(
        self, bp_id: str, node_id: str
    ) -> Optional[response]:
        r_path = f"/api/blueprints/{bp_id}/external-generic-systems/{node_id}"
        self.rest.delete(r_path)

    # IBA probes and dashboards
    def get_all_probes(self, bp_id: str):
        """
        Return all IBA probes for a given blueprint
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        Returns
        -------
            (obj) json object
        """
        p_path = f"/api/blueprints/{bp_id}/probes"
        return self.rest.json_resp_get(p_path)

    def get_predefined_probes(self, bp_id: str):
        """
        Return all IBA predefined probes for a given blueprint
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        Returns
        -------
            (obj) json object
        """
        p_path = f"/api/blueprints/{bp_id}/iba/predefined-probes"
        return self.rest.json_resp_get(p_path)

    def get_probe(self, bp_id: str, probe_id: str = None, probe_name: str = None):
        """
        Return IBA probe for a given blueprint by ID or name
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        probe_id
            (str) ID of IBA probe
        probe_name
            (str) name of IBA probe
        Returns
        -------
            (obj) json object
        """
        probes = self.get_all_probes(bp_id=bp_id)

        if probes:
            if probe_name:
                for p in probes["items"]:
                    if p["label"] == probe_name:
                        return p
                raise AosAPIError(f"IBA Probe {probe_name} not found")

            if probe_id:
                for p in probes["items"]:
                    if p["id"] == probe_id:
                        return p
                raise AosAPIError(f"IBA Probe {probe_id} not found")

    # Security Zones
    def get_all_security_zones(self, bp_id: str) -> List[SecurityZone]:
        """
        Return all security-zones (VRFs) in a given blueprint
        Parameters
        ----------
        bp_id
            (str) - ID of AOS Blueprint

        Returns
        -------
            [SecurityZone]
        """
        sec_zones = self.rest.json_resp_get(
            f"/api/blueprints/{bp_id}/security-zones"
        )["items"]

        return [SecurityZone.from_json(sz) for sz in sec_zones.values()]

    def get_security_zone(self, bp_id, sz_id) -> SecurityZone:
        """
        Return security-zone (VRF) in a given blueprint based on ID.

        Parameters
        ----------

        bp_id
            (str) - ID of AOS blueprint

        sz_id
            (str) - ID of security-zone

        Returns
        -------
            SecurityZone
        """
        return SecurityZone.from_json(
            self.rest.json_resp_get(
                f"/api/blueprints/{bp_id}/security-zones/{sz_id}"
            )
        )

    def find_sz_by_name(self, bp_id: str, name: str) -> Optional[SecurityZone]:
        """
        Returns security-zones (VRF) in a given blueprint based on name.

        Parameters
        ----------

        bp_id
            (str) - ID of AOS blueprint

        name
            (str) - ID of security-zone

        Returns
        -------
            SecurityZone
        """
        for sz in self.get_all_security_zones(bp_id):
            if sz.vrf_name == name:
                return sz

    def create_security_zone_from_json(
        self, bp_id: str, payload: dict, params: dict = None
    ):
        """
        Create a security-zone in the given blueprint using a
        preformatted json object.

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        payload
            (str) - json object for payload
        params
            (dict) - supported endpoint paramaters. Most common is
            {'async': 'full'} which returns created task ID for tracking
        Returns
        -------
            (obj) - security-zone ID
        """
        sz_path = f"/api/blueprints/{bp_id}/security-zones"
        return self.rest.json_resp_post(uri=sz_path, data=payload, params=params)

    def apply_security_zone_dhcp(self, bp_id: str, sz_id: str, dhcp_servers: dict):

        self.rest.put(
            uri=f"/api/blueprints/{bp_id}/security-zones/{sz_id}/dhcp-servers",
            data=dhcp_servers,
        )

        return self.get_security_zone(bp_id, sz_id)

    def create_security_zone(
        self,
        bp_id: str,
        name: str,
        routing_policy: dict = None,
        import_policy: str = None,
        vlan_id: int = None,
        vni_id: int = None,
        leaf_loopback_ip_pools: list = None,
        dhcp_servers: list = None,
        timeout: int = 60,
    ):
        """
        Create a security-zone in the given blueprint

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        name
            (str) - name given to the security-zone AND vrf_name. Must
                    be unique to all other security-zones
        routing_policy
            (dict) - specific routing policy to apply. Overrides defaults:
                    {
                        "export_policy": {
                            "spine_leaf_links": False,
                            "loopbacks": True,
                            "l2edge_subnets": True,
                            "l3edge_server_links": True
                        },
                        "import_policy": "default_only"
                    }
        import_policy
            (str) - change the route import policy. Default is
                    "default_only
                    ["default_only", "all", "extra_only"]
        vni_id
            (int) - VxLAN VNI assosiated with the routing zone
        vlan_id
            (int) - VLAN ID use for sub-interface tagging with external system
                    connections. Must be unique across all security zones
                    and VRFs
                    Default (None) wll request vlan from pool.
                    range 1 - 4094
        leaf_loopback_ip_pools
            (list) - list of IP pool IDs to assign to leaf_loopback resources
        dhcp_servers
            (list) - list of DHCP server (relay) IP addresses
        timeout
            (int) - time (seconds) to wait for creation

        Returns
        -------
            (obj) - security-zone
        """

        r_policy = {
            "export_policy": {
                "spine_leaf_links": False,
                "loopbacks": True,
                "l2edge_subnets": True,
                "l3edge_server_links": False,
            },
            "import_policy": "default_only",
        }

        if routing_policy:
            r_policy = routing_policy
        if import_policy:
            r_policy["import_policy"] = import_policy

        sec_zone = {
            "routing_policy": r_policy,
            "sz_type": "evpn",
            "label": name,
            "vrf_name": name,
            "vlan_id": vlan_id,
            "vni_id": vni_id,
        }

        sz_task = self.create_security_zone_from_json(
            bp_id, sec_zone, params={"async": "full"}
        )
        logger.info(f"Creating Security-zone '{name}' in blueprint '{bp_id}'")

        repeat_until(
            lambda: self.is_task_active(bp_id, sz_task["task_id"]) is False,
            timeout=timeout,
        )
        sz = self.find_sz_by_name(bp_id, name)

        # SZ leaf loopback pool
        if leaf_loopback_ip_pools:
            group_name = "leaf_loopback_ips"
            group_path = requote_uri(f"sz:{sz.id},{group_name}")
            self.apply_resource_groups(
                bp_id=bp_id,
                resource_type="ip",
                group_name=group_path,
                pool_ids=leaf_loopback_ip_pools,
            )
            logger.info(
                f"Applying '{group_name}' resource pool "
                f"'{leaf_loopback_ip_pools}' to Security-zone "
                f"'{name}' in blueprint '{bp_id}'"
            )
        # DHCP servers (relay)
        if dhcp_servers:
            dhcp = {"items": dhcp_servers}
            self.apply_security_zone_dhcp(
                bp_id=bp_id, sz_id=sz.id, dhcp_servers=dhcp
            )
            logger.info(
                f"Applying dhcp servers '{dhcp_servers}' to Security-zone "
                f"'{name}' in blueprint '{bp_id}'"
            )

        return self.get_security_zone(bp_id, sz.id)

    def update_security_zone(self, bp_id: str, sz_id: str, payload: str):
        """
        Update a security-zone in the given blueprint using a
        preformatted json object.

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        sz_id
            (str) - ID of security-zone
        payload
            (str) - json object for payload

        Returns
        -------

        """
        sz_path = f"/api/blueprints/{bp_id}/security-zones/{sz_id}"

        self.rest.patch(uri=sz_path, data=payload)

    def get_sz_connectivity_points(self, bp_id: str, sz_id: str):
        """
        return all connectivity-points associated with a security-zone.
        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        sz_id
            (str) - ID of security-zone

        Returns
        -------

        """
        cp_path = (
            f"/api/blueprints/{bp_id}/security-zones/" f"{sz_id}/connectivity-points"
        )

        resp = self.rest.json_resp_get(cp_path)
        return list(resp["items"].values())

    def apply_sz_connectivity_points_raw(self, bp_id: str, sz_id: str, data: dict):

        cp_path = (
            f"/api/blueprints/{bp_id}/security-zones/" f"{sz_id}/connectivity-points"
        )

        return self.rest.json_resp_post(uri=cp_path, data=data)

    def apply_sz_connectivity_points(
        self,
        bp_id: str,
        sz_id: str,
        links: dict,
        peering_type: str,
        routing_policy: dict = None,
        resources: dict = None,
        ipv4_subnet: dict = str,
        vlan_id: int = None,
        ipv6_enabled: bool = False,
        ipv6_subnet: dict = None,
        routing_protocol: str = "bgp",
        ospf_domain_id: str = None,
        ospf_policy: dict = None,
    ):
        """
        Add connectivity-points to a given security-zone for external-router
        connectivity
        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        sz_id
            (str) - ID of security-zone
        links
            (dict) - Blueprint link nodes associated with the security-zone
        peering_type
            (str) - [ interface, loopback ]
        routing_policy
            (dict) - (optional) updated routing-policy to use with external router
        resources
            (dict) - (optional) further defined resource assigment such as IPv4/IPv6
            address
        ipv4_subnet
            (dict) - IPv4 subnet to assign to the peering links ex '10.1.2.0/24'
        vlan_id
            (int) - (optional) vlan id used for peering. If not specified the
            vlan_id will be assigned from the resource pool
        ipv6_enabled
            (bool) - enable or disable IPv6 on the peering links. Default: disabled
        ipv6_subnet
            (dict) - (Optional) IPv4 subnet to assign to the peering links
        routing_protocol
            (str) - Routing protol used for external router peering. Default BGP
            ['bgp', ospf]
        ospf_domain_id
            (str) - (Optional) ospf domain for external router peering if using OSPF
            routing_protocol
        ospf_policy
            (dict) - (Optional) ospf policy for external router peering if using
            OSPF routing_protocol

        Returns
        -------

        """
        data = {
            "routing_policy": routing_policy,
            "composed_of": links,
            "resources": resources,
            "ospf_policy": ospf_policy,
            "ipv6_subnet": ipv6_subnet,
            "ospf_domain_id": ospf_domain_id,
            "routing_protocol": routing_protocol,
            "ipv4_subnet": ipv4_subnet,
            "ipv6_enabled": ipv6_enabled,
            "vlan_id": vlan_id,
            "peering_type": peering_type,
        }

        return self.apply_sz_connectivity_points_raw(
            bp_id=bp_id, sz_id=sz_id, data=data
        )

    def delete_security_zone(self, bp_id: str, sz_id: str) -> None:
        """
        Remove security-zone from a blueprint.
        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        sz_id
            (str) - ID of security-zone

        Returns
        -------

        """
        self.rest.delete(f"/api/blueprints/{bp_id}/security-zones/{sz_id}")

    def delete_sz_connectivity_point(
        self, bp_id: str, sz_id: str, cp_id: str
    ) -> None:
        """
        Remove connectivity-points from a given security-zone.
        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        sz_id
            (str) - ID of security-zone
        cp_id
            (str) - ID of connectivity-point

        Returns
        -------

        """
        self.rest.delete(
            f"/api/blueprints/{bp_id}/security-zones/{sz_id}/"
            f"connectivity-points/{cp_id}"
        )

    def apply_leaf_loopback_ip_to_sz(self, bp_id: str, sz_id: str, pool_id: str):
        """
        Assign IP Pool to a specified security-zone for use by leaf nodes for
        loopback IPs.
        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        sz_id
            (str) - ID of security-zone
        pool_id
            (str) - ID of AOS resource pool

        Returns
        -------

        """
        data = json.dumps({"pool_ids": [str(pool_id)]})
        p_path = (
            f"/api/blueprints/{bp_id}/resource_groups/ip/"
            f"sz:{sz_id},leaf_loopback_ips"
        )

        return self.rest.json_resp_put(uri=p_path, data=data)

    # Virtual Networks
    def create_virtual_network_from_json(
        self, bp_id: str, virtual_network: dict, params: dict = None
    ):
        """
        Create new virtual-network (VLAN) in a given blueprint
        Parameters
        ----------
        bp_id
            (str) - ID of blueprint
        virtual_network
            (dict) - VirtualNetwork object
        params
            (dict) - endpoint parameters. Default None
        Returns
        -------

        """
        vn_path = f"/api/blueprints/{bp_id}/virtual-networks"
        return self.rest.json_resp_post(
            uri=vn_path, data=virtual_network, params=params
        )

    def create_virtual_network(
        self,
        bp_id: str,
        name: str,
        bound_to: list,
        sz_id: str = None,
        sz_name: str = None,
        vn_type: VNType = VNType.vxlan,
        vn_id: str = None,
        tag_type: VNTagType = None,
        ipv4_subnet: str = None,
        ipv4_gateway: str = None,
        ipv6_enabled: bool = False,
        ipv6_subnet: str = None,
        ipv6_gateway: str = None,
        tagged_ct: bool = False,
        untagged_ct: bool = False,
        timeout: int = 60,
    ):
        """

        Parameters
        ----------
        bp_id
            (str) - ID of blueprint
        name
            (str) - VLAN name
        bound_to
            (list) - nodes to assign the given virtual network to
        sz_id
            (str) - (optional) Security-zone ID associated with the virtual-network.
            Default: default security zone
        sz_name
            (str) - (optional) Security-zone name associated with the
            virtual-network.
            Default: default security zone
        vn_type
            (VNType) - Type of virtual network ['vxlan', 'vlan']
        vn_id
            (str) - (Optional) ID of virtual network
        tag_type
            (VNTagType) - (Optional) Default tag type.
            ['vlan_tagged', 'untagged', ''unassigned]
            Default: None
        ipv4_subnet
            (str) - (optional) IPV4 subnet assigned to virtual-network. If none
            given the subnet will be assigned from resource pool
            default: None
        ipv4_gateway
            (str) - (optional) IPV4 gateway address assigned to virtual-network.
            If none given the subnet will be assigned from resource pool
            default: None
        ipv6_enabled
            (bool) - (Optional) Enable or disable IPv6 on the virtual-network
        ipv6_subnet
            (str) - (optional) IPV6 subnet assigned to virtual-network. If none
            given the subnet will be assigned from resource pool
            default: None
        ipv6_gateway
            (str) - (optional) IPV4 gateway address assigned to virtual-network.
            If none given the subnet will be assigned from resource pool
            default: None
        tagged_ct
            (bool) - (optional) Create tagged connectivity template for the given
            virtual-network.
        untagged_ct
            (bool) - (optional) Create untagged connectivity template for the given
            virtual-network.
        timeout
            (int) - time (seconds) to wait for creation

        Returns
        -------

        """
        if sz_name:
            sz = self.find_sz_by_name(bp_id, name=sz_name)
            if sz:
                sz_id = sz.id
            else:
                raise ValueError(f"Invalid argument '{sz_name}' was passed")

        virt_net = {
            "label": name,
            "security_zone_id": sz_id,
            "vn_type": vn_type.value,
            "vn_id": vn_id,
            "bound_to": bound_to,
            "ipv4_enabled": True,
            "dhcp_service": "dhcpServiceEnabled",
            "ipv4_subnet": ipv4_subnet,
            "ipv4_gateway": ipv4_gateway,
        }

        if ipv6_enabled:
            virt_net["ipv6_subnet"] = ipv6_subnet
            virt_net["ipv6_gateway"] = ipv6_gateway

        if tag_type:
            virt_net["default_endpoint_tag_types"] = {
                "single-link": tag_type.value,
                "dual-link": tag_type.value,
            }
        if tagged_ct:
            virt_net["create_policy_tagged"] = tagged_ct
        if untagged_ct:
            virt_net["create_policy_untagged"] = untagged_ct

        vn_task = self.create_virtual_network_from_json(
            bp_id, virt_net, params={"async": "full"}
        )
        logger.info(f"Creating virtual-network '{name}' in blueprint '{bp_id}'")

        repeat_until(
            lambda: self.is_task_active(bp_id, vn_task["task_id"]) is False,
            timeout=timeout,
        )

        return self.find_vn_by_name(bp_id, name)

    def get_all_virtual_networks(self, bp_id: str) -> List[VirtualNetwork]:
        """
        Return all virtual networks in a given blueprint
        Parameters
        ----------
        bp_id
            (str) - ID of AOS Blueprint

        Returns
        -------
            [VirtualNetwork]
        """
        virt_nets = self.rest.json_resp_get(
            f"/api/blueprints/{bp_id}/virtual-networks"
        )["virtual_networks"]

        return [VirtualNetwork.from_json(vn) for vn in virt_nets.values()]

    def get_virtual_network(self, bp_id: str, vn_id: str) -> VirtualNetwork:
        """
        Return virtual-networks (VLANS) in a given blueprint based on ID.

        Parameters
        ----------

        bp_id
            (str) - ID of AOS blueprint

        vn_id
            (str) - ID of virtual-network

        Returns
        -------
            VirtualNetwork
        """

        return VirtualNetwork.from_json(
            self.rest.json_resp_get(
                f"/api/blueprints/{bp_id}/virtual-networks/{vn_id}"
            )
        )

    def find_vn_by_name(self, bp_id: str, name: str) -> Optional[VirtualNetwork]:
        """
        Return virtual-networks (VLANS) in a given blueprint based on name.

        Parameters
        ----------

        bp_id
            (str) - ID of AOS blueprint

        name
            (str) - ID of virtual-network

        Returns
        -------
            (obj) - VirtualNetwork
        """
        for vn in self.get_all_virtual_networks(bp_id):
            if vn.label == name:
                return vn

    def delete_virtual_network(self, bp_id: str, vn_id: str) -> None:
        """
        Removes a given virtual network based
        Parameters
        ----------
        bp_id
             (str) - ID of AOS Blueprint
        vn_id
            (str) - ID of virtual network

        Returns
        -------
        """
        self.rest.delete(f"/api/blueprints/{bp_id}/virtual_networks/{vn_id}")

    def add_virtual_network_batch(self, bp_id: str, payload: str):
        """
        Create multiple virtual networks in the given blueprint using a
        preformatted json object.

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        payload
            (str) - json object for payload

        Returns
        -------
            (obj) - virtual network IDs
        """
        vn_path = f"/api/blueprints/{bp_id}/virtual-networks-batch"

        return self.rest.json_resp_post(uri=vn_path, data=payload)

    def get_fabric_addressing_policy(self, bp_id):
        """
        Return fabric-addressing-policy in a given blueprint.

        Parameters
        ----------
        bp_id
            (str) - ID of AOS Blueprint

        Returns
        ----------
            (obj) json object
        """
        path = f'/api/blueprints/{bp_id}/fabric-addressing-policy'
        return self.rest.json_resp_get(path)

    def update_fabric_addressing_policy(
        self,
        bp_id,
        ipv6_enabled=None,
        esi_mac_msb=None
    ):
        """
        Sets a fabric addressing policy for a given blueprint.

        Parameters
        ----------
        bp_id
            (str) - ID of AOS Blueprint
            (bool) - (optional) enable or disable support for IPv6 virtual networks
            (int)  - (optional) Most Significant Byte (MSB) value used for
            ESI MAC addresses
        Returns
        -------
        """

        data = {}

        if ipv6_enabled:
            data['ipv6_enabled'] = ipv6_enabled

        if esi_mac_msb:
            data['esi_mac_msb'] = esi_mac_msb

        url = f'/api/blueprints/{bp_id}/fabric-addressing-policy'
        return self.rest.patch(url, data=data)

    def get_node_relationships(
        self,
        bp_id,
        relationship_type: str = None,
        source_id: str = None,
        target_id: str = None
    ):
        """
        Return node relationships in a given blueprint

        Parameters
        ---------
        bp_id
            (str) - ID of AOS Blueprint
        relationship_type
            (str) - (optional) type of relationship
        source_id
            (str) - (optional) ID of source of relationship
        target_id
            (str) - (optional) ID of target of relationship
        """

        url = f'/api/blueprints/{bp_id}/relationships'

        params = {
            'relationship_type': relationship_type,
            'source_id': source_id,
            'target_id': target_id
        }

        return self.rest.json_resp_get(url, params=params)['relationships']
