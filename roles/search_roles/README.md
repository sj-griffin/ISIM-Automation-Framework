search_roles
=========

Use this role to search for roles in a Container in the ISIM Application.

Requirements
------------

start_config role is a required dependencies. It contains the Ansible Custom Modules and handlers.

Role Variables
--------------

Provide, at a minimum, the following variables. Others are optional:
search_roles_container_dn:

Dependencies
------------

start_config is a required role - since it contains the Ansible Custom Modules and Handlers.

Example Playbook
----------------

Here is an example of how to use this role:

    - hosts: servers
      connection: local
      roles:
         - role: search_roles
           search_roles_container_dn: 'erglobalid=00000000000000000000,ou=demo,dc=com'
           search_roles_ldap_filter: '(errolename=*)'

License
-------

Apache

Author Information
------------------

IBM
