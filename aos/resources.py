# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
from .aos import AosSubsystem, AosAPIError

logger = logging.getLogger(__name__)


class AosResources(AosSubsystem):
    """
    Management of AOS Resource elements:
    - ASN Pools
    - VNI Pools
    - IPv4 address Pools
    - IPv6 address Pools
    """

    def __init__(self, rest):
        self.asn_pools = AosAsnPools(rest)
        self.vni_pools = AosVniPools(rest)
        self.ipv4_pools = AosIpv4Pools(rest)
        self.ipv6_pools = AosIpv6Pools(rest)


class AosAsnPools(AosSubsystem):
    """
    Manage AOS ASN Pools.
    This does not apply the resource to a blueprint
    See `aos.blueprint` to apply to blueprint
    """

    def get_all(self):
        """
        Return all asn pools configured from AOS

        Returns
        -------
            (obj) json response
        """
        a_path = "/api/resources/asn-pools"
        return self.rest.json_resp_get(a_path)

    def get_pool(self, pool_id: str = None, pool_name: str = None):
        """
        Return an existing ASN pool by id or name
        Parameters
        ----------
        pool_id
            (str) ID of AOS asn pool (optional)
        pool_name
            (str) Name or label of AOS asn pool (optional)


        Returns
        -------
            (obj) json response
        """

        if pool_name:
            pools = self.get_all()
            if pools:
                for pool in pools:
                    if pool.get("display_name") == pool_name:
                        return pool
                raise AosAPIError(f"ASN Pool {pool_name} not found")

        return self.rest.json_resp_get(f"/api/resources/asn-pools/{pool_id}")

    def add_pool(self, pool_list: list):
        """
        Add one or more ASN pools to AOS

        Parameters
        ----------
        pool_list
            (list) - list of json payloads

        Returns
        -------
            (list) ASN pool IDs
        """
        p_path = "/api/resources/asn-pools"

        ids = []
        for pool in pool_list:
            item_id = self.rest.json_resp_post(uri=p_path, data=pool)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_pool(self, pool_list: str):
        """
        Delete one or more asn pools from AOS.
        ASN Pools can not be deleted if they are "in_us" by a Blueprint

        Parameters
        ----------
        pool_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/resources/asn-pools"

        ids = []
        for pool_id in pool_list:
            self.rest.json_resp_delete(f"{p_path}/{pool_id}")
            ids.append(pool_id)

        return ids


class AosVniPools(AosSubsystem):
    """
    Manage AOS VNI Pools.
    This does not apply the resource to a blueprint
    See `aos.blueprint` to apply to blueprint
    """

    def get_all(self):
        """
        Return all vni pools configured from AOS

        Returns
        -------
            (obj) json response
        """
        v_path = "/api/resources/vni-pools"
        return self.rest.json_resp_get(v_path)

    def get_pool(self, pool_id: str = None, pool_name: str = None):
        """
        Return an existing VNI pool by id or name
        Parameters
        ----------
        pool_id
            (str) ID of AOS vni pool (optional)
        pool_name
            (str) Name or label of AOS vni pool (optional)


        Returns
        -------
            (obj) json response
        """

        if pool_name:
            pools = self.get_all()
            if pools:
                for pool in pools:
                    if pool.get("display_name") == pool_name:
                        return pool
                raise AosAPIError(f"VNI Pool {pool_name} not found")

        return self.rest.json_resp_get(f"/api/resources/vni-pools/{pool_id}")

    def add_pool(self, pool_list: list):
        """
        Add one or more vni pools to AOS

        Parameters
        ----------
        pool_list
            (list) - list of json payloads

        Returns
        -------
            (list) VNI pool IDs
        """
        p_path = "/api/resources/vni-pools"

        ids = []
        for pool in pool_list:
            item_id = self.rest.json_resp_post(uri=p_path, data=pool)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_pool(self, pool_list: str):
        """
        Delete one or more vni pools from AOS.
        VNI Pools can not be deleted if they are "in_us" by a Blueprint

        Parameters
        ----------
        pool_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/resources/vni-pools"

        ids = []
        for pool_id in pool_list:
            self.rest.json_resp_delete(f"{p_path}/{pool_id}")
            ids.append(pool_id)

        return ids


class AosIpv4Pools(AosSubsystem):
    """
    Manage AOS IPv4 address Pools.
    This does not apply the resource to a blueprint
    See `aos.blueprint` to apply to blueprint
    """

    def get_all(self):
        """
        Return all ip pools from AOS

        Returns
        -------
            (obj) json response
        """
        ip_path = "/api/resources/ip-pools"
        return self.rest.json_resp_get(ip_path)

    def get_pool(self, pool_id: str = None, pool_name: str = None):
        """
        Return an existing IPv4 pool by id or name
        Parameters
        ----------
        pool_id
            (str) ID of AOS ipv4 pool (optional)
        pool_name
            (str) Name or label of AOS ipv4 pool (optional)


        Returns
        -------
            (obj) json response
        """

        if pool_name:
            pools = self.get_all()
            if pools:
                for pool in pools:
                    if pool.get("display_name") == pool_name:
                        return pool
                raise AosAPIError(f"IPv4 Pool {pool_name} not found")

        return self.rest.json_resp_get(f"/api/resources/ip-pools/{pool_id}")

    def add_pool(self, pool_list: list):
        """
        Add one or more ip pools to AOS

        Parameters
        ----------
        pool_list
            (list) - list of json payloads

        Returns
        -------
            (list) ip pool IDs
        """
        p_path = "/api/resources/ip-pools"

        ids = []
        for pool in pool_list:
            item_id = self.rest.json_resp_post(uri=p_path, data=pool)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_pool(self, pool_list: str):
        """
        Delete one or more asn pools from AOS.
        ASN Pools can not be deleted if they are "in_us" by a Blueprint

        Parameters
        ----------
        pool_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/resources/ip-pools"

        ids = []
        for pool_id in pool_list:
            self.rest.json_resp_delete(f"{p_path}/{pool_id}")
            ids.append(pool_id)

        return ids


class AosIpv6Pools(AosSubsystem):
    """
    Manage AOS IPv6 address Pools.
    This does not apply the resource to a blueprint
    See `aos.blueprint` to apply to blueprint
    """

    def get_all(self):
        """
        Return all ip pools from AOS

        Returns
        -------
            (obj) json response
        """
        ip_path = "/api/resources/ipv6-pools"
        return self.rest.json_resp_get(ip_path)

    def get_pool(self, pool_id: str = None, pool_name: str = None):
        """
        Return an existing IPv6 pool by id or name
        Parameters
        ----------
        pool_id
            (str) ID of AOS ipv6 pool (optional)
        pool_name
            (str) Name or label of AOS ipv6 pool (optional)


        Returns
        -------
            (obj) json response
        """

        if pool_name:
            pools = self.get_all()
            if pools:
                for pool in pools:
                    if pool.get("display_name") == pool_name:
                        return pool
                raise AosAPIError(f"IPv6 Pool {pool_name} not found")

        return self.rest.json_resp_get(f"/api/resources/ipv6-pools/{pool_id}")

    def add_pool(self, pool_list: list):
        """
        Add one or more ipv6 pools to AOS

        Parameters
        ----------
        pool_list
            (list) - list of json payloads

        Returns
        -------
            (list) ip pool IDs
        """
        p_path = "/api/resources/ipv6-pools"

        ids = []
        for pool in pool_list:
            item_id = self.rest.json_resp_post(uri=p_path, data=pool)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_pool(self, pool_list: str):
        """
        Delete one or more IPv6 pools from AOS.
        IPv6 Pools can not be deleted if they are "in_us" by a Blueprint

        Parameters
        ----------
        pool_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/resources/ipv6-pools"

        ids = []
        for pool_id in pool_list:
            self.rest.json_resp_delete(f"{p_path}/{pool_id}")
            ids.append(pool_id)

        return ids
