#!/usr/bin/python
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
from __future__ import (absolute_import, division, print_function)

DOCUMENTATION = '''
---
author:
  - David Caro (@david-caro)
module: k8s_control_apiserver_etcd_servers
short_description: Update the etcd servers in the apiserver.yml file on a k8s control node.
description:
  - Update the etcd servers in the apiserver.yml file on a k8s control node.

options:
  etcd_members:
    description:
      - List of endpoints (full url) for each of the etcd members.
    required: true
    type: list
    elements: str
  apiserver_yaml_path:
    description:
      - Path to the yaml file with the apiserver definition
    required: false
    type: str
    default: /etc/kubernetes/manifests/kube-apiserver.yaml

requirements:
  - "python >= 3.6"
'''

EXAMPLES = '''
- name: Update etcd members for the apiserver
  delegate_to: tools-k8s-control-2.toolsbeta.eqiad1.wikimedia.cloud
  wikimedia.wmcs.k8s_control_apiserver_etcd_servers:
    etcd_members:
        - https://tools-k8s-etcd-1.toolsbeta.eqiad1.wikimedia.cloud:2379
        - https://tools-k8s-etcd-2.toolsbeta.eqiad1.wikimedia.cloud:2379
    apiserver_yaml_path: /etcd/custompath/apiserver.yaml
'''

RETURN = '''
'''

__metaclass__ = type
import yaml
import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import jsonify
from ansible_collections.wikimedia.wmcs.plugins.module_utils.etcd import (
    get_common_etcdctl_args_specs,
    get_cluster_info,
)


def main():
    """ Module entry point """

    argument_spec = {
        "etcd_members": {"type": "list", "elements": "str", "required": True},
        "apiserver_yaml_path": {"type": "str", "required": False, "default": "/etc/kubernetes/manifests/kube-apiserver.yaml"},
    }
    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
    )

    etcd_members = module.params.get('etcd_members')
    apiserver_yaml_path = module.params.get('apiserver_yaml_path')

    if not os.path.exists(apiserver_yaml_path):
        module.fail_json(message=f"{apiserver_yaml_path} does not exist.")

    new_etcd_members_arg = "--etcd-servers=" + ",".join(sorted(etcd_members))
    apiserver_yaml = yaml.load(open(apiserver_yaml_path))

    # we expect the container to be the first and only in the spec
    command_args = apiserver_yaml['spec']['containers'][0]['command']
    for index, arg in enumerate(command_args):
        if arg.startswith('--etcd-servers='):
            if arg == new_etcd_members_arg:
                module.exit_json(changed=False, old_members=arg, new_members=new_etcd_members_arg)
            else:
                command_args[index] = new_etcd_members_arg
                with open(apiserver_yaml_path, 'w') as apiserver_fd:
                    apiserver_fd.write(yaml.dump(apiserver_yaml))

                module.exit_json(changed=True, old_members=arg, new_members=new_etcd_members_arg)

    module.fail_json(
        changed=False,
        message=(
            "Unable to find the etcd-servers command arg in the "
            f"{apiserver_yaml_path} definition file"
        ),
    )


if __name__ == '__main__':
    main()
