apply_identity_feed
=========

Use this role to idempotently apply the configuration of an identity feed within the ISIM Application.

Requirements
------------

The start_config role is a required dependency. It contains the Ansible Custom Modules and handlers.

Role Variables
--------------

Provide, at a minimum, the following variables. Others are optional:
apply_identity_feed_container_path:
apply_identity_feed_service_type:
apply_identity_feed_name:

Dependencies
------------

start_config is a required role - since it contains the Ansible Custom Modules and Handlers.

Example Playbook
----------------

Here is an example of how to use this role:

    - hosts: servers
      connection: local
      roles:
         - role: apply_identity_feed
           apply_identity_feed_container_path: '//demo//lo::Sydney//ou::ou1//bp::testing'
           apply_identity_feed_name: 'soap-test-feed'
           apply_identity_feed_service_type: 'ADFeed'
           apply_identity_feed_description: "Here's a description"
           apply_identity_feed_use_workflow: True
           apply_identity_feed_evaluate_sod: True
           apply_identity_feed_placement_rule: 'insert placement rule here'
           apply_identity_feed_configuration:
                erURL: 'demo.demo'
                erUid: 'admin'
                erPassword: 'Object00'
                erNamingContexts:
                    - '//demo//ad::Restricted'
                erPersonProfileName: 'Person'
                erAttrMapFilename: '/test'
                ernamingattribute: 'uid'

License
-------

Apache

Author Information
------------------

IBM
