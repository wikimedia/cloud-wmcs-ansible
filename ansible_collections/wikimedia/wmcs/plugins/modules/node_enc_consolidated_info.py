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
module: node_enc_consolidated_info
short_description: Get information from the puppet enc about a host
description:
  - Get information from the puppet enc

options:
  enc_url:
    description:
      - Base url to the enc service
    required: true
    type: str
  openstack_project:
    description: Openstack project to get info for
    required: true
    type: str
  fqdn:
    description: FQDN of the node to retrieve the hiera and roles from
    required: true
    type: str

requirements:
  - "python >= 3.6"
'''

EXAMPLES = '''
- name: Fetch hiera data for a specific openstack vm
  wikimedia.wmcs.node_enc_info:
    enc_url: http://example.enc:8180/v1
    openstack_project: my_project
    fqdn: toolsbeta-proxy-1.toolsbeta.eqiad1.wikimedia.cloud

'''

RETURN = '''
'''

__metaclass__ = type
import yaml
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import jsonify
from ansible_collections.wikimedia.wmcs.plugins.module_utils.enc_connection import EncConnection


def main():
    """ Module entry point """

    argument_spec = {
        "enc_url": {"type": "str", "required": True},
        "openstack_project": {"type": "str", "required": True},
        "fqdn": {"type": "str", "required": True},
    }
    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
    )

    enc_url = module.params.get('enc_url')
    openstack_project = module.params.get('openstack_project')
    fqdn = module.params.get('fqdn')

    conn = EncConnection(enc_url=enc_url, openstack_project=openstack_project)
    res = conn.get_node_consolidated_info(fqdn=fqdn)
    if res.status_code != 200:
        module.fail_json("Error trying to contact the enc backend: %s" % res.raw)

    try:
        data = yaml.load(res.text)
    except Exception as error:
        module.fail_json(
            "Error parsing response from the enc backend: %s\nResponse:\n%s" % (
                error,
                res.raw,
            ),
        )

    module.exit_json(changed=False, enc_data=data, fqdn=fqdn, openstack_project=openstack_project)


if __name__ == '__main__':
    main()
