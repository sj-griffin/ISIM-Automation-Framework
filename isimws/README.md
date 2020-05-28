# ISIM Web Services for Ansible Library

This repository contains Python code to manage ISIM using the SOAP web services via Ansible. It provides output in a
standardised IBMResponse format which can be easily interpreted by Ansible modules. It is inspired by and based on the
IBM-Security/ibmsecurity repository (https://github.com/IBM-Security/ibmsecurity).


## Requirements

Python v3.6 and above is required for this package.

The following Python Packages are required:
1. zeep - for interacting with SOAP services
2. requests - for direct manipulation of SOAP HTTP calls
3. importlib - for the sample code to work
4. PyYAML - for the sample code to work

The ISIM appliance is expected to be configured and have an application interface set up already.

## Versioning

This package uses a date for versioning. For example: "2019.11.20.0"

It is the date when the package is released with a sequence number at the end to handle when there are 
multiple releases in one day (expected to be uncommon).

## Features

This python package provides the following features:
1. Easy to use - the details of making a SOAP call are handled within the ISIMApplication class
2. Intuitive layout of code package and naming maps to the GUI interface of the ISIM application
3. Idempotency - functions that make updates will query the application to compare the current state with the target
state and dynamically determine what action to take.
4. Standard logging is included - with the ability to set logging levels.
5. Parameters to function will use standard default values wherever possible.
6. A force option is provided to override idempotency.

## Example Code

A sample `testisim.py` is provided. Provide details of your application interface and a user/password to authenticate.
Then call the functions needed. Run the code like you would any other Python script.

e.g.: `python testisim.py`

Note: the code requires PyYAML (for printing output in YAML) and importlib (dynamically load all packages) packages to work.

### Installation Instructions

Use the setup.py file to package the source code into the dist directory with `python3 setup.py sdist bdist_wheel`
Install the package with `pip3 install ./dist/isimws-XXXX.XX.XX.X-py3-none-any.whl`

### Function Data Return Format
~~~~
{
    rc:       <0 for success, higher for errors>
    changed:  <True or False>
    warnings: <List of strings with warnings - e.g. incompatible version>
    data:     <XML data returned by application SOAP API that the function called>
}
~~~~

Note: it is preferred to return warnings rather than send back a non-zero rc.

## Organization of code

TBA

# License

The contents of this repository are open-source under the Apache 2.0 licence.

```
Copyright 2019 International Business Machines

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
