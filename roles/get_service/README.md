get_service
=========

Use this role to retrieve information about a service in the ISIM Application using it's DN.

Requirements
------------

start_config role is a required dependencies. It contains the Ansible Custom Modules and handlers.

Role Variables
--------------

Provide, at a minimum, the following variables. Others are optional:
get_service_service_dn:

Dependencies
------------

start_config is a required role - since it contains the Ansible Custom Modules and Handlers.

Example Playbook
----------------

Here is an example of how to use this role:

    - hosts: servers
      connection: local
      roles:
         - role: get_service
           get_service_service_dn: 'erglobalid=5621731231346846233,ou=services,erglobalid=00000000000000000000,ou=demo,dc=com'

License
-------

Apache

Author Information
------------------

IBM
