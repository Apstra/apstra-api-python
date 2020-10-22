# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
from collections import namedtuple
from typing import Optional
from .aos import AosSubsystem, AosAPIError


logger = logging.getLogger(__name__)

Blueprint = namedtuple("Blueprint", ["label", "id"])


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
        returns blueprint by either id or name
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

    def apply_configlet(self, bp_id: str, configlet: dict):
        """
        Import and apply existing configlet to AOS Blueprint
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        configlet
            (Str) ID of AOS configlet to use

        Returns
        -------

        """
        c_path = f"/api/blueprints/{bp_id}/configlets"
        self.rest.json_resp_post(c_path, data=configlet)

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

    def apply_property_set(self, bp_id: str, property_set: dict):
        """
        Import and apply existing property-set to AOS Blueprint
        Parameters
        ----------
        bp_id
            (str) ID of blueprint
        property_set
            (Str) ID of AOS property-set to use

        Returns
        -------

        """
        ps_path = f"/api/blueprints/{bp_id}/property-sets"
        self.rest.json_resp_post(ps_path, data=property_set)

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

        return {
            "version": int(resp["staging_version"]),
            "status": resp["status"],
            "deploy_error": resp["deploy_error"],
        }

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
            "version": int(staging_version["staging_version"]),
            "description": d,
        }
        self.rest.json_resp_put(commit_path, data=payload)
