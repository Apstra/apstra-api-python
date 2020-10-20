# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
from .aos import AosSubsystem

logger = logging.getLogger(__name__)


class AosConfiglet(AosSubsystem):
    """
    AOS configlet create, modify, delete.
    This does not apply the configlet to a blueprint
    Use `blueprint.apply_configlet` to apply to blueprint
    """

    def create(self, payload):
        """
        Create new configlet in AOS.
        Parameters
        ----------
        payload
            (dict) json payload of generated configlet

        Returns
        -------
        (obj) RestAPI response
        """
        c_path = "/api/design/configlets"

        return self.rest.json_resp_post(c_path, data=payload)


class AosPropertySet(AosSubsystem):
    """
    AOS property-set create, modify, delete.
    This does not apply the property-set to a blueprint
    Use `blueprint.apply_property_set` to apply to blueprint
    """

    def create(self, payload):
        """
        Create new property-set in AOS.
        Parameters
        ----------
        payload
            (dict) json payload of generated property-set

        Returns
        -------
        (obj) RestAPI response
        """
        ps_path = "/api/property-sets"

        return self.rest.json_resp_post(ps_path, data=payload)
