from typing import List, Dict, Optional
from collections import Counter
import logging
from isimws.application.isimapplication import ISIMApplication, IBMResponse, create_return_object
from isimws.utilities.tools import build_attribute
import isimws

logger = logging.getLogger(__name__)

# service name for this module
soap_service = "WSRoleService"

# minimum version required by this module
requires_version = None


def search(isim_application: ISIMApplication,
           container_dn: Optional[str],
           ldap_filter: str = "(errolename=*)",
           check_mode=False,
           force=False) -> IBMResponse:
    """
    Search for a role using a filter.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The optional DN of a container to search in. Set to None to search everywhere.
    :param ldap_filter: An LDAP filter string to search for.
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state.
    :return: An IBMResponse object. If the call was successful, the data field will contain a list of the Python dict
        representations of each role matching the filter.
    """
    # The session object is handled by the ISIMApplication instance
    data = []
    if container_dn is None:
        # Add the filter string to the request
        data.append(ldap_filter)

        # Invoke the call
        ret_obj = isim_application.invoke_soap_request("Searching for roles",
                                                       soap_service,
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
                                                       soap_service,
                                                       "searchForRolesInContainer",
                                                       data,
                                                       requires_version=requires_version)
    return ret_obj


def get(isim_application: ISIMApplication, role_dn: str, check_mode=False, force=False) -> IBMResponse:
    """
    Get a role by it's DN.
    :param isim_application: The ISIMApplication instance to connect to.
    :param role_dn: The ITIM DN of the role.
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the role.
    """
    # The session object is handled by the ISIMApplication instance
    # Add the dn string to the request
    data = [role_dn]

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Retrieving a static role",
                                                   soap_service,
                                                   "lookupRole",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def _create(isim_application: ISIMApplication,
            container_dn: str,
            name: str,
            role_classification: str,
            description: str = "",
            role_owners: List[str] = [],
            user_owners: List[str] = [],
            enable_access: bool = False,
            common_access: bool = False,
            access_type: str = "",
            access_image_uri: str = "",
            access_search_terms: List[str] = [],
            access_additional_info: str = "",
            access_badges: List[Dict[str, str]] = [],
            assignment_attributes: List[str] = []) -> IBMResponse:
    """
    Create a Role.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The DN of the container (business unit) to create the role under.
    :param name: The role name.
    :param role_classification: Set to either "application" or "business".
    :param description: A description of the role.
    :param role_owners: A list of DNs corresponding to the roles that own this role.
    :param user_owners: A list of DNs corresponding to the users that own this role.
    :param enable_access: Set to True to enable access for the role.
    :param common_access: Set to True to show the role as a common access.
    :param access_type: Set to one of 'application', 'emailgroup', 'sharedfolder' or 'role'.
    :param access_image_uri: The URI of an image to use for the access icon.
    :param access_search_terms: A list of search terms for the access.
    :param access_additional_info: Additional information about the acceess.
    :param access_badges: A list of dicts representing badges for the access. Each entry in the list must contain the
        keys 'text' and 'colour' with string values.
    :param assignment_attributes: A list of attribute names to assign to the role.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the action taken by the server.
    """
    data = []

    # Get the required SOAP types
    role_type_response = isim_application.retrieve_soap_type(soap_service,
                                                             "ns1:WSRole",
                                                             requires_version=requires_version)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if role_type_response['rc'] != 0:
        return role_type_response
    role_type = role_type_response['data']

    # Retrieve the attribute type
    attribute_type_response = isim_application.retrieve_soap_type(soap_service,
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

    # Populate the role attributes
    attribute_list = _build_role_attributes_list(
        attr_type=attr_type,
        role_classification=role_classification,
        description=description,
        role_owners=role_owners,
        user_owners=user_owners,
        enable_access=enable_access,
        common_access=common_access,
        access_type=access_type,
        access_image_uri=access_image_uri,
        access_search_terms=access_search_terms,
        access_additional_info=access_additional_info,
        access_badges=access_badges,
        assignment_attributes=assignment_attributes
    )

    role_object['attributes'] = {'item': attribute_list}
    data.append(role_object)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Creating a Role",
                                                   soap_service,
                                                   "createStaticRole",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def _modify(isim_application: ISIMApplication,
            role_dn: str,
            role_classification: Optional[str] = None,
            description: Optional[str] = None,
            role_owners: Optional[List[str]] = None,
            user_owners: Optional[List[str]] = None,
            enable_access: Optional[bool] = None,
            common_access: Optional[bool] = None,
            access_type: Optional[str] = None,
            access_image_uri: Optional[str] = None,
            access_search_terms: Optional[List[str]] = None,
            access_additional_info: Optional[str] = None,
            access_badges: Optional[List[Dict[str, str]]] = None,
            assignment_attributes: Optional[List[str]] = None) -> IBMResponse:
    """
    Modify the attributes of an existing Role. Only arguments with a value will be changed. Any arguments set to None
        will be left as they are.
    :param isim_application: The ISIMApplication instance to connect to.
    :param role_dn: The DN of the existing role to modify.
    :param role_classification: Set to either "application" or "business".
    :param description: A description of the role.
    :param role_owners: A list of DNs corresponding to the roles that own this role.
    :param user_owners: A list of DNs corresponding to the users that own this role.
    :param enable_access: Set to True to enable access for the role.
    :param common_access: Set to True to show the role as a common access.
    :param access_type: Set to one of 'application', 'emailgroup', 'sharedfolder' or 'role'.
    :param access_image_uri: The URI of an image to use for the access icon.
    :param access_search_terms: A list of search terms for the access.
    :param access_additional_info: Additional information about the acceess.
    :param access_badges: A list of dicts representing badges for the access. Each entry in the list must contain the
        keys 'text' and 'colour' with string values.
    :param assignment_attributes: A list of attribute names to assign to the role.
    :return: An IBMResponse object. If the call was successful, the data field will be empty.
    """
    # Retrieve the attribute type
    attribute_type_response = isim_application.retrieve_soap_type(soap_service,
                                                                  "ns1:WSAttribute",
                                                                  requires_version=requires_version)
    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if attribute_type_response['rc'] != 0:
        return attribute_type_response
    attr_type = attribute_type_response['data']

    data = []

    # Add the role DN to the request
    data.append(role_dn)

    # Setup the list of modified attributes and add them to the request
    attribute_list = _build_role_attributes_list(
        attr_type=attr_type,
        role_classification=role_classification,
        description=description,
        role_owners=role_owners,
        user_owners=user_owners,
        enable_access=enable_access,
        common_access=common_access,
        access_type=access_type,
        access_image_uri=access_image_uri,
        access_search_terms=access_search_terms,
        access_additional_info=access_additional_info,
        access_badges=access_badges,
        assignment_attributes=assignment_attributes
    )

    data.append(attribute_list)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Modifying a Role",
                                                   soap_service,
                                                   "modifyStaticRole",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def apply(isim_application: ISIMApplication,
          container_dn: str,
          name: str,
          role_classification: str,
          description: str = "",
          role_owners: List[str] = [],
          user_owners: List[str] = [],
          enable_access: bool = False,
          common_access: bool = False,
          access_type: str = "",
          access_image_uri: str = "",
          access_search_terms: List[str] = [],
          access_additional_info: str = "",
          access_badges: List[Dict[str, str]] = [],
          assignment_attributes: List[str] = [],
          check_mode=False,
          force=False) -> IBMResponse:
    """
    Set a Role. This function will dynamically choose whether to to create or modify based on whether a role with the
        same name exists in the same container. Only attributes which differ from the existing role will be changed.
        Note that the name and container_dn of an existing role can't be changed because they are used to identify the
        role. If they don't match an existing role, a new role will be created with the specified name and container_dn.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The DN of the container (business unit) to create the role under.
    :param name: The role name.
    :param role_classification: Set to either "application" or "business".
    :param description: A description of the role.
    :param role_owners: A list of DNs corresponding to the roles that own this role.
    :param user_owners: A list of DNs corresponding to the users that own this role.
    :param enable_access: Set to True to enable access for the role.
    :param common_access: Set to True to show the role as a common access.
    :param access_type: Set to one of 'application', 'emailgroup', 'sharedfolder' or 'role'.
    :param access_image_uri: The URI of an image to use for the access icon.
    :param access_search_terms: A list of search terms for the access.
    :param access_additional_info: Additional information about the acceess.
    :param access_badges: A list of dicts representing badges for the access. Each entry in the list must contain the
        keys 'text' and 'colour' with string values.
    :param assignment_attributes: A list of attribute names to assign to the role.
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the action taken by the server. If a modify request was used, the data field will be empty.
    """

    # Check that the compulsory attributes are set properly
    if not (isinstance(container_dn, str) and len(container_dn) > 0 and
            isinstance(name, str) and len(name) > 0 and
            isinstance(role_classification, str) and len(role_classification) > 0):
        raise ValueError("Invalid role configuration. container_dn, name, and role_classification must have "
                         "non-empty string values.")

    # If any values are set to None, they must be replaced with empty values. This is because these values will be
    # passed to methods that interpret None as 'no change', whereas we want them to be explicitly set to empty values.
    if description is None:
        description = ""

    if role_owners is None:
        role_owners = []

    if user_owners is None:
        user_owners = []

    if enable_access is None:
        enable_access = False

    if common_access is None:
        common_access = False

    if access_type is None:
        access_type = ""

    if access_image_uri is None:
        access_image_uri = ""

    if access_search_terms is None:
        access_search_terms = []

    if access_additional_info is None:
        access_additional_info = ""

    if access_badges is None:
        access_badges = []

    if assignment_attributes is None:
        assignment_attributes = []

    # Search for instances with the specified name in the specified container
    search_response = search(
        isim_application=isim_application,
        container_dn=container_dn,
        ldap_filter="(errolename=" + name + ")"
    )
    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if search_response['rc'] != 0:
        return search_response
    search_results = search_response['data']

    if len(search_results) == 0:
        # If there are no results, create a new role and return the response
        return _create(
            isim_application=isim_application,
            container_dn=container_dn,
            name=name,
            role_classification=role_classification,
            description=description,
            role_owners=role_owners,
            user_owners=user_owners,
            enable_access=enable_access,
            common_access=common_access,
            access_type=access_type,
            access_image_uri=access_image_uri,
            access_search_terms=access_search_terms,
            access_additional_info=access_additional_info,
            access_badges=access_badges,
            assignment_attributes=assignment_attributes
        )
    elif len(search_results) == 1:
        # If exactly one result is found, compare it's attributes with the requested attributes and determine if a
        # modify operation is required.
        existing_role = search_results[0]
        modify_required = False

        existing_role_classification = _get_role_attribute(existing_role, 'erroleclassification')

        if existing_role_classification is None:
            modify_required = True
        elif role_classification.lower() == "application":
            if existing_role_classification[0] != "role.classification.application":
                modify_required = True
            else:
                role_classification = None  # set to None so that no change occurs
        elif role_classification.lower() == "business":
            if existing_role_classification[0] != "role.classification.business":
                modify_required = True
            else:
                role_classification = None  # set to None so that no change occurs
        else:
            raise ValueError(role_classification + "is not a valid role classification. Must be 'application' or "
                                                   "'business'.")

        existing_description = _get_role_attribute(existing_role, 'description')
        if existing_description is None:
            modify_required = True
        elif description != existing_role['description'] or description != existing_description[0]:
            modify_required = True
        else:
            description = None  # set to None so that no change occurs

        existing_owners = _get_role_attribute(existing_role, 'owner')
        new_owners = role_owners + user_owners
        if existing_owners is None:
            modify_required = True
        elif Counter(new_owners) != Counter(existing_owners):
            modify_required = True
        else:
            # set to None so that no change occurs
            role_owners = None
            user_owners = None

        existing_access_setting = _get_role_attribute(existing_role, 'eraccessoption')
        if existing_access_setting is None:
            modify_required = True
        elif not enable_access and existing_access_setting[0] != '1':
            modify_required = True
        elif enable_access and not common_access and existing_access_setting[0] != '2':
            modify_required = True
        elif enable_access and common_access and existing_access_setting[0] != '3':
            modify_required = True
        else:
            # set to None so that no change occurs
            enable_access = None
            common_access = None

        existing_access_type = _get_role_attribute(existing_role, 'erobjectprofilename')

        if existing_access_type is None:
            modify_required = True
        elif access_type.lower() == "application":
            if existing_access_type[0] != "Application":
                modify_required = True
            else:
                access_type = None  # set to None so that no change occurs
        elif access_type.lower() == "sharedfolder":
            if existing_access_type[0] != "SharedFolder":
                modify_required = True
            else:
                access_type = None  # set to None so that no change occurs
        elif access_type.lower() == "emailgroup":
            if existing_access_type[0] != "MailGroup":
                modify_required = True
            else:
                access_type = None  # set to None so that no change occurs
        elif access_type.lower() == "role":
            if existing_access_type[0] != "AccessRole":
                modify_required = True
            else:
                access_type = None  # set to None so that no change occurs

        else:
            raise ValueError(access_type + "is not a valid access type. Must be 'application', 'sharedfolder', "
                                           "'emailgroup', or 'role'.")

        existing_access_image_uri = _get_role_attribute(existing_role, 'erimageuri')
        if existing_access_image_uri is None:
            if access_image_uri != "":
                modify_required = True
            else:
                print("TRIGGERED")
                access_image_uri = None  # set to None so that no change occurs
        elif access_image_uri != existing_access_image_uri[0]:
            modify_required = True
        else:
            access_image_uri = None  # set to None so that no change occurs

        existing_access_search_terms = _get_role_attribute(existing_role, 'eraccesstag')
        if existing_access_search_terms is None:
            modify_required = True
        elif Counter(access_search_terms) != Counter(existing_access_search_terms):
            modify_required = True
        else:
            access_search_terms = None  # set to None so that no change occurs

        existing_access_additional_info = _get_role_attribute(existing_role, 'eradditionalinformation')
        if existing_access_additional_info is None:
            modify_required = True
        elif access_additional_info != existing_access_additional_info[0]:
            modify_required = True
        else:
            access_additional_info = None  # set to None so that no change occurs

        existing_access_badges = _get_role_attribute(existing_role, 'erbadge')

        new_badges = []
        for badge in access_badges:
            new_badges.append(str(badge['text'] + "~" + badge['colour']))

        if existing_access_badges is None:
            modify_required = True
        elif Counter(new_badges) != Counter(existing_access_badges):
            modify_required = True
        else:
            access_badges = None  # set to None so that no change occurs

        existing_assignment_attributes = _get_role_attribute(existing_role, 'erroleassignmentkey')
        if existing_assignment_attributes is None:
            modify_required = True
        elif Counter(assignment_attributes) != Counter(existing_assignment_attributes):
            modify_required = True
        else:
            assignment_attributes = None  # set to None so that no change occurs

        if modify_required:
            existing_dn = existing_role['itimDN']

            return _modify(
                isim_application=isim_application,
                role_dn=existing_dn,
                role_classification=role_classification,
                description=description,
                role_owners=role_owners,
                user_owners=user_owners,
                enable_access=enable_access,
                common_access=common_access,
                access_type=access_type,
                access_image_uri=access_image_uri,
                access_search_terms=access_search_terms,
                access_additional_info=access_additional_info,
                access_badges=access_badges,
                assignment_attributes=assignment_attributes
            )
        else:
            return create_return_object()

    else:
        raise ValueError("More than one instance of the role '" + name + "' was found in container '" + container_dn +
                         "'. Cannot determine what action to take.")


def _build_role_attributes_list(
        attr_type,
        role_classification: Optional[str] = None,
        description: Optional[str] = None,
        role_owners: Optional[List[str]] = None,
        user_owners: Optional[List[str]] = None,
        enable_access: Optional[bool] = None,
        common_access: Optional[bool] = None,
        access_type: Optional[str] = None,
        access_image_uri: Optional[str] = None,
        access_search_terms: Optional[List[str]] = None,
        access_additional_info: Optional[str] = None,
        access_badges: Optional[List[Dict[str, str]]] = None,
        assignment_attributes: Optional[List[str]] = None) -> List:
    """
    Build a list of attributes to be passed in a SOAP request. Used by the _create and _modify functions. Only
        arguments with a value will be set. Any arguments set to None will be left as they are. The one exception to
        this is role_owners and user_owners. If you set either one, it will overwrite all existing owners, both role
        and user. To set an attribute to an empty value, use an empty string or empty list.
    :param attr_type: The SOAP type that can be used to instantiate the an attribute object.
    :param role_classification: Set to either "application" or "business".
    :param description: A description of the role.
    :param role_owners: A list of DNs corresponding to the roles that own this role.
    :param user_owners: A list of DNs corresponding to the users that own this role.
    :param enable_access: Set to True to enable access for the role.
    :param common_access: Set to True to show the role as a common access.
    :param access_type: Set to one of 'application', 'emailgroup', 'sharedfolder' or 'role'.
    :param access_image_uri: The URI of an image to use for the access icon.
    :param access_search_terms: A list of search terms for the access.
    :param access_additional_info: Additional information about the acceess.
    :param access_badges: A list of dicts representing badges for the access. Each entry in the list must contain the
        keys 'text' and 'colour' with string values.
    :param assignment_attributes: A list of attribute names to assign to the role.
    :return:
    """

    print ("TYPE: " + str(type(attr_type)))
    attribute_list = []

    if description is not None:
        attribute_list.append(build_attribute(attr_type, 'description', [description]))

    if role_classification is not None:
        if role_classification.lower() == "application":
            attribute_list.append(
                build_attribute(attr_type, 'erroleclassification', ["role.classification.application"]))
        elif role_classification.lower() == "business":
            attribute_list.append(build_attribute(attr_type, 'erroleclassification', ["role.classification.business"]))
        else:
            raise ValueError(role_classification + "is not a valid role classification. Must be 'application' or "
                                                   "'business'.")

    if role_owners is not None and user_owners is not None:
        attribute_list.append(build_attribute(attr_type, 'owner', role_owners + user_owners))
    elif role_owners is not None:
        attribute_list.append(build_attribute(attr_type, 'owner', role_owners))
    elif user_owners is not None:
        attribute_list.append(build_attribute(attr_type, 'owner', user_owners))

    if enable_access is not None:
        if enable_access is False:
            attribute_list.append(build_attribute(attr_type, 'eraccessoption', [1]))
        else:
            if common_access is False:
                attribute_list.append(build_attribute(attr_type, 'eraccessoption', [2]))
            elif common_access is True:
                attribute_list.append(build_attribute(attr_type, 'eraccessoption', [3]))

    if description is not None:
        attribute_list.append(build_attribute(attr_type, 'eraccessdescription', [description]))

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

    if access_image_uri is not None:
        attribute_list.append(build_attribute(attr_type, 'erimageuri', [access_image_uri]))

    if access_search_terms is not None:
        attribute_list.append(build_attribute(attr_type, 'eraccesstag', access_search_terms))

    if access_additional_info is not None:
        attribute_list.append(build_attribute(attr_type, 'eradditionalinformation', [access_additional_info]))

    if access_badges is not None:
        badges = []
        for badge in access_badges:
            badges.append(str(badge['text'] + "~" + badge['colour']))
        attribute_list.append(build_attribute(attr_type, 'erbadge', badges))

    if assignment_attributes is not None:
        attribute_list.append(build_attribute(attr_type, 'erroleassignmentkey', assignment_attributes))

    return attribute_list


def _get_role_attribute(role_object: Dict, key: str) -> Optional[List]:
    """
    A method to simplify parsing of the roles returned by the SOAP API. This is only for attributes stored in the
        role's 'attributes' list. The attributes 'select', 'name', 'itimDN' and 'description' aren't part of this list
        and can be referenced by their keys.
    :param role_object: An OrderedDict representing a role as returned by the get and search calls.
    :param key: The name of a key to retrieve.
    :return: A list of values for the requested key, or None if the key doesn't exist.
    """
    attributes = role_object['attributes']['item']

    for attribute in attributes:
        if attribute['name'] == key:
            return attribute['values']['item']

    return None
