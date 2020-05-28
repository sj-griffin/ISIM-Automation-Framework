search_containers
=========

Use this role to search for containers in the ISIM Application.

Requirements
------------

start_config role is a required dependencies. It contains the Ansible Custom Modules and handlers.

Role Variables
--------------

Provide, at a minimum, the following variables. Others are optional:
search_containers_parent_dn:
search_containers_container_name:
search_containers_profile:

Dependencies
------------

start_config is a required role - since it contains the Ansible Custom Modules and Handlers.

Example Playbook
----------------

Here is an example of how to use this role:

    - hosts: servers
      connection: local
      roles:
         - role: search_containers
           search_containers_parent_dn: 'erglobalid=00000000000000000000,ou=demo,dc=com'
           search_containers_container_name: 'demo'
           search_containers_profile: 'OrganizationalUnit'

License
-------

Apache

Author Information
------------------

IBM
