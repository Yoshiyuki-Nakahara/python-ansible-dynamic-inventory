import os
import sys
import requests
import configparser
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory


class AnsibleDynamicInventory:

    def load_config(self, filename):
        if filename is None:
            for v in sys.path:
                path = v + '/ansible_dynamic_inventory/ansible_dynamic_inventory.ini'
                if os.path.exists( path ):
                    filename = path
                    break
        config = configparser.ConfigParser()
        config.read(filename)
        return config


    def load_ansible_staitc_inventory(self, config):
        filename = config.get("ansible", "static_inventory_path")
        inventory = Inventory(DataLoader(), VariableManager(), filename)
        return inventory


    def convert_to_dynamic_inventory(aelf, ansible_static_inventory):
        ansible_groups = dict()
        for v in ansible_static_inventory.get_groups():
            ansible_groups[v] = dict()
            group = ansible_static_inventory.get_group(v)
            group_hosts = group.get_hosts()
            if len(group_hosts):
                ansible_groups[v]["hosts"] = map(str, group_hosts)
            group_vars = group.get_vars()
            if len(group_vars):
                ansible_groups[v]["vars"] = group_vars
            group_children = group.child_groups
            if len(group_children):
                ansible_groups[v]["children"] = map(str, group_children)
        return ansible_groups


    def replace_with_consul_service(self, config, ansible_group_dict):
        consul_url = config.get("consul", "url")
        if len(consul_url) == 0:
            return ansible_group_dict

        replace_force_zero_hosts = config.getboolean("consul", "force_replace_zero_hosts")
        for v in ansible_group_dict.keys():
            res = requests.get(consul_url + "/catalog/service/" + v)
            if res.status_code == requests.codes.ok and (len(res.json()) or replace_force_zero_hosts is True):
                ansible_group_dict[v]["hosts"] = map(lambda x: x["ServiceAddress"], res.json())
        return ansible_group_dict
