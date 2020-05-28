apply_person
=========

Use this role to idempotently apply the configuration of a person within the ISIM Application.

Requirements
------------

start_config role is a required dependency. It contains the Ansible Custom Modules and handlers.

person Variables
--------------

Provide, at a minimum, the following variables. Others are optional:
apply_person_container_path:
apply_person_uid:
apply_person_profile:
apply_person_full_name:
apply_person_surname:

Dependencies
------------

start_config is a required role - since it contains the Ansible Custom Modules and Handlers.

Example Playbook
----------------

Here is an example of how to use this role:

    - hosts: servers
      connection: local
      roles:
         - role: apply_person
           apply_person_container_path: '//demo//lo::Sydney//ou::ou1//bp::testing'
           apply_person_uid: 'jbloggs'
           apply_person_profile: 'Person'
           apply_person_full_name: 'Joe Bloggs'
           apply_person_surname: 'Bloggs'
           apply_person_aliases:
                - 'JB'
                - 'Joe'
           apply_person_password: 'Passw0rd'
           apply_person_roles:
                - ["//demo", "new-role"]
                - ["//demo", "Demo Role"]

License
-------

Apache

Author Information
------------------

IBM
