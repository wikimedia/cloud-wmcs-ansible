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
module: prefix_enc
short_description: Set information from the puppet enc for the prefix
description:
  - Set information from the puppet enc for the prefix

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
  prefix:
    description: Project specific prefix to look for hiera data
    required: true
    type: str
  data:
    description: Hiera data to set (a string in yaml format)
    required: true
    type: str

requirements:
  - "python >= 3.6"
'''

EXAMPLES = '''
- name: Fetch hiera data for a specific openstack vm
  wikimedia.wmcs.prefix_enc:
    enc_url: http://example.enc:8180/v1
    openstack_project: my_project
    prefix: toolsbeta
    data: |
        authdns_servers:
            208.80.154.11: 208.80.154.11
            208.80.154.135: 208.80.154.135
        http_proxy: ''

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
        "prefix": {"type": "str", "required": True},
        "data": {"type": "str", "required": True},
    }
    module = AnsibleModule(
        argument_spec,
        supports_check_mode=True,
    )

    enc_url = module.params.get('enc_url')
    openstack_project = module.params.get('openstack_project')
    prefix = module.params.get('prefix')
    data = module.params.get('data')

    conn = EncConnection(enc_url=enc_url, openstack_project=openstack_project)
    res = conn.set_prefix_hiera(prefix=prefix, data=data)
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

    module.exit_json(changed=False, result=data, prefix=prefix, openstack_project=openstack_project)


if __name__ == '__main__':
    main()
