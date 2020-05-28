apply_container
=========

Use this role to idempotently apply the configuration of a container within the ISIM Application.

Requirements
------------

The start_config role is a required dependency. It contains the Ansible Custom Modules and handlers.

container Variables
--------------

Provide, at a minimum, the following variables. Others are optional:
apply_container_parentcontainer_path:
apply_container_profile:
apply_container_name:

Dependencies
------------

start_config is a required role - since it contains the Ansible Custom Modules and Handlers.

Example Playbook
----------------

Here is an example of how to use this role:

    - hosts: servers
      connection: local
      roles:
         - role: apply_container
           apply_container_parent_container_path: '//demo//lo::Sydney'
           apply_container_profile: 'OrganizationalUnit'
           apply_container_name: 'ou1'
           apply_container_description: 'A description'
           apply_container_associated_people:
                - ['//demo//lo::Sydney//ou::ou1//bp::testing', 'cspeed']
                - ['//demo//lo::Sydney//ou::ou1', 'bjones']
                - ['//IBM', 'ayang']

License
-------

Apache

Author Information
------------------

IBM
