= Wikimedia Cloud Services Team ansible playbooks and modules

== Installation

Either in a virtualenv or in your system you have to install ansible:

```
pip install ansible
# or
sudo apt install ansible
# or
sudo dnf install ansible
# ...
```

Then you have to download the galaxy collections:
```
ansible-galaxy collection install -r collections.yml
```

== Running a playbook

Currently there's only one playbook to spin up a new etcd node in a toolforge
setup:
```
ansible-playbook playbooks/add_k8s_etcd_member.yml
```

Currently, by default it will spin it up on toolsbeta project.


== Requirements

You need to have access to the openstack control nodes, and from there access
to the openstack apis.

The password should be currently in plain text in a file called 'passwords' one
directory above this one (TODO: make it pull it from the secret store/encrypted
file, etc.).
