#!/usr/bin/env python

import os, argparse, requests, json, re
import configparser
from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory

def _get_version():
    version_txt_path = os.path.abspath(os.path.dirname(__file__)) + '/__version__.txt'
    return open(version_txt_path).read().splitlines()[0]

def _parse_program_args():
    description = u"{0} [Options]\nDetailed options -h or --help".format(__file__)
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--version', action='version', version=_get_version())
    parser.add_argument('--list', action='store_true', help='print dynamic inventory')
    return vars(parser.parse_args())

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
    consul_url = config.get("consul", "url")
    if len(consul_url) == 0:
        return ansible_group_dict

    replace_force_zero_hosts = config.getboolean("consul", "force_replace_zero_hosts")
    for v in ansible_group_dict.keys():
        res = requests.get(consul_url + "/catalog/service/" + v)
        if res.status_code == requests.codes.ok and (len(res.json()) or replace_force_zero_hosts == True):
            ansible_group_dict[v]["hosts"] = map(lambda x: x["ServiceAddress"], res.json())
    return ansible_group_dict

def main():
    args = _parse_program_args()
    if args["list"]:
        config_path = "/etc/ansible_dynamic_inventory.ini"
        config = _load_config(config_path)
        ansible_static_inventory = _load_ansible_staitc_inventory(config)
        ansible_group_dict = _get_ansible_group_hosts(config, ansible_static_inventory)
        ansible_group_dict = _replace_with_consul_service(config, ansible_group_dict)
        ansible_dynamic_inventory = json.dumps(ansible_group_dict)
        print(ansible_dynamic_inventory)

if __name__ == '__main__':
    main()
