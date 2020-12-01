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
module: etcd_member
short_description: Manage members of the etcd cluster
description:
    - Manage members of the etcd cluster

options:
  endpoints:
    description: |
        Comma-separated list of endpoints to connect to (already existing etcd
        members), Note that there should be no spaces!
    required: true
    type: str
  ca_file:
    description: Path to the ca file to use
    required: false
    default: /etc/etcd/ssl/ca.pem
    type: str
  cert_file:
    description: Path to the cert file to use
    required: true
    type: str
  key_file:
    description: Path to the key file to use
    required: true
    type: str
  ensure:
    description: absent or present (default)
    required: false
    type: str
    default: present
    choices:
        - present
        - absent
  member_fqdn:
    description: Name of the member
    required: true
    type: str
  member_peer_url:
    description: |
      URL of the member endpoint including protocol and port, will
      use https://<member_fqdn>:2380 by default
    required: false
    type: str
    default: ""

requirements:
  - "python >= 3.6"
'''

EXAMPLES = '''
- name: Ensure a member is present with the given url, note the delegate_to and the ca_file/cert_file
  delegate_to: toolsbeta-test-k8s-etcd-2.toolsbeta.eqiad1.wikimedia.cloud
  wikimedia.wmcs.etcd_member:
    ensure: present
    endpoints:  https://toolsbeta-test-k8s-etcd-1.toolsbeta.eqiad1.wikimedia.cloud:2379,https://toolsbeta-test-k8s-etcd-2.toolsbeta.eqiad1.wikimedia.cloud:2379
    ca_file: /etc/etcd/ssl/ca.pem
    cert_file: /etc/etcd/ssl/toolsbeta-test-k8s-etcd-2.toolsbeta.eqiad1.wikimedia.cloud.pem
    key_file: /etc/etcd/ssl/toolsbeta-test-k8s-etcd-2.toolsbeta.eqiad1.wikimedia.cloud.priv
    member_fqdn: toolsbeta-test-k8s-etcd-4.toolsbeta.wikimedia.cloud
    member_peer_url: https://toolsbeta-test-k8s-etcd-4.toolsbeta.wikimedia.cloud:2380

'''

RETURN = '''
new_member_id:
    description: |
        The id of the new member (or the existing one if it was already there).
    returned: On success
    type: str
    sample: "a35238e603a2372c"
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
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.wikimedia.wmcs.plugins.module_utils.etcd import (
    get_common_etcdctl_args_specs,
    get_etcdctl_args,
    get_cluster_info,
)


def get_member_or_none(members, member_name, member_peer_url):
    return next(
        (
            member
            for member in members.values()
            if (
                'name' in member and member['name'] == member_name
                # in case the member is not started, it does not show the name,
                # just the peer url
                or 'name' not in member and member['peerURLs'] == member_peer_url
            )
        ),
        None,
    )


def main():
    """ Module entry point """

    module = AnsibleModule(
        get_common_etcdctl_args_specs(
            ensure={
                "type": "str",
                "required": False,
                "default": "present",
                "choices": ["present", "absent"],
            },
            member_fqdn={"type": "str", "required": True},
            member_peer_url={"type": "str", "required": False, "default": ""},
        ),
        supports_check_mode=True,
    )
    ensure = module.params.get("ensure")
    member_fqdn = module.params.get("member_fqdn")
    member_peer_url = module.params.get("member_peer_url")
    if not member_peer_url:
        member_peer_url = f"https://{member_fqdn}:2380"

    before_members = get_cluster_info(module)
    current_entry = get_member_or_none(
        members=before_members,
        member_name=member_fqdn,
        member_peer_url=member_peer_url,
    )
    extra_args = None
    if ensure == "present":
        if current_entry and current_entry['peerURLs'] == member_peer_url:
            module.exit_json(
                changed=False,
                new_member_id=current_entry['member_id'],
                members=before_members,
                stdout="Already there",
                stderr="",
                rc=0,
            )
        elif current_entry and current_entry['peerURLs'] != member_peer_url:
            extra_args = ["member", "update", current_entry["member_id"], member_peer_url]
        else:
            extra_args = ["member", "add", member_fqdn, member_peer_url]

    else:
        if not current_entry:
            module.exit_json(
                changed=False,
                members=before_members,
                stdout="Already not there.",
                stderr="",
                rc=0,
            )

        extra_args = ["member", "remove", current_entry['member_id']]

    if extra_args is None:
        module.fail_json(
            changed=False,
            members=before_members,
            stdout="This should never happen.",
        )

    args = get_etcdctl_args(
        module_params=module.params,
        extra_args=extra_args,
    )
    rc, out, err = module.run_command(args=args)
    # unfortunately, this command does not give the member_id, but only the new
    # name, that then member list does not show, so we have to diff before and
    # after to find out which one is the new member id
    after_members = get_cluster_info(module)
    new_member_id = list(set(after_members.keys()) - set(before_members.keys()))[0]
    module.exit_json(
        changed=True, new_member_id=new_member_id, members=after_members, stdout=out, stderr=err, rc=rc
    )


if __name__ == '__main__':
    main()
