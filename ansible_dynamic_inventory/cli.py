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
    parser.add_argument('--plantuml', action='store_true', help='print plantuml format')
    parser.add_argument('--config', action='store', help='path to ansible_dynamic_inventory.ini')
    args = vars(parser.parse_args())
    if args['config'] is None and 'ANSIBLE_DYNAMIC_INVENTORY_INI_PATH' in os.environ:
        args['config'] = os.environ['ANSIBLE_DYNAMIC_INVENTORY_INI_PATH']
    return args


def main():
    args = _parse_program_args()
    adi = AnsibleDynamicInventory(args['config'])
    ansible_dynamic_inventory = adi.get_inventory()
    if args["plantuml"]:
        plantuml_text = adi.convert_to_plantuml(ansible_dynamic_inventory)
        print(plantuml_text)
    else:
        print(json.dumps(ansible_dynamic_inventory, indent=2))


if __name__ == '__main__':
    main()
