# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
from dataclasses import dataclass
from .aos import AosSubsystem, AosAPIError
from typing import Optional, List, Generator

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
        super().__init__(rest)
        self.asn_pools = AosAsnPool(rest)
        self.vni_pools = AosVniPool(rest)
        self.ipv4_pools = AosIPPool(rest)
        self.ipv6_pools = AosIPv6Pool(rest)


@dataclass
class AosResource:
    display_name: str
    id: str


@dataclass
class PoolSubnet:
    network: str

    @classmethod
    def from_json(cls, d: dict):
        return PoolSubnet(
            network=d["network"],
        )


@dataclass
class IPPool(AosResource):
    subnets: List[PoolSubnet]

    @classmethod
    def from_json(cls, d: dict):
        return IPPool(
            display_name=d["display_name"],
            subnets=[PoolSubnet.from_json(s) for s in d["subnets"]],
            id=d["id"],
        )


class AosIPPool(AosSubsystem):
    def create(
        self,
        name: str,
        subnets: List[str],
        tags: Optional[List[str]] = None,
    ) -> IPPool:
        if tags is None:
            tags = []

        ip_pool = {
            "subnets": [{"network": net} for net in subnets],
            "tags": tags,
            "display_name": name,
            "id": name.replace(" ", "-"),
        }

        created = self.rest.json_resp_post("/api/resources/ip-pools", data=ip_pool)
        return self.get(created["id"])

    def delete(self, pool_id: str) -> None:
        self.rest.delete(f"/api/resources/ip-pools/{pool_id}")

    def get(self, pool_id: str) -> IPPool:
        return IPPool.from_json(
            self.rest.json_resp_get(f"/api/resources/ip-pools/{pool_id}")
        )

    def iter_all(self) -> Generator[IPPool, None, None]:
        pools = self.rest.json_resp_get("/api/resources/ip-pools")
        if pools:
            for p in pools["items"]:
                yield IPPool.from_json(p)

    def find_by_name(self, name: str) -> List[IPPool]:
        return [p for p in self.iter_all() if p.display_name == name]


class AosIPv6Pool(AosSubsystem):
    def create(
        self,
        name: str,
        subnets: List[str],
        tags: Optional[List[str]] = None,
    ) -> IPPool:
        if tags is None:
            tags = []

        ip_pool = {
            "subnets": [{"network": net} for net in subnets],
            "tags": tags,
            "display_name": name,
            "id": name,
        }

        created = self.rest.json_resp_post("/api/resources/ipv6-pools", data=ip_pool)
        return self.get(created["id"])

    def delete(self, pool_id: str) -> None:
        self.rest.delete(f"/api/resources/ipv6-pools/{pool_id}")

    def get(self, pool_id: str) -> IPPool:
        return IPPool.from_json(
            self.rest.json_resp_get(f"/api/resources/ipv6-pools/{pool_id}")
        )

    def iter_all(self) -> Generator[IPPool, None, None]:
        pools = self.rest.json_resp_get("/api/resources/ipv6-pools")
        if pools:
            for p in pools["items"]:
                yield IPPool.from_json(p)

    def find_by_name(self, name: str) -> List[IPPool]:
        return [p for p in self.iter_all() if p.display_name == name]


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
        resp = self.rest.json_resp_get(ip_path)
        return resp["items"]

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
            self.rest.delete(f"{p_path}/{pool_id}")
            ids.append(pool_id)

        return ids


@dataclass
class Range:
    first: int
    last: int

    @classmethod
    def from_json(cls, d: dict):
        return Range(first=d["first"], last=d["last"])


@dataclass
class AsnPool(AosResource):
    ranges: List[Range]

    @classmethod
    def from_json(cls, d):
        if d is None:
            return None
        return AsnPool(
            id=d["id"],
            display_name=d.get("display_name", ""),
            ranges=[Range.from_json(r) for r in d["ranges"]],
        )


class AosAsnPool(AosSubsystem):
    def create(self, name: str, ranges: List[Range]) -> AsnPool:
        asn_pool = {
            "display_name": name,
            "id": name,
            "ranges": [{"first": r.first, "last": r.last} for r in ranges],
        }

        created = self.rest.json_resp_post("/api/resources/asn-pools", data=asn_pool)
        return self.get(created["id"])

    def delete(self, pool_id: str) -> None:
        self.rest.delete(f"/api/resources/asn-pools/{pool_id}")

    def get(self, pool_id: str) -> Optional[AsnPool]:
        return AsnPool.from_json(
            self.rest.json_resp_get(f"/api/resources/asn-pools/{pool_id}")
        )

    def iter_all(self) -> Generator[AsnPool, None, None]:
        pools = self.rest.json_resp_get("/api/resources/asn-pools")
        if pools:
            for p in pools["items"]:
                yield AsnPool.from_json(p)

    def find_by_name(self, pool_name: str) -> List[AsnPool]:
        return [p for p in self.iter_all() if p.display_name == pool_name]


@dataclass
class VniPool(AosResource):
    ranges: List[Range]

    @classmethod
    def from_json(cls, d):
        if d is None:
            return None
        return VniPool(
            id=d["id"],
            display_name=d.get("display_name", ""),
            ranges=[Range.from_json(r) for r in d["ranges"]],
        )


class AosVniPool(AosSubsystem):
    def create(self, name: str, ranges: List[Range]) -> VniPool:
        vni_pool = {
            "display_name": name,
            "id": name,
            "ranges": [{"first": r.first, "last": r.last} for r in ranges],
        }

        created = self.rest.json_resp_post("/api/resources/vni-pools", data=vni_pool)
        return self.get(created["id"])

    def delete(self, pool_id: str) -> None:
        self.rest.delete(f"/api/resources/vni-pools/{pool_id}")

    def get(self, pool_id: str) -> Optional[VniPool]:
        return VniPool.from_json(
            self.rest.json_resp_get(f"/api/resources/vni-pools/{pool_id}")
        )

    def iter_all(self) -> Generator[VniPool, None, None]:
        pools = self.rest.json_resp_get("/api/resources/vni-pools")
        if pools:
            for p in pools["items"]:
                yield VniPool.from_json(p)

    def find_by_name(self, pool_name: str) -> List[VniPool]:
        return [p for p in self.iter_all() if p.display_name == pool_name]
