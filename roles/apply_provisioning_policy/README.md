apply_provisioning_policy
=========

Use this role to idempotently apply the configuration of a provisioning policy within the ISIM Application.


Requirements
------------

The start_config role is a required dependency. It contains the Ansible Custom Modules and handlers.

Role Variables
--------------

Provide, at a minimum, the following variables. Others are optional:
apply_provisioning_policy_container_path:
apply_provisioning_policy_name:
apply_provisioning_policy_priority:
apply_provisioning_policy_membership_type:
apply_provisioning_policy_entitlements:

Dependencies
------------

start_config is a required role - since it contains the Ansible Custom Modules and Handlers.

Example Playbook
----------------

Here is an example of how to use this role:

    - hosts: servers
      connection: local
      roles:
         - role: apply_provisioning_policy
           apply_provisioning_policy_container_dn: "//demo//lo::Sydney//ou::ou1//bp::testing"
           apply_provisioning_policy_name: "Provisioning policy test"
           apply_provisioning_policy_priority: 50
           apply_provisioning_policy_description: "Here's a description"
           apply_provisioning_policy_keywords: "here are some keywords"
           apply_provisioning_policy_caption: "Here's a caption"
           apply_provisioning_policy_available_to_subunits: False
           apply_provisioning_policy_enabled: True
           apply_provisioning_policy_membership_type: "roles"
           apply_provisioning_policy_membership_roles:
                - ['//demo', 'new-role']
                - ['//demo', 'test-role']
           apply_provisioning_policy_entitlements:
                - automatic: False
                  ownership_type: 'all'
                  target_type: 'all'
                  service_type: null
                  service: null
                  workflow: null

                - automatic: True
                  ownership_type: 'device'
                  target_type: 'policy'
                  service_type: 'ADprofile'
                  service: null
                  workflow: ['//demo', 'Default Account Request Workflow']

                - automatic: False
                  ownership_type: 'individual'
                  target_type: 'specific'
                  service_type: null
                  service: ['//demo', 'ITIM Service']
                  workflow: ['//demo', 'Default Account Request Workflow']


License
-------

Apache

Author Information
------------------

IBM
