from typing import List, Dict, Optional
import logging
from isimws.application.isimapplication import ISIMApplication
from isimws.utilities.tools import build_attribute
import isimws

logger = logging.getLogger(__name__)

# service name for this module
service = "WSPersonService"

# minimum version required by this module
requires_version = None


def create(isim_application: ISIMApplication,
           container_dn: str,
           profile_name: str,
           username: str,
           surname: str,
           full_name: str,
           aliases: List[str],
           password: str,
           roles: List[str],
           check_mode=False,
           force=False):
    """
    Create a Person.
    :param isim_application:
    :param container_dn:
    :param profile_name:
    :param username:
    :param surname:
    :param full_name:
    :param aliases:
    :param password:
    :param roles:
    :param check_mode:
    :param force:
    :return:
    """
    data = []

    # Get the required SOAP types
    person_type_response = isim_application.retrieve_soap_type(service,
                                                               "ns1:WSPerson",
                                                               requires_version=requires_version)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if person_type_response['rc'] != 0:
        return person_type_response
    person_type = person_type_response['data']

    attribute_type_response = isim_application.retrieve_soap_type(service,
                                                                  "ns1:WSAttribute",
                                                                  requires_version=requires_version)
    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if attribute_type_response['rc'] != 0:
        return attribute_type_response
    attr_type = attribute_type_response['data']

    # Retrieve the container object (the business unit)
    container_response = isimws.isim.container.get(isim_application=isim_application, container_dn=container_dn)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if container_response['rc'] != 0:
        return container_response

    container_object = container_response['data']
    data.append(container_object)

    # Setup the person object
    person_object = person_type()

    person_object['profileName'] = profile_name
    person_object['select'] = False

    attribute_list = []
    attribute_list.append(build_attribute(attr_type, 'uid', [username]))
    attribute_list.append(build_attribute(attr_type, 'sn', [surname]))
    attribute_list.append(build_attribute(attr_type, 'cn', [full_name]))
    attribute_list.append(build_attribute(attr_type, 'eraliases', aliases))
    attribute_list.append(build_attribute(attr_type, 'erpersonpassword', [password]))
    attribute_list.append(build_attribute(attr_type, 'erroles', roles))

    person_object['attributes'] = {'item': attribute_list}
    data.append(person_object)

    # Leave the date object empty
    data.append(None)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Creating a Person",
                                                   service,
                                                   "createPerson",
                                                   data,
                                                   requires_version=requires_version)

    return ret_obj
