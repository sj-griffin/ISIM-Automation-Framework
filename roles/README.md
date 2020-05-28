# ISIM Ansible Roles

This repository contains Ansible Custom Modules and Roles for automating ISIM application tasks. Custom Modules provide
the interface to the idempotent Python functions in the isimws package.

## Requirements

Python v3.6 and above is required for this package.

The following Python Packages are required (including their dependencies):
1. isimws
2. ansible

These roles assume that the ISIM appliance is already configured and the ISIM application is running and listening on
the application interface.


## Get Started

Use the following setting in ansible.cfg to set the location of the installed roles:
```
[defaults]
roles_path = <dest dir>
```

## Versioning

git tag will be used to indicate version numbers. The version numbers will be based on date. For example: "2019.11.20.0"

It is the date when the package is released with a sequence number at the end to handle when there are
multiple releases in one day (expected to be uncommon).

## Features

The `start_config` role is a requirement for every playbok. It contains the custom modules and all handlers. All other
roles have a dependency on it and `start_config` will get automatically invoked as needed.This repository contains a
small selection of roles - users are encouraged to add more as needed.

### Custom Modules
_”Modules (also referred to as “task plugins” or “library plugins”) are the ones that do the actual work in ansible,
they are what gets executed in each playbook task. But you can also run a single one using the ‘ansible’ command.”_
http://docs.ansible.com/ansible/modules_intro.html

Ansible custom modules provide the glue to seamless invoke python functions to execute SOAP API calls against ISIM
application instances. At present there is only one module provided:

isim - this module is for all calls to the ISIM application.

### Roles
“Roles in Ansible build on the idea of include files and combine them to form clean, reusable abstractions – they allow
you to focus more on the big picture and only dive down into the details when needed.”
http://docs.ansible.com/ansible/playbooks_roles.html

Using roles allows one to concentrate on describing the business needs in a playbook. The actual call to the python
function and the need to deploy and restart processes is taken care of inside the role.

## Naming of Roles and variables
Roles start with a verb like "apply" or "search" followed by a name that describes either the task or the python function
being called. This depends on whether the role contains a single tasks or a combination of tasks.

The apply roles should be used to define system configuration. These roles compare the current state of the system to
the target state and dynamically determine whether to perform a create or modify operation, or take no action.

Specific create or modify roles are not provided- apply roles should be used for any create or modify activity.

# License

The contents of this repository are open-source under the Apache 2.0 licence.

```
Copyright 2017 International Business Machines

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

Ansible is a trademark of Red Hat, Inc.
