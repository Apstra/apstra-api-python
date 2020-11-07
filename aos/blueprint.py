# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import json
import logging
from collections import namedtuple
from typing import Optional
from .aos import AosSubsystem, AosAPIError, AosInputError
from .design import AosConfiglets, AosPropertySets


logger = logging.getLogger(__name__)

Blueprint = namedtuple("Blueprint", ["label", "id"])
Device = namedtuple("Device", ["label", "system_id"])
StagingVersion = namedtuple("Staging", ["version", "status", "deploy_error"])


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

    def delete_blueprint(self, bp_id: str):
        """
        Deletes blueprint by id
        Parameters
        ----------
        bp_id
            (str) ID of AOS blueprint (optional)

        Returns
        -------
            (obj) json object
        """

        return self.rest.json_resp_delete(f"/api/blueprints/{bp_id}")

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

    # Commit, staging and rollback
    def get_staging_version(self, bp_id: str):
        """
        Get the latest version of staged changes for the given blueprint
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        Returns
        -------
            int
        """
        commit_diff_path = f"/api/blueprints/{bp_id}/diff-status"
        resp = self.rest.json_resp_get(commit_diff_path)

        return StagingVersion(
            version=int(resp["staging_version"]),
            status=resp["status"],
            deploy_error=resp["deploy_error"],
        )

    def commit_staging(self, bp_id: str, description=None):
        """
        Commit all changes in staging to Blueprint.
        Uses latest staging version number available on a Blueprint
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        description
            (str) description to use during commit

        Returns
        -------

        """
        commit_path = f"/api/blueprints/{bp_id}/deploy"

        staging_version = self.get_staging_version(bp_id)

        d = ""
        if description:
            d = description

        payload = {
            "version": int(staging_version.version),
            "description": d,
        }
        return self.rest.json_resp_put(commit_path, data=payload)

    # Graph Queries
    def qe_query(self, bp_id: str, query: str):
        """
        QE query aginst a Blueprint graphDB

        Parameters
        ----------
        bp_id
            (str) ID of AOS blueprint (optional)
        query
            (str) qe query string

        Returns
        -------
            (obj) - json object
        """
        qe_path = f"/api/blueprints/{bp_id}/qe"
        data = {"query": query}
        resp = self.rest.json_resp_post(uri=qe_path, data=data)

        return resp["items"]

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
        role_in = f"role in {role}"
        id_in = f"id in {system_id}"

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

    # Security Zones
    def get_security_zones_all(self, bp_id: str):
        """
        Return all security-zones in a given blueprint.

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint

        Returns
        -------
            (obj) - json object
        """
        sz_path = f"/api/blueprints/{bp_id}/security-zones"

        resp = self.rest.json_resp_get(uri=sz_path)
        return resp["items"]

    def get_security_zone(self, bp_id: str, sz_id: str = None, sz_name: str = None):
        """
        Return security-zone in a given blueprint based on name or ID.

        Parameters
        ----------

        bp_id
            (str) - ID of AOS blueprint

        sz_id
            (str) - ID of security-zone (optional)

        sz_name
            (str) - Name or label of security-zone (optional)

        Returns
        -------
            (obj) - json object
        """

        sec_zones = self.get_security_zones_all(bp_id)

        if sec_zones:
            if sz_name:
                for sz, value in sec_zones.items():
                    if value["label"] == sz_name:
                        return value
                raise AosAPIError(f"Security-zone {sz_name} not found")

            if sz_id:
                for sz, value in sec_zones.items():
                    if value["id"] == sz_id:
                        return value
                raise AosAPIError(f"Security-zone {sz_name} not found")

    def add_security_zone(self, bp_id: str, payload: str):
        """
        Create a security-zone in the given blueprint using a
        preformatted json object.

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        payload
            (str) - json object for payload

        Returns
        -------
            (obj) - security-zone ID
        """
        sz_path = f"/api/blueprints/{bp_id}/security-zones"

        return self.rest.json_resp_post(uri=sz_path, data=payload)

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
            (obj) - security-zone ID
        """
        sz_path = f"/api/blueprints/{bp_id}/security-zones/{sz_id}"

        return self.rest.json_resp_patch(uri=sz_path, data=payload)

    def delete_security_zone(self, bp_id: str, sz_id: str):
        """
        Delete a given security-zone from a blueprint

        Parameters
        ----------

        bp_id
            (str) - ID of AOS blueprint
        sz_id
            (str) - Id of security-zone

        Returns
        -------
            (obj) {}
        """
        sz_path = f"/api/blueprints/{bp_id}/security-zones"

        return self.rest.json_resp_delete(uri=sz_path)

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
        p_path = f"/api/blueprints/{bp_id}/resource_groups/ip/sz:{sz_id},leaf_loopback_ips"

        return self.rest.json_resp_put(uri=p_path, data=data)

    # Virtual Networks
    def get_virtual_networks_all(self, bp_id: str):
        """
        Return all virtual networks in a given blueprint.

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint

        Returns
        -------
            (obj) - json object
        """
        vn_path = f"/api/blueprints/{bp_id}/virtual-networks"

        resp = self.rest.json_resp_get(uri=vn_path)
        return resp["virtual_networks"]

    def get_virtual_network(
        self, bp_id: str, vn_id: str = None, vn_name: str = None
    ):
        """
        Return virtual network in a given blueprint based on name or ID.

        Parameters
        ----------

        bp_id
            (str) - ID of AOS blueprint

        vn_id
            (str) - ID of virtual network (optional)

        vn_name
            (str) - Name or label of virtual networks (optional)

        Returns
        -------
            (obj) - json object
        """

        virt_networks = self.get_virtual_networks_all(bp_id)

        if virt_networks:
            if vn_name:
                for vn, value in virt_networks.items():
                    if value["label"] == vn_name:
                        return value
                raise AosAPIError(f"Virtual Network {vn_name} not found")

            if vn_id:
                for vn, value in virt_networks.items():
                    if value["id"] == vn_id:
                        return value
                raise AosAPIError(f"Virtual Network {vn_name} not found")

    def add_virtual_network(self, bp_id: str, payload: str):
        """
        Create a virtual network in the given blueprint using a
        preformatted json object.

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        payload
            (str) - json object for payload

        Returns
        -------
            (obj) - virtual network ID
        """
        vn_path = f"/api/blueprints/{bp_id}/virtual-networks"

        return self.rest.json_resp_post(uri=vn_path, data=payload)

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

    def update_virtual_network(self, bp_id: str, vn_id: str, payload: str):
        """
        Update a virtual network in the given blueprint using a
        preformatted json object.

        Parameters
        ----------
        bp_id
            (str) - ID of AOS blueprint
        vn_id
            (str) - ID of virtual network
        payload
            (str) - json object for payload

        Returns
        -------
            (obj) - virtual network ID
        """
        vn_path = f"/api/blueprints/{bp_id}/virtual-networks/{vn_id}"

        return self.rest.json_resp_patch(uri=vn_path, data=payload)

    def delete_virtual_network(self, bp_id: str, vn_id: str):
        """
        Delete a given virtual network from a blueprint

        Parameters
        ----------

        bp_id
            (str) - ID of AOS blueprint
        vn_id
            (str) - Id of virtual network

        Returns
        -------
            (obj) {}
        """
        vn_path = f"/api/blueprints/{bp_id}/virtual-networks/{vn_id}"

        return self.rest.json_resp_delete(uri=vn_path)
