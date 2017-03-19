import os
import sys
import json
import re
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
                if os.path.exists(path):
                    filename = path
                    break

        config = configparser.ConfigParser()
        config.read(filename)
        return config

    def load_ansible_staitc_inventory(self, config):
        static_inventory_path = config.get("ansible", "static_inventory_path")
        inventory = Inventory(DataLoader(), VariableManager(), static_inventory_path)
        return inventory

    def convert_to_dynamic_inventory(aelf, ansible_static_inventory):
        ansible_dynamic_inventory = dict()
        for v in ansible_static_inventory.get_groups():
            ansible_dynamic_inventory[v] = dict()
            group = ansible_static_inventory.get_group(v)
            group_hosts = group.get_hosts()
            if len(group_hosts):
                ansible_dynamic_inventory[v]["hosts"] = map(str, group_hosts)
            group_vars = group.get_vars()
            if len(group_vars):
                ansible_dynamic_inventory[v]["vars"] = group_vars
            group_children = group.child_groups
            if len(group_children):
                ansible_dynamic_inventory[v]["children"] = map(str, group_children)
        ansible_dynamic_inventory["_meta"] = dict()
        ansible_dynamic_inventory["_meta"]["hostvars"] = dict()
        for v in ansible_static_inventory.get_hosts():
            ansible_dynamic_inventory["_meta"]["hostvars"][v.name] = dict(v.vars)
        return ansible_dynamic_inventory

    def replace_with_consul_service(self, config, ansible_dynamic_inventory):
        consul_url = config.get("consul", "url")
        if len(consul_url) == 0:
            return ansible_dynamic_inventory

        replace_force_zero_hosts = config.getboolean("consul", "force_replace_zero_hosts")
        for v in ansible_group_dict.keys():
            res = requests.get(consul_url + "/catalog/service/" + v)
            if res.status_code == requests.codes.ok and (len(res.json()) or replace_force_zero_hosts is True):
                ansible_group_dict[v]["hosts"] = map(lambda x: x["ServiceAddress"], res.json())
        return ansible_dynamic_inventory

    def convert_to_plantuml(self, ansible_dynamic_inventory):
        plantuml_text = groups_text = hosts_text = ""
        group_name_regex = r'[^\w]'
        host_name_regex = r'[^\w\.]'
        for group_name, v in ansible_dynamic_inventory.iteritems():
            group_name = re.sub(group_name_regex, '_', group_name) # use character limit for plantuml
            if group_name == "_meta": # hostvars
                for host_name, _v in v["hostvars"].iteritems():
                    host_name = re.sub(host_name_regex, '_', host_name) # use character limit for plantuml
                    hosts_text += "object " + host_name
                    if _v:
                        hosts_text += " " + json.dumps(_v, indent=2, separators=("", ": "))
                    hosts_text += "\n"
            else: # group definition
                group_text = ""
                group_vars_text = ""
                if v.has_key("hosts"):
                    hostnames = list()
                    for hostname in v['hosts']:
                        hostnames.append(re.sub(host_name_regex, '_', hostname)) # use character limit for plantuml
                    group_join_text = "\n  " + group_name + "_hosts - "
                    group_text += group_join_text + group_join_text.join(hostnames) + "\n"
                if v.has_key("vars"):
                    group_text += "  class " + group_name + "_vars" + "\n"
                    group_vars_text += "class " + group_name + "_vars " + json.dumps(v['vars'], indent=2, separators=("", ": "))  + "\n"
                if v.has_key("children"):
                    for children_group_name in v['children']:
                        children_group_name = re.sub(group_name_regex, '_', children_group_name) # use character limit for plantuml
                        group_text += "  class " + group_name + "_children - " + children_group_name + "\n"
                groups_text += "package " + group_name + " {" + group_text + "}\n"
                groups_text += group_vars_text
        plantuml_text = hosts_text + "\n" + groups_text
        plantuml_text = "@startuml\n\n" + plantuml_text + "\n@enduml"
        return plantuml_text
