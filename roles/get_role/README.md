get_role
=========

Use this role to retrieve information about a role in the ISIM Application using it's DN.

Requirements
------------

start_config role is a required dependencies. It contains the Ansible Custom Modules and handlers.

Role Variables
--------------

Provide, at a minimum, the following variables. Others are optional:
get_role_role_dn:

Dependencies
------------

start_config is a required role - since it contains the Ansible Custom Modules and Handlers.

Example Playbook
----------------

Here is an example of how to use this role:

    - hosts: servers
      connection: local
      roles:
         - role: get_role
           get_role_role_dn: 'erglobalid=7148929463058980179,ou=roles,erglobalid=00000000000000000000,ou=demo,dc=com'

License
-------

Apache

Author Information
------------------

IBM
