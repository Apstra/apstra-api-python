# Copyright 2020-present, Apstra, Inc. All rights reserved.
#
# This source code is licensed under End User License Agreement found in the
# LICENSE file at http://www.apstra.com/eula
import logging
from .aos import AosSubsystem, AosAPIError

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

    def get_all(self):
        """
        Return all logical devices configured from AOS

        Returns
        -------
            (obj) json response
        """
        ld_path = "/api/design/logical-devices"
        return self.rest.json_resp_get(ld_path)

    def get_logical_device(self, ld_id: str = None, ld_name: str = None):
        """
        Return an existing logical device by id or name
        Parameters
        ----------
        ld_id
            (str) ID of AOS logical device (optional)
        ld_name
            (str) Name or label of AOS logical device (optional)


        Returns
        -------
            (obj) json response
        """

        if ld_name:
            log_dev = self.get_all()
            if log_dev:
                for ld in log_dev:
                    if ld.get("display_name") == ld_name:
                        return ld
                raise AosAPIError(f"Logical Device {ld_name} not found")

        return self.rest.json_resp_get(f"/api/design/logical-devices/{ld_id}")

    def add_logical_device(self, ld_list: list):
        """
        Add one or more vni pools to AOS

        Parameters
        ----------
        ld_list
            (list) - list of json payloads

        Returns
        -------
            (list) logical device IDs
        """
        p_path = "/api/design/logical-devices"

        ids = []
        for ld in ld_list:
            item_id = self.rest.json_resp_post(uri=p_path, data=ld)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_logical_device(self, ld_list: str):
        """
        Delete one or more logical devices from AOS

        Parameters
        ----------
        ld_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/design/logical-devices"

        ids = []
        for ld_id in ld_list:
            self.rest.json_resp_delete(f"{p_path}/{ld_id}")
            ids.append(ld_id)

        return ids


class AosInterfaceMaps(AosSubsystem):
    """
    Manage AOS Interface Maps.
    This does not apply the logical device to a blueprint
    Use `blueprint.apply_configlet` to apply to blueprint
    """

    def get_all(self):
        """
        Return all interface maps configured from AOS

        Returns
        -------
            (obj) json response
        """
        im_path = "/api/design/interface-maps"
        return self.rest.json_resp_get(im_path)

    def get_interface_map(self, im_id: str = None, im_name: str = None):
        """
        Return an existing interface map by id or name
        Parameters
        ----------
        im_id
            (str) ID of AOS interface map (optional)
        im_name
            (str) Name or label of AOS interface map (optional)


        Returns
        -------
            (obj) json response
        """

        if im_name:
            int_maps = self.get_all()
            if int_maps:
                for im in int_maps:
                    if im.get("display_name") == im_name:
                        return im
                raise AosAPIError(f"Interface Map {im_name} not found")

        return self.rest.json_resp_get(f"/api/design/interface-maps/{im_id}")

    def add_interface_map(self, im_list: list):
        """
        Add one or more ip pools to AOS

        Parameters
        ----------
        im_list
            (list) - list of json payloads

        Returns
        -------
            (list) interface map IDs
        """
        p_path = "/api/design/interface-maps"

        ids = []
        for im in im_list:
            item_id = self.rest.json_resp_post(uri=p_path, data=im)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_interface_maps(self, im_list: str):
        """
        Delete one or more logical devices from AOS

        Parameters
        ----------
        im_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/design/interface-maps"

        ids = []
        for im_id in im_list:
            self.rest.json_resp_delete(f"{p_path}/{im_id}")
            ids.append(im_id)

        return ids


class AosRackTypes(AosSubsystem):
    """
    Manage AOS Rack Types
    This does not apply the rack type to a blueprint
    Use `blueprint.apply_rack_type` to apply to blueprint
    """

    def get_all(self):
        """
        Return all rack types configured from AOS

        Returns
        -------
            (obj) json response
        """
        r_path = "/api/design/rack-types"
        return self.rest.json_resp_get(r_path)

    def get_rack_type(self, rt_id: str = None, rt_name: str = None):
        """
        Return an existing rack type by id or name
        Parameters
        ----------
        rt_id
            (str) ID of AOS rack type (optional)
        rt_name
            (str) Name or label of AOS rack type (optional)


        Returns
        -------
            (obj) json response
        """

        if rt_name:
            rack_types = self.get_all()
            if rack_types:
                for rt in rack_types:
                    if rt.get("display_name") == rt_name:
                        return rt
                raise AosAPIError(f"Rack Type {rt_name} not found")

        return self.rest.json_resp_get(f"/api/design/rack-types/{rt_id}")

    def add_rack_type(self, rt_list: list):
        """
        Add one or more rack types to AOS

        Parameters
        ----------
        rt_list
            (list) - list of json payloads

        Returns
        -------
            (list) rack type IDs
        """
        p_path = "/api/design/rack-types"

        ids = []
        for im in rt_list:
            item_id = self.rest.json_resp_post(uri=p_path, data=im)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_rack_type(self, rt_list: str):
        """
        Delete one or more rack types from AOS

        Parameters
        ----------
        rt_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/design/rack-types"

        ids = []
        for rt_id in rt_list:
            self.rest.json_resp_delete(f"{p_path}/{rt_id}")
            ids.append(rt_id)

        return ids


class AosTemplates(AosSubsystem):
    """
    Manage AOS Templates
    This does not apply the template to an existing blueprint
    built from the given template.
    """

    def get_all(self):
        """
        Return all blueprint templates configured from AOS

        Returns
        -------
            (obj) json response
        """
        t_path = "/api/design/templates"
        return self.rest.json_resp_get(t_path)

    def get_template(self, temp_id: str = None, temp_name: str = None):
        """
        Return an existing template by id or name
        Parameters
        ----------
        temp_id
            (str) ID of AOS template (optional)
        temp_name
            (str) Name or label of AOS template (optional)


        Returns
        -------
            (obj) json response
        """

        if temp_name:
            templates = self.get_all()
            if templates:
                for template in templates:
                    if template.get("display_name") == temp_name:
                        return template
                raise AosAPIError(f"Template {temp_name} not found")

        return self.rest.json_resp_get(f"/api/design/templates/{temp_id}")

    def add_template(self, template_list: list):
        """
        Add one or more templates to AOS

        Parameters
        ----------
        template_list
            (list) - list of json payloads

        Returns
        -------
            (list) template IDs
        """
        t_path = "/api/design/templates"

        ids = []
        for template in template_list:
            item_id = self.rest.json_resp_post(uri=t_path, data=template)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_templates(self, temp_list: str):
        """
        Delete one or more templates from AOS

        Parameters
        ----------
        temp_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/design/rack-types"

        ids = []
        for temp_id in temp_list:
            self.rest.json_resp_delete(f"{p_path}/{temp_id}")
            ids.append(temp_id)

        return ids


class AosConfiglets(AosSubsystem):
    """
    Manage AOS configlets.
    This does not apply the configlet to a blueprint
    Use `blueprint.apply_configlet` to apply to blueprint
    """

    def get_all(self):
        """
        Return all configlets configured from AOS

        Returns
        -------
            (obj) json response
        """
        t_path = "/api/design/configlets"
        return self.rest.json_resp_get(t_path)

    def get_configlet(self, conf_id: str = None, conf_name: str = None):
        """
        Return an existing configlet by id or name
        Parameters
        ----------
        conf_id
            (str) ID of AOS configlet (optional)
        conf_name
            (str) Name or label of AOS configlet (optional)


        Returns
        -------
            (obj) json response
        """

        if conf_name:
            configlets = self.get_all()
            if configlets:
                for configlet in configlets:
                    if configlet.get("display_name") == conf_name:
                        return configlet
                raise AosAPIError(f"Configlet {conf_name} not found")

        return self.rest.json_resp_get(f"/api/design/configlets/{conf_id}")

    def add_configlet(self, conf_list):
        """
        Add one or more vni pools to AOS

        Parameters
        ----------
        conf_list
            (list) - list of json payloads

        Returns
        -------
            (list) configlet IDs
        """
        p_path = "/api/design/configlets"

        ids = []
        for conf in conf_list:
            item_id = self.rest.json_resp_post(uri=p_path, data=conf)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_configlet(self, conf_list: str):
        """
        Delete one or more configlets from AOS

        Parameters
        ----------
        conf_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/design/configlets"

        ids = []
        for conf_id in conf_list:
            self.rest.json_resp_delete(f"{p_path}/{conf_id}")
            ids.append(conf_id)

        return ids


class AosPropertySets(AosSubsystem):
    """
    Manage AOS property-set.
    This does not apply the property-set to a blueprint
    Use `blueprint.apply_property_set` to apply to blueprint
    """

    def get_all(self):
        """
        Return all property sets configured from AOS

        Returns
        -------
            (obj) json response
        """
        t_path = "/api/design/property-sets"
        return self.rest.json_resp_get(t_path)

    def get_property_set(self, ps_id: str = None, ps_name: str = None):
        """
        Return an existing property set by id or name
        Parameters
        ----------
        ps_id
            (str) ID of AOS property set (optional)
        ps_name
            (str) Name or label of AOS property set (optional)


        Returns
        -------
            (obj) json response
        """

        if ps_name:
            property_sets = self.get_all()
            if property_sets:
                for ps in property_sets:
                    if ps.get("display_name") == ps_name:
                        return ps
                raise AosAPIError(f"Configlet {ps_name} not found")

        return self.rest.json_resp_get(f"/api/design/property-sets/{ps_id}")

    def add_property_set(self, ps_list):
        """
        Add one or more vni pools to AOS

        Parameters
        ----------
        ps_list
            (list) - list of json payloads

        Returns
        -------
            (list) property set IDs
        """
        p_path = "/api/design/property-sets"

        ids = []
        for ps in ps_list:
            item_id = self.rest.json_resp_post(uri=p_path, data=ps)
            if item_id:
                ids.append(item_id)

        return ids

    def delete_property_set(self, ps_list: str):
        """
        Delete one or more property sets from AOS

        Parameters
        ----------
        ps_list
            (list) - list of ids

        Returns
        -------
            (list) deleted IDs
        """
        p_path = "/api/design/property-sets"

        ids = []
        for ps_id in ps_list:
            self.rest.json_resp_delete(f"{p_path}/{ps_id}")
            ids.append(ps_id)

        return ids
