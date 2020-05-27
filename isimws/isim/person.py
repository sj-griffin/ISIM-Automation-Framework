from typing import List, Dict, Optional
from collections import Counter
import logging
from isimws.application.isimapplication import ISIMApplication, IBMResponse, create_return_object
from isimws.utilities.tools import build_attribute, get_soap_attribute
from isimws.utilities.dnencoder import DNEncoder
import isimws

logger = logging.getLogger(__name__)

# service name for this module
soap_service = "WSPersonService"

# minimum version required by this module
requires_version = None


def get(isim_application: ISIMApplication, person_dn: str, check_mode=False, force=False) -> IBMResponse:
    """
    Get a person by it's DN.
    :param isim_application: The ISIMApplication instance to connect to.
    :param person_dn: The ITIM DN of the person.
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the role.
    """
    # The session object is handled by the ISIMApplication instance
    # Add the dn string to the request
    data = [person_dn]

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Retrieving a person",
                                                   soap_service,
                                                   "lookupPerson",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def search(isim_application: ISIMApplication,
           ldap_filter: str = "(uid=*)",
           check_mode=False,
           force=False) -> IBMResponse:
    """
    Search for a person using a filter. The search is performed from the root.
    :param isim_application: The ISIMApplication instance to connect to.
    :param ldap_filter: An LDAP filter string to search for.
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state.
    :return: An IBMResponse object. If the call was successful, the data field will contain a list of the Python dict
        representations of each role matching the filter.
    """
    # The session object is handled by the ISIMApplication instance
    data = []

    # Add the filter string to the request
    data.append(ldap_filter)

    # Add an empty attribute list to the request
    data.append("")

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Searching for people",
                                                   soap_service,
                                                   "searchPersonsFromRoot",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def apply(isim_application: ISIMApplication,
          container_path: str,
          uid: str,
          profile: str,
          full_name: str,
          surname: str,
          aliases: Optional[List[str]] = None,
          password: Optional[str] = None,
          roles: Optional[List[tuple]] = None,
          check_mode=False,
          force=False) -> IBMResponse:
    """
    Apply a person configuration. This function will dynamically choose whether to to create or modify based on whether
        a person with the same uid exists in the same container. Note that encrypted attribute values such as passwords
        will always be updated because there is no way to determine whether the new value matches the existing one.
        Only attributes which differ from the existing person will be changed. Note that the uid, container_path, and
        profile of an existing person can't be changed. In the uid's case this is because it is used to identify the
        person. If the uid doesn't match an existing person in the specified container, a new person will be created
        with the specified uid and container_path.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_path: A path representing the container (business unit) that the person exists in. The expected
            format is '//organization_name//profile::container_name//profile::container_name'. Valid values for profile
            are 'ou' (organizational unit), 'bp' (business partner unit), 'lo' (location), or 'ad' (admin domain).
    :param uid: The username or UID for the person.
    :param profile: The name of the profile to use for the person. Currently only "Person" is supported.
    :param full_name: The full name of the person.
    :param surname: The surname of the person.
    :param aliases: A list of aliases for the person.
    :param password: A password to use as the preferred password for the person.
    :param roles: A list of tuples containing the container path and role name for each of the roles that the person
        will be part of.
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state. This will always result in a new person
        being created, regardless of whether a person with the same full name in the same container already exists. Use
        with caution.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the action taken by the server. If a modify request was used, the data field will be empty.
    """

    # Check that the compulsory attributes are set properly
    if not (isinstance(container_path, str) and len(container_path) > 0 and
            isinstance(uid, str) and len(uid) > 0 and
            isinstance(profile, str) and len(profile) > 0 and
            isinstance(full_name, str) and len(full_name) > 0 and
            isinstance(surname, str) and len(surname) > 0):
        raise ValueError("Invalid person configuration. container_path, uid, profile, full_name, and surname "
                         "must have non-empty string values.")

    # If any values are set to None, they must be replaced with empty values. This is because these values will be
    # passed to methods that interpret None as 'no change', whereas we want them to be explicitly set to empty values.
    if aliases is None:
        aliases = []

    if password is None:
        password = ""

    if roles is None:
        roles = []

    # Convert the container path into a DN that can be passed to the SOAP API. This also validates the container path.
    dn_encoder = DNEncoder(isim_application)
    container_dn = dn_encoder.container_path_to_dn(container_path)

    # Convert the role names into DNs that can be passed to the SOAP API
    role_dns = []
    for role in roles:
        role_dns.append(dn_encoder.encode_to_isim_dn(container_path=str(role[0]),
                                                     name=str(role[1]),
                                                     object_type='role'))

    # Resolve the instance with the specified name in the specified container
    existing_person = dn_encoder.get_unique_object(container_path=container_path,
                                                   name=uid,
                                                   object_type='person')

    if existing_person is None or force:
        # If the instance doesn't exist yet, create a new role and return the response
        if check_mode:
            return create_return_object(changed=True)
        else:
            return _create(
                isim_application=isim_application,
                container_dn=container_dn,
                uid=uid,
                profile=profile,
                full_name=full_name,
                surname=surname,
                aliases=aliases,
                password=password,
                role_dns=role_dns
            )
    else:
        # If an existing instance was found, compare it's attributes with the requested attributes and determine if a
        # modify operation is required.
        modify_required = False

        existing_full_name = get_soap_attribute(existing_person, 'cn')

        if existing_full_name is None:
            modify_required = True
        elif existing_full_name[0] != full_name:
            modify_required = True
        else:
            full_name = None  # set to None so that no change occurs

        existing_surname = get_soap_attribute(existing_person, 'sn')

        if existing_surname is None:
            modify_required = True
        elif existing_surname[0] != surname:
            modify_required = True
        else:
            surname = None  # set to None so that no change occurs

        existing_aliases = get_soap_attribute(existing_person, 'eraliases')

        if existing_aliases is None:
            if aliases != []:
                modify_required = True
            else:
                aliases = None  # set to None so that no change occurs
        elif Counter(aliases) != Counter(existing_aliases):
            modify_required = True
        else:
            aliases = None  # set to None so that no change occurs

        existing_password = get_soap_attribute(existing_person, 'erpersonpassword')

        if existing_password is None:
            if password != "":
                modify_required = True
            else:
                password = None  # set to None so that no change occurs
        elif existing_password[0] != password:
            modify_required = True
        else:
            password = None  # set to None so that no change occurs

        existing_roles = get_soap_attribute(existing_person, 'erroles')

        if existing_roles is None:
            if role_dns != []:
                modify_required = True
            else:
                role_dns = None  # set to None so that no change occurs
        elif Counter(role_dns) != Counter(existing_roles):
            modify_required = True
        else:
            role_dns = None  # set to None so that no change occurs

        if modify_required:
            if check_mode:
                return create_return_object(changed=True)
            else:
                existing_dn = existing_person['itimDN']

                return _modify(
                    isim_application=isim_application,
                    person_dn=existing_dn,
                    full_name=full_name,
                    surname=surname,
                    aliases=aliases,
                    password=password,
                    role_dns=role_dns
                )
        else:
            return create_return_object(changed=False)


def _create(isim_application: ISIMApplication,
            container_dn: str,
            uid: str,
            profile: str,
            full_name: str,
            surname: str,
            aliases: List[str] = [],
            password: str = "",
            role_dns: List[str] = []) -> IBMResponse:
    """
    Create a Person. To set an attribute to an empty value, use an empty string or empty list. Do not use None as this
        indicates no change, which is not applicable to a create operation.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The DN of the container (business unit) to create the person under.
    :param uid: The username or UID for the person.
    :param profile: The name of the profile to use for the person. Currently only "Person" is supported.
    :param full_name: The full name of the person.
    :param surname: The surname of the person.
    :param aliases: A list of aliases for the person.
    :param password: A password to use as the preferred password for the person.
    :param role_dns: A list of DNs corresponding to roles that the person will be part of.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the action taken by the server.
    """
    data = []

    # Get the required SOAP types
    person_type_response = isim_application.retrieve_soap_type(soap_service,
                                                               "ns1:WSPerson",
                                                               requires_version=requires_version)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if person_type_response['rc'] != 0:
        return person_type_response
    person_type = person_type_response['data']

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

    # Setup the person object
    person_object = person_type()

    # Check that the profile is valid
    if profile.lower() == "person":
        person_object['profileName'] = "Person"
    else:
        raise ValueError(profile + "is not a valid profile. Must be 'Person'.")

    person_object['select'] = False

    attribute_list = _build_person_attributes_list(
        attr_type=attr_type,
        uid=uid,
        surname=surname,
        full_name=full_name,
        aliases=aliases,
        password=password,
        role_dns=role_dns
    )

    person_object['attributes'] = {'item': attribute_list}
    data.append(person_object)

    # Leave the date object empty
    data.append(None)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Creating a Person",
                                                   soap_service,
                                                   "createPerson",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def _modify(isim_application: ISIMApplication,
            person_dn: str,
            full_name: Optional[str] = None,
            surname: Optional[str] = None,
            aliases: Optional[List[str]] = None,
            password: Optional[str] = None,
            role_dns: Optional[List[str]] = None) -> IBMResponse:
    """
    Modify the attributes of an existing Person. Only arguments with a value will be changed. Any arguments set to None
        will be left as they are. To set an attribute to an empty value, use an empty string or empty list.
    :param isim_application: The ISIMApplication instance to connect to.
    :param person_dn: The DN of the existing person to modify.
    :param full_name: The full name of the person.
    :param surname: The surname of the person.
    :param aliases: A list of aliases for the person.
    :param password: A password to use as the preferred password for the person.
    :param role_dns: A list of DNs corresponding to roles that the person will be part of.
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

    # Add the person DN to the request
    data.append(person_dn)

    # Setup the list of modified attributes and add them to the request
    attribute_list = _build_person_attributes_list(
        attr_type=attr_type,
        full_name=full_name,
        surname=surname,
        aliases=aliases,
        password=password,
        role_dns=role_dns
    )

    data.append(attribute_list)

    # Leave the date object empty
    data.append(None)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Modifying a Person",
                                                   soap_service,
                                                   "modifyPerson",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def _build_person_attributes_list(
        attr_type,
        uid: Optional[str] = None,
        full_name: Optional[str] = None,
        surname: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        password: Optional[str] = None,
        role_dns: Optional[List[str]] = None) -> List:
    """
    Build a list of attributes to be passed in a SOAP request. Used by the _create and _modify functions. Only
        arguments with a value will be set. Any arguments set to None will be left as they are.
        To set an attribute to an empty value, use an empty string or empty list.
    :param uid: The username or UID for the person.
    :param full_name: The full name of the person.
    :param surname: The surname of the person.
    :param aliases: A list of aliases for the person.
    :param password: A password to use as the preferred password for the person.
    :param role_dns: A list of DNs corresponding to roles that the person will be part of.
    :return: A list of attributes formatted to be passed to the SOAP API.
    """

    attribute_list = []

    if uid is not None:
        if uid == '':
            attribute_list.append(build_attribute(attr_type, 'uid', []))
        else:
            attribute_list.append(build_attribute(attr_type, 'uid', [uid]))

    if full_name is not None:
        if full_name == '':
            attribute_list.append(build_attribute(attr_type, 'cn', []))
        else:
            attribute_list.append(build_attribute(attr_type, 'cn', [full_name]))

    if surname is not None:
        if surname == '':
            attribute_list.append(build_attribute(attr_type, 'sn', []))
        else:
            attribute_list.append(build_attribute(attr_type, 'sn', [surname]))

    if aliases is not None:
        attribute_list.append(build_attribute(attr_type, 'eraliases', aliases))

    if password is not None:
        if password == '':
            attribute_list.append(build_attribute(attr_type, 'erpersonpassword', []))
        else:
            attribute_list.append(build_attribute(attr_type, 'erpersonpassword', [password]))

    if role_dns is not None:
        attribute_list.append(build_attribute(attr_type, 'erroles', role_dns))

    return attribute_list
