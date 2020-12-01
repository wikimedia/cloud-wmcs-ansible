from __future__ import (absolute_import, division, print_function)
__metaclass__ = type
import requests


def get_common_etcdctl_args_specs(**extra_args):
    args = {
        "endpoints": {"type": "str", "required": True},
        "cert_file": {"type": "str", "required": True},
        "key_file": {"type": "str", "required": True},
        "ca_file": {"type": "str", "required": False, "default": "/etc/etcd/ssl/ca.pem"},
    }
    args.update(extra_args)
    return args


def get_etcdctl_args(module_params, extra_args):
    return [
        "etcdctl",
        "--endpoints", module_params.get('endpoints'),
        "--ca-file", module_params.get('ca_file'),
        "--cert-file", module_params.get('cert_file'),
        "--key-file", module_params.get('key_file'),
        *extra_args
    ]


def to_simple_type(maybe_not_string):
    """
    Simple type interpolation, as etcdctl member list does not return json (yet)
    """
    if maybe_not_string == "true":
        return True
    elif maybe_not_string == "false":
        return False

    try:
        return int(maybe_not_string)
    except ValueError:
        pass

    return maybe_not_string


def get_cluster_info(module):
    args = get_etcdctl_args(
        module_params=module.params, extra_args=["member", "list"]
    )
    rc, out, err = module.run_command(args=args)
    structured_result = {}
    if rc == 0:
        for line in out.split('\n'):
            if not line.strip():
                continue

            # <memberid>[<status>]: <key>=<value> <key>=<value>...
            # where value might be the string "true" or a stringified int "42"
            # and the '[<status>]' bit might not be there
            # peerURLs and memberid are the only key that seems to be there always
            split_info = [
                [to_simple_type(subelem) for subelem in elem.split('=')]
                for elem in line.split()
            ]
            struct_elem = dict(split_info[1:])

            first_part = split_info[0][0][:-1]
            if '[' in first_part:
                member_id = first_part.split('[', 1)[0]
                status = first_part.split('[', 1)[1][:-1]
            else:
                member_id = first_part
                status = "up"

            struct_elem['member_id'] = member_id
            struct_elem['status'] = status

            if 'peerURLs' not in struct_elem:
                module.fail_json(
                    msg=(
                        "Unable to parse etcdctl output (missing peerURLs for "
                        f"member line):\nParsed: {struct_elem}\nLine: {line}\n"
                        f"Full output: {out}"
                    ),
                    args=args,
                    out=out,
                    err=err,
                    rc=rc,
                )
            structured_result[struct_elem['member_id']] = struct_elem

    return structured_result
