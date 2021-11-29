# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
from dataclasses import dataclass
from .aos import AosSubsystem
from typing import Optional, List, Generator

logger = logging.getLogger(__name__)


class AosExternalSystems(AosSubsystem):
    """
    Management of AOS Resource elements:
    - Providers
    - External Routers
    - Virtual Infra Managers
    """

    def __init__(self, rest):
        super().__init__(rest)
        self.external_router = AosExternalRouter(rest)


# Resources
@dataclass
class AosResource:
    display_name: str
    id: str


@dataclass
class ExternalRouter(AosResource):
    asn: int
    address: str

    @classmethod
    def from_json(cls, d):
        if d is None:
            return None
        return ExternalRouter(
            id=d["id"],
            display_name=d.get("display_name", ""),
            asn=d.get("asn"),
            address=d.get("address"),
        )


class AosExternalRouter(AosSubsystem):
    def create(self, name: str, asn: int, address: str) -> ExternalRouter:
        ext_rtr = {
            "display_name": name,
            "id": name,
            "asn": asn,
            "address": address,
        }

        created = self.rest.json_resp_post(
            "/api/resources/external-routers", data=ext_rtr
        )
        return self.get(created["id"])

    def delete(self, ext_rtr_id: str) -> None:
        self.rest.delete(f"/api/resources/external-routers/{ext_rtr_id}")

    def get(self, rtr_id: str) -> Optional[ExternalRouter]:
        return ExternalRouter.from_json(
            self.rest.json_resp_get(f"/api/resources/external-routers/{rtr_id}")
        )

    def iter_all(self) -> Generator[ExternalRouter, None, None]:
        rtrs = self.rest.json_resp_get("/api/resources/external-routers")
        if rtrs:
            for r in rtrs["items"]:
                yield ExternalRouter.from_json(r)

    def find_by_name(self, rtr_name: str) -> List[ExternalRouter]:
        return [r for r in self.iter_all() if r.display_name == rtr_name]
