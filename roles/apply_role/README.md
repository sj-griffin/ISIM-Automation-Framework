apply_role
=========

Use this role to idempotently apply the configuration of a role within the ISIM Application.

Requirements
------------

The start_config role is a required dependency. It contains the Ansible Custom Modules and handlers.

Role Variables
--------------

Provide , at a minimum, the following variables. Others are optional:
apply_role_container_path:
apply_role_name:
apply_role_role_classification:

Dependencies
------------

start_config is a required role - since it contains the Ansible Custom Modules and Handlers.

Example Playbook
----------------

Here is an example of how to use this role:

    - hosts: servers
      connection: local
      roles:
         - role: apply_role
           apply_role_container_path: '//demo//lo::Sydney//ou::ou1//bp::testing'
           apply_role_name: 'test-role'
           apply_role_role_classification: 'application'
           apply_role_description: 'A role to test the SOAP API'
           apply_role_role_owners:
                - ["//demo", "new-role"]
           apply_role_user_owners:
                - ["//demo", "testuser"]
           apply_role_enable_access: True
           apply_role_common_access: False
           apply_role_access_type: 'emailgroup'
           apply_role_access_image_uri: ""
           apply_role_access_search_terms:
                - 'test'
                - 'testing'
           apply_role_access_additional_info: 'Some additional information'
           apply_role_access_badges:
                - text: 'An orange badge'
                  colour: 'orange'
                - text: 'A red badge'
                  colour: 'red'
           apply_role_assignment_attributes:
                - 'attribute1'
                - 'attribute2'

License
-------

Apache

Author Information
------------------

IBM
