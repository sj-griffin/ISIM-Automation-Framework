apply_account_service
=========

Use this role to idempotently apply the configuration of an account service within the ISIM Application.

Requirements
------------

The start_config role is a required dependency. It contains the Ansible Custom Modules and handlers.

Role Variables
--------------

Provide, at a minimum, the following variables. Others are optional:
apply_account_service_container_path:
apply_account_service_service_type:
apply_account_service_name:
apply_account_service_access_name: (only if apply_account_service_define_access is True)

Dependencies
------------

start_config is a required role - since it contains the Ansible Custom Modules and Handlers.

Example Playbook
----------------

Here is an example of how to use this role:

    - hosts: servers
      connection: local
      roles:
         - role: apply_account_service
           apply_account_service_container_path: '//demo//lo::Sydney//ou::ou1//bp::testing'
           apply_account_service_name: 'soap-test-service'
           apply_account_service_service_type: 'ADprofile'
           apply_account_service_description: "Here's a description"
           apply_account_service_owner: ['//demo', 'testuser']
           apply_account_service_service_prerequisite: ['//demo', 'ITIM Service']
           apply_account_service_define_access: True
           apply_account_service_access_name: 'Test Access'
           apply_account_service_access_type: 'emailgroup'
           apply_account_service_access_description: 'A description of the access'
           apply_account_service_access_image_uri: 'test.demo'
           apply_account_service_access_search_terms:
                - 'test'
                - 'testing'
           apply_account_service_access_additional_info: 'Some additional information'
           apply_account_service_access_badges:
                - text: 'An orange badge'
                  colour: 'orange'
                - text: 'A red badge'
                  colour: 'red'
           apply_account_service_configuration:
                erURL: 'demo.demo'
                erUid: 'admin'
                erPassword: 'Object00'
                erADBasePoint: 'abc'
                erADGroupBasePoint: 'def'
                erADDomainUser: 'ghi'
                erADDomainPassword: 'jkl'
                erURI: ['test1', 'test2']

License
-------

Apache

Author Information
------------------

IBM
