search_provisioning_policies
=========

Use this role to search for provisioning policies in a Container in the ISIM Application.

Requirements
------------

start_config role is a required dependencies. It contains the Ansible Custom Modules and handlers.

Role Variables
--------------

Provide, at a minimum, the following variables. Others are optional:
search_provisioning_policies_container_dn:
search_provisioning_policies_policy_name:

Dependencies
------------

start_config is a required role - since it contains the Ansible Custom Modules and Handlers.

Example Playbook
----------------

Here is an example of how to use this role:

    - hosts: servers
      connection: local
      roles:
         - role: search_provisioning_policies
           search_provisioning_policies_container_dn: 'erglobalid=00000000000000000000,ou=demo,dc=com'
           search_provisioning_policies_policy_name: 'Example Policy'

License
-------

Apache

Author Information
------------------

IBM
