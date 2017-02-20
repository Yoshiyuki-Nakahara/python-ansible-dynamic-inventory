#!/usr/bin/env python

import os, argparse, requests, json
import configparser
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory

def _load_config(filename):
    config = configparser.ConfigParser()
    config.read(filename)
    return config

def _load_ansible_staitc_inventory(config):
    filename = config.get("ansible", "static_inventory_path")
    inventory = Inventory(
        loader = DataLoader(),
        variable_manager = VariableManager(),
        host_list = filename
    )
    return inventory

def _get_ansible_group_hosts(config, ansible_static_inventory):
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

def _replace_with_consul_service(config, ansible_group_dict):
    consu_url = config.get("consul", "url")
    if len(consu_url) == 0:
        return ansible_group_dict
    replace_force_zero_hosts = config.getboolean("consul", "force_replace_zero_hosts")
    for v in ansible_group_dict.keys():
        url = config.get("consul", "url") + "/catalog/service/" + v
        res = requests.get(url).json()
        if len(res) or replace_force_zero_hosts != False:
            ansible_group_dict[v]["hosts"] = map(lambda x: x["ServiceAddress"], res)
    return ansible_group_dict

def main():
    config_path = "/etc/ansible_dynamic_inventory.ini"
    config = _load_config(config_path)
    ansible_static_inventory = _load_ansible_staitc_inventory(config)
    ansible_group_dict = _get_ansible_group_hosts(config, ansible_static_inventory)
    ansible_group_dict = _replace_with_consul_service(config, ansible_group_dict)
    ansible_dynamic_inventory = json.dumps(ansible_group_dict)
    print ansible_dynamic_inventory

if __name__ == '__main__':
    main()
