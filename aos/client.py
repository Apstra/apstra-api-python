# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
import requests
from .aos import AosRestAPI, AosAuth
from .blueprint import AosBlueprint
from .devices import SystemAgents
from .resources import AosConfiglet, AosPropertySet

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


    :class:`aos.blueprint.AosBlueprint` - AOS blueprint specific actions

    :class:`aos.devices.SystemAgents` - AOS system-agent create, modify, delete

    :class:`aos.resources.AosConfiglet` - AOS configlet create, modify, delete

    :class:`aos.resources.AosPropertySet` -AOS property-set create, modify, delete
    """

    def __init__(
        self, protocol: str, host: str, port: int, session: requests.Session = None
    ):
        self.session = session
        self.rest = AosRestAPI(protocol, host, port, session)
        self.auth = AosAuth(self.rest)
        self.blueprint = AosBlueprint(self.rest)
        self.system_agent = SystemAgents(self.rest)
        self.configlet = AosConfiglet(self.rest)
        self.property_set = AosPropertySet(self.rest)
