import os
import argparse
import json
from ansible_dynamic_inventory import AnsibleDynamicInventory


def _get_version():
    version_txt_path = os.path.abspath(os.path.dirname(__file__)) + '/__version__.txt'
    return open(version_txt_path).read().splitlines()[0]


def _parse_program_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--version', action='version', version=_get_version())
    parser.add_argument('--list', action='store_true', help='print dynamic inventory')
    parser.add_argument('--config', action='store', help='path to ansible_dynamic_inventory.ini')
    return vars(parser.parse_args())


def main():
    args = _parse_program_args()
    if args["list"]:
        adi = AnsibleDynamicInventory()
        config = adi.load_config(args['config'])
        ansible_static_inventory = adi.load_ansible_staitc_inventory(config)
        ansible_group_dict = adi.convert_to_dynamic_inventory(ansible_static_inventory)
        ansible_group_dict = adi.replace_with_consul_service(config, ansible_group_dict)
        ansible_dynamic_inventory = json.dumps(ansible_group_dict)
        print(ansible_dynamic_inventory)


if __name__ == '__main__':
    main()
