# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
from .aos import AosSubsystem, AosAPIError

logger = logging.getLogger(__name__)


class AosExternalSystems(AosSubsystem):
    """
    Management of AOS Resource elements:
    - Providers
    - External Routers
    - Virtual Infra Managers
    """

    def __init__(self, rest):
        self.external_router = AosExternalRouters(rest)


class AosExternalRouters(AosSubsystem):
    """
    Manage AOS external routers.
    This does not apply the resource to a blueprint
    See `aos.blueprint` to apply to blueprint
    """

    def get_all(self):
        """
        Return all external routers configured from AOS

        Returns
        -------
            (obj) json response
        """
        er_path = "/api/resources/external-routers"
        return self.rest.json_resp_get(er_path)

    def get_external_router(self, ex_id: str = None, ex_name: str = None):
        """
        Return an existing external router by id or name
        Parameters
        ----------
        ex_id
            (str) ID of AOS external router (optional)
        ex_name
            (str) Name or label of AOS external router (optional)


        Returns
        -------
            (obj) json response
        """

        if ex_name:
            ext_routers = self.get_all()
            if ext_routers:
                for rtr in ext_routers:
                    if rtr.get("display_name") == ex_name:
                        return rtr
                raise AosAPIError(f"External Router {ex_name} not found")

        return self.rest.json_resp_get(f"/api/resources/external-routers/{ex_id}")

    def add_external_router(self, router_list):
        """
        Add one or more external routers to AOS

        Parameters
        ----------
        router_list
            (list) - list of json payloads

        Returns
        -------
            (list) external router IDs
        """
        p_path = "/api/resources/external-routers"

        ids = []
        for rtr in router_list:
            item_id = self.rest.json_resp_post(uri=p_path, data=rtr)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_external_router(self, ext_list: str):
        """
        Delete one or more device profiles from AOS
        External routers can not be deleted if they are associated with
        a blueprint.

        Parameters
        ----------
        ext_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/resources/external-routers"

        ids = []
        for ext_id in ext_list:
            self.rest.json_resp_delete(f"{p_path}/{ext_id}")
            ids.append(ext_id)

        return ids
