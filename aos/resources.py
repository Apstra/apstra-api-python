# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
from .aos import AosSubsystem

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

    def get_asn_pools(self):
        """
        Return all asn pools configured from AOS

        Returns
        -------
            (obj) json response
        """
        a_path = '/api/resources/asn-pools'
        return self.rest.json_resp_get(a_path)


class AosVniPools(AosSubsystem):
    """
    Manage AOS VNI Pools.
    This does not apply the resource to a blueprint
    See `aos.blueprint` to apply to blueprint
    """
    def get_vni_pools(self):
        """
        Return all vni pools configured from AOS

        Returns
        -------
            (obj) json response
        """
        v_path = '/api/resources/vni-pools'
        return self.rest.json_resp_get(v_path)


class AosIpv4Pools(AosSubsystem):
    """
    Manage AOS IPv4 address Pools.
    This does not apply the resource to a blueprint
    See `aos.blueprint` to apply to blueprint
    """

    def get_ip_pools(self):
        """
        Return all ip pools from AOS

        Returns
        -------
            (obj) json response
        """
        ip_path = "/api/resources/ip-pools"
        return self.rest.json_resp_get(ip_path)

    def get_ip_pool_by_name(self, name: str):
        """
        Return an existing IP pool by pool name

        Returns
        -------
            (obj) json response
        """
        pools = self.get_ip_pools()

        for pool in pools:
            if pool.get("display_name") == name:
                return pool

        return None


class AosIpv6Pools(AosSubsystem):
    """
    Manage AOS IPv6 address Pools.
    This does not apply the resource to a blueprint
    See `aos.blueprint` to apply to blueprint
    """

    def get_ip_pools(self):
        """
        Return all ip pools from AOS

        Returns
        -------
            (obj) json response
        """
        ip_path = "/api/resources/ipv6-pools"
        return self.rest.json_resp_get(ip_path)

    def get_ip_pool_by_name(self, name: str):
        """
        Return an existing IP pool by pool name

        Returns
        -------
            (obj) json response
        """
        pools = self.get_ip_pools()

        for pool in pools:
            if pool.get("display_name") == name:
                return pool

        return None
