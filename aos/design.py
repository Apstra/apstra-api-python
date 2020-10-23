# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
from .aos import AosSubsystem

logger = logging.getLogger(__name__)


class AosDesign(AosSubsystem):
    """
    Management of AOS design elements:
    - Logical Devices
    - Interface Maps
    - Rack Types
    - Templates
    - Configlets
    - Property Sets
    - TCP/UDP Ports
    """

    def __init__(self, rest):
        self.logical_devices = AosLogicalDevices(rest)
        self.interface_maps = AosInterfaceMaps(rest)
        self.rack_types = AosRackTypes(rest)
        self.templates = AosTemplates(rest)
        self.configlets = AosConfiglets(rest)
        self.property_sets = AosPropertySets(rest)


class AosLogicalDevices(AosSubsystem):
    """
    Manage AOS Logical Devices.
    This does not apply the logical device to a blueprint
    Use `blueprint.apply_configlet` to apply to blueprint
    """
    def get_logical_devices(self):
        """
        Return all logical devices configured from AOS

        Returns
        -------
            (obj) json response
        """
        ld_path = '/api/design/logical-devices'
        return self.rest.json_resp_get(ld_path)


class AosInterfaceMaps(AosSubsystem):
    """
    Manage AOS Interface Maps.
    This does not apply the logical device to a blueprint
    Use `blueprint.apply_configlet` to apply to blueprint
    """
    def get_interface_maps(self):
        """
        Return all interface maps configured from AOS

        Returns
        -------
            (obj) json response
        """
        im_path = '/api/design/interface-maps'
        return self.rest.json_resp_get(im_path)


class AosRackTypes(AosSubsystem):
    """
    Manage AOS Rack Types
    This does not apply the rack type to a blueprint
    Use `blueprint.apply_rack_type` to apply to blueprint
    """
    def get_rack_types(self):
        """
        Return all rack types configured from AOS

        Returns
        -------
            (obj) json response
        """
        r_path = '/api/design/rack-types'
        return self.rest.json_resp_get(r_path)


class AosTemplates(AosSubsystem):
    """
    Manage AOS Templates
    This does not apply the template to an existing blueprint
    built from the given template.
    """
    def get_templates(self):
        """
        Return all blueprint templates configured from AOS

        Returns
        -------
            (obj) json response
        """
        t_path = '/api/design/templates'
        return self.rest.json_resp_get(t_path)


class AosConfiglets(AosSubsystem):
    """
    Manage AOS configlets.
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


class AosPropertySets(AosSubsystem):
    """
    Manage AOS property-set.
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
