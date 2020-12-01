# Ansible Collection - wikimedia.wmcs

Documentation for the collection.


# BUILD
$ ansible-galaxy collection build --force


# INSTALL
$ ansible-galaxy collection install --force $(ansible-galaxy collection build --force  | awk '{ print $NF }')
