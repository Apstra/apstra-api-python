# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
import requests

from .aos import AosRestAPI, AosAuth
from .blueprint import AosBlueprint
from .devices import AosDevices
from .design import AosDesign
from .resources import AosResources
from .external_systems import AosExternalSystems
from .telemetry import AosTelemetryManager

logger = logging.getLogger(__name__)


class AosClient:
    """
    Establish, maintain and interact with an AOS server session

    Parameters
    ----------
    protocol
        (str) https or http connection to AOS api
    host
        (str) AOS server url or ip address
    port
        (int) AOS server port (ex 80, 443)
    session
        (obj) Established session with AOS server


    :class:`aos.blueprint.AosBlueprint` - Manage AOS blueprints

    :class:`aos.devices.AosDevices` - Manage AOS controlled devices and agents

    :class:`aos.design.AosDesign` - Manage AOS Design elements

    :class:`aos.resources.AosResources` - Manage AOS resource pools

    :class:`aos.external_systems.AosExternalSystems`
    - Manage AOS external system integrations
    """

    def __init__(
        self, protocol: str, host: str, port: int, session: requests.Session = None
    ):
        self.session = session
        self.rest = AosRestAPI(protocol, host, port, session)
        self.auth = AosAuth(self.rest)
        self.blueprint = AosBlueprint(self.rest)
        self.devices = AosDevices(self.rest)
        self.design = AosDesign(self.rest)
        self.resources = AosResources(self.rest)
        self.external_systems = AosExternalSystems(self.rest)
        self.telemetry_mgr = AosTelemetryManager(self.rest)
