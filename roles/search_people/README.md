search_roles
=========

Use this role to search for people in the ISIM Application.

Requirements
------------

The start_config role is a required dependency. It contains the Ansible Custom Modules and handlers.

Role Variables
--------------

Provide, at a minimum, the following variables. Others are optional:

Dependencies
------------

start_config is a required role - since it contains the Ansible Custom Modules and Handlers.

Example Playbook
----------------

Here is an example of how to use this role:

    - hosts: servers
      connection: local
      roles:
         - role: search_people
           search_people_ldap_filter: '(uid=*)'

License
-------

Apache

Author Information
------------------

IBM
