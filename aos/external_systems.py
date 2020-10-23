# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
from .aos import AosSubsystem

logger = logging.getLogger(__name__)


class ExternalSystems(AosSubsystem):
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

    def get_external_routers(self):
        """
        Return all external routers configured from AOS

        Returns
        -------
            (obj) json response
        """
        er_path = "/api/resources/external-routers"
        return self.rest.json_resp_get(er_path)
