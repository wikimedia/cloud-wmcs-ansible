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
module: etcd_cluster_info
short_description: Get information from the etcd cluster about itself
description:
  - Get information from the etcd cluster

options:
  endpoints:
    description:
      - Comma-separated list of endpoints to connect to (already existing etcd
        members), Note that there should be no spaces!
    type: str
    required: true
  ca_file:
    description: Path to the ca file to use
    type: str
    required: false
    default: /etc/etcd/ssl/ca.pem
  cert_file:
    description: Path to the cert file to use
    type: str
    required: true
  key_file:
    description: Path to the key file to use
    type: str
    required: true

requirements:
  - "python >= 3.6"
'''

EXAMPLES = '''
- name: Get cluster info, note the delegate_to and the ca_file/cert_file
  delegate_to: tools-k8s-etcd-2.toolsbeta.eqiad1.wikimedia.cloud
  wikimedia.wmcs.etcd_cluster_info:
    endpoints:  https://tools-k8s-etcd-1.toolsbeta.eqiad1.wikimedia.cloud:2379,https://tools-k8s-etcd-2.toolsbeta.eqiad1.wikimedia.cloud:2379
    ca_file: /etc/etcd/ssl/ca.pem
    cert_file: /etc/etcd/ssl/tools-k8s-etcd-2.toolsbeta.eqiad1.wikimedia.cloud.pem
    key_file: /etc/etcd/ssl/tools-k8s-etcd-2.toolsbeta.eqiad1.wikimedia.cloud.priv

'''

RETURN = '''
members:
    description: Dictionary with the list of members and some info.
    returned: On success
    type: complex
    contains:
        clientURLs:
            description: The url that clients should use to connect to this node.
            type: str
            sample: "https://toolsbeta-test-k8s-etcd-6.toolsbeta.eqiad1.wikimedia.cloud:2379"
        isLeader:
            description: |
                True if this node is currently the leader, False otherwise.
            type: bool
        member_id:
            description: |
                UID of this node, this is also the key the dict is under.
            type: str
            sample: "5208bbf5c00e7cdf"
        peerURLs:
            description: |
                The url other nodes in the cluster should use to connect to this one.
            type: str
            sample: "https://toolsbeta-test-k8s-etcd-6.toolsbeta.eqiad1.wikimedia.cloud:2380"
        status:
            description: Current status of the node.
            type: str
            sample: "up"
'''

__metaclass__ = type
import yaml
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import jsonify
from ansible_collections.wikimedia.wmcs.plugins.module_utils.etcd import (
    get_common_etcdctl_args_specs,
    get_cluster_info,
)


def main():
    """ Module entry point """

    module = AnsibleModule(
        get_common_etcdctl_args_specs(),
        supports_check_mode=True,
    )
    cluster_info = get_cluster_info(module=module)
    module.exit_json(changed=False, members=cluster_info)


if __name__ == '__main__':
    main()
