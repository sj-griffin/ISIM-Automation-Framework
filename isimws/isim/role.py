from typing import List, Dict, Optional
import logging
from isimws.application.isimapplication import ISIMApplication
from isimws.utilities.tools import build_attribute
import isimws

logger = logging.getLogger(__name__)

# service name for this module
service = "WSRoleService"

# minimum version required by this module
requires_version = None


def search(isim_application: ISIMApplication,
           container_dn: Optional[str],
           ldap_filter: str = "(errolename=*)",
           check_mode=False,
           force=False):
    """
    Search for a role using a filter.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The optional DN of a container to search in. Set to None to search everywhere.
    :param ldap_filter: An LDAP filter string to search for.
    :param check_mode: Set to True to enable check mode :param force: Set to True to force execution regardless of
        current state.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representations of each role matching the filter.
    """
    # The session object is handled by the ISIMApplication instance
    data = []
    if container_dn is None:
        # Add the filter string to the request
        data.append(ldap_filter)

        # Invoke the call
        ret_obj = isim_application.invoke_soap_request("Searching for roles",
                                                       service,
                                                       "searchRoles",
                                                       data,
                                                       requires_version=requires_version)
    else:
        # Retrieve the container object (the business unit)
        container_response = isimws.isim.container.get(isim_application=isim_application, container_dn=container_dn)

        # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
        if container_response['rc'] != 0:
            return container_response

        container_object = container_response['data']
        data.append(container_object)

        # Add the filter string to the request
        data.append(ldap_filter)

        # Invoke the call
        ret_obj = isim_application.invoke_soap_request("Searching for roles in container " + container_dn,
                                                       service,
                                                       "searchForRolesInContainer",
                                                       data,
                                                       requires_version=requires_version)
    return ret_obj


def get(isim_application: ISIMApplication, role_dn: str, check_mode=False, force=False):
    """
    Get a role by it's DN.
    :param isim_application: The ISIMApplication instance to connect to.
    :param role_dn: The ITIM DN of the role.
    :param check_mode: Set to True to enable check mode
    :param force: Set to True to force execution regardless of current state
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the role.
    """
    # The session object is handled by the ISIMApplication instance
    # Add the dn string to the request
    data = [role_dn]

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Retrieving a static role",
                                                   service,
                                                   "lookupRole",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def create(isim_application: ISIMApplication,
           container_dn: str,
           role_classification: str,
           name: str,
           description: str = "",
           role_owners: List[str] = [],
           user_owners: List[str] = [],
           enable_access: bool = False,
           common_access: bool = False,
           access_type: Optional[str] = None,
           access_image_uri: Optional[str] = None,
           access_search_terms: List[str] = [],
           access_additional_info: str = None,
           access_badges: List[Dict[str, str]] = [],
           assignment_attributes: List[str] = [],
           check_mode=False,
           force=False):
    """
    Create a Role.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The DN of the container (business unit) to create the role under.
    :param role_classification: Set to either "application" or "business".
    :param name: The role name.
    :param description: A description of the role.
    :param role_owners: A list of DNs corresponding to the roles that own this role.
    :param user_owners: A list of DNs corresponding to the users that own this role.
    :param enable_access: Set to True to enable access for the role. If False, all access related attributes will be
        ignored.
    :param common_access: Set to True to show the role as a common access.
    :param access_type: Set to one of 'application', 'emailgroup', 'sharedfolder' or 'role'.
    :param access_image_uri: The URI of an image to use for the access icon.
    :param access_search_terms: A list of search terms for the access.
    :param access_additional_info: Additional information about the acceess.
    :param access_badges: A list of dicts representing badges for the access. Each entry in the list must contain the
        keys 'text' and 'colour' with string values.
    :param assignment_attributes: A list of attribute names to assign to the role.
    :param check_mode: Set to True to enable check mode
    :param force: Set to True to force execution regardless of current state
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the action taken by the server.
    """
    data = []

    # Get the required SOAP types
    role_type_response = isim_application.retrieve_soap_type(service,
                                                             "ns1:WSRole",
                                                             requires_version=requires_version)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if role_type_response['rc'] != 0:
        return role_type_response
    role_type = role_type_response['data']

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

    # Setup the role object
    role_object = role_type()

    role_object['name'] = name
    role_object['description'] = description
    role_object['select'] = False

    # populate the role attributes
    attribute_list = []
    if role_classification.lower() == "application":
        attribute_list.append(build_attribute(attr_type, 'erroleclassification', ["role.classification.application"]))
    elif role_classification.lower() == "business":
        attribute_list.append(build_attribute(attr_type, 'erroleclassification', ["role.classification.business"]))
    else:
        raise ValueError(role_classification + "is not a valid role classification. Must be 'application' or "
                                               "'business'.")

    attribute_list.append(build_attribute(attr_type, 'errolename', [name]))
    attribute_list.append(build_attribute(attr_type, 'eraccessname', [name]))
    attribute_list.append(build_attribute(attr_type, 'eraccessdescription', [description]))
    attribute_list.append(build_attribute(attr_type, 'owner', role_owners + user_owners))

    if enable_access is False:
        attribute_list.append(build_attribute(attr_type, 'eraccessoption', 1))
    else:
        if common_access is False:
            attribute_list.append(build_attribute(attr_type, 'eraccessoption', 2))
        elif common_access is True:
            attribute_list.append(build_attribute(attr_type, 'eraccessoption', 3))

        if access_type is not None:
            if access_type.lower() == "application":
                attribute_list.append(build_attribute(attr_type, 'erobjectprofilename', ["Application"]))
            elif access_type.lower() == "sharedfolder":
                attribute_list.append(build_attribute(attr_type, 'erobjectprofilename', ["SharedFolder"]))
            elif access_type.lower() == "emailgroup":
                attribute_list.append(build_attribute(attr_type, 'erobjectprofilename', ["MailGroup"]))
            elif access_type.lower() == "role":
                attribute_list.append(build_attribute(attr_type, 'erobjectprofilename', ["AccessRole"]))
            else:
                raise ValueError(access_type + "is not a valid access type. Must be 'application', 'sharedfolder', "
                                               "'emailgroup', or 'role'.")
        else:
            # application is the default access type when it is not specified
            attribute_list.append(build_attribute(attr_type, 'erobjectprofilename', ["Application"]))

        if access_image_uri is not None:
            attribute_list.append(build_attribute(attr_type, 'erimageuri', [access_image_uri]))

        attribute_list.append(build_attribute(attr_type, 'eraccesstag', access_search_terms))

        if access_additional_info is not None:
            attribute_list.append(build_attribute(attr_type, 'eradditionalinformation', [access_additional_info]))

        badges = []
        for badge in access_badges:
            badges.append(str(badge['text'] + "~" + badge['colour']))
        attribute_list.append(build_attribute(attr_type, 'erbadge', badges))

    attribute_list.append(build_attribute(attr_type, 'erroleassignmentkey', assignment_attributes))

    role_object['attributes'] = {'item': attribute_list}
    data.append(role_object)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Creating a Role",
                                                   service,
                                                   "createStaticRole",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj
