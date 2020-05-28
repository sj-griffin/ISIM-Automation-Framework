from typing import List, Dict, Optional
from collections import Counter
import logging
from isimws.application.isimapplication import ISIMApplication, IBMResponse, create_return_object
from isimws.utilities.tools import build_attribute, get_soap_attribute, strip_zeep_element_data
from isimws.utilities.dnencoder import DNEncoder
import isimws

logger = logging.getLogger(__name__)

# service name for this module
soap_service = "WSOrganizationalContainerService"

# minimum version required by this module
requires_version = None


def search(isim_application: ISIMApplication,
           parent_dn: str,
           container_name: str,
           profile: str,
           check_mode=False,
           force=False) -> IBMResponse:
    """
    Search for a container by it's name.
    :param isim_application: The ISIMApplication instance to connect to.
    :param parent_dn: The DN of the parent container to search under. All descendants of this container will be
        searched, not just direct children. To search for an Organization, you must specify the root container here,
        e.g. "ou=demo,dc=com".
    :param container_name: The name of the container to search for. Only containers that exactly match the name will
        appear in the results.
    :param container_name: The name of the container to search for.
    :param profile: The type of container to search for. Valid values are 'Organization', 'OrganizationalUnit',
        'BPOrganization', 'Location', or 'AdminDomain'.
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state.
    :return: An IBMResponse object. If the call was successful, the data field will contain a list of the Python dict
        representations of each role matching the filter.
    """
    # The session object is handled by the ISIMApplication instance
    data = []

    # Retrieve the parent container object
    container_response = isimws.isim.container.get(isim_application=isim_application, container_dn=parent_dn)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if container_response['rc'] != 0:
        return container_response

    container_object = container_response['data']
    data.append(container_object)

    # Add the container profile name to the request
    if not (profile == "Organization" or
            profile == "OrganizationalUnit" or
            profile == "Location" or
            profile == "AdminDomain" or
            profile == "BPOrganization"):
        raise ValueError("'" + profile + "' is not a valid container profile. Valid values are 'Organization', "
                                         "'OrganizationalUnit', 'BPOrganization', 'Location', or 'AdminDomain'.")
    data.append(profile)

    # Add the container name to the request
    data.append(container_name)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Searching for containers",
                                                   soap_service,
                                                   "searchContainerByName",
                                                   data,
                                                   requires_version=requires_version)

    ret_obj = strip_zeep_element_data(ret_obj)

    return ret_obj


# Get a container by it's DN
def get(isim_application: ISIMApplication, container_dn: str, check_mode=False, force=False) -> IBMResponse:
    # The session object is handled by the ISIMApplication instance
    # Add the dn string
    data = [container_dn]

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Retrieving an organisational container",
                                                   soap_service,
                                                   "lookupContainer",
                                                   data,
                                                   requires_version=requires_version)

    return ret_obj


# Required attributes
# Organization: organization name (str) [o], description (optional str) [description]
# Object class: organization
# Profile name: Organization

# Admin domain: admin domain name (str) [ou], description (optional str) [description], administrator (optional list[str] of person DNs) [erAdministrator]
# Object class: SecurityDomain
# Profile name: AdminDomain / SecurityDomain (depending on what operation is being performed)

# Business partner unit: business partner name (str) [ou], sponsor (optional str - a person DN) [erSponsor]
# Object class: erBPOrg
# Profile name: BPOrganization / BusinessPartnerOrganisation (depending on what operation is being performed)

# Location: location name (str) [l], description (optional str) [description], supervisor (optional str -  person DN) [erSupervisor]
# Object class: locality
# Profile name: Location

# Organizational unit: organizational unit name (str) [ou], description (optional str) [description], supervisor (optional str -  person DN) [erSupervisor]
# Object class: organizationalunit
# Profile name: OrganizationalUnit

def apply(isim_application: ISIMApplication,
          parent_container_path: str,
          profile: str,
          name: str,
          description: Optional[str] = None,
          associated_people: Optional[List[tuple]] = None,
          check_mode=False,
          force=False) -> IBMResponse:
    """
    Apply a container configuration. This function will dynamically choose whether to to create or modify based on
        whether a container with the same name and profile exists in the same parent container. Only attributes which
        differ from the existing container will be changed. Note that the name, profile, and parent_container_path of
        an existing container can't be changed because they are used to identify the container. If they don't match an
        existing container, a new container will be created with the specified name, profile, and parent_container_path.
    :param isim_application: The ISIMApplication instance to connect to.
    :param parent_container_path: A path representing the container (business unit) that the container exists in. The
        expected format is '//organization_name//profile::container_name//profile::container_name'. Valid values for
        profile are 'ou' (organizational unit), 'bp' (business partner unit), 'lo' (location), or 'ad' (admin domain).
        To create an Organization, you must specify the root container here, i.e. "//".
    :param profile: The container profile to use. Valid values are 'Organization', 'OrganizationalUnit',
        'BPOrganization', 'Location', or 'AdminDomain'.
    :param name: The container name. This will be automatically applied to the correct attribute depending on the
        container profile selected.
    :param description: A description of the container. Will be ignored if the selected container profile doesn't use
        a description.
    :param associated_people: A list of tuples containing the container path and UID of each of the people associated
        with the container. The way this list will be interpreted changes depending on the selected container profile.
        For an organization, it will be ignored. For an organizational unit or location, the first entry in the list
        will be set as the supervisor, and the other entries will be ignored. For a business partner unit, the first
        entry in the list will be set as the sponsor, and the other entries will be ignored. For an admin domain, each
        entry in the list will be set as an administrator of the admin domain.
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state. This will always result in a new container
        being created, regardless of whether a container with the same name and profile in the same parent container
        already exists. Use with caution.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the action taken by the server. If a modify request was used, the data field will be empty.
    """

    # Validate the profile name. If performing a modify, make sure it matches the existing profile. In fact, the
    # profile should be used to identify containers. The logic to select the attributes to modify should probably be
    # done in apply, and the create and modify methods just take a list of attributes to set.

    # Check that the compulsory attributes are set properly
    if not (isinstance(parent_container_path, str) and len(parent_container_path) > 0 and
            isinstance(profile, str) and len(profile) > 0 and
            isinstance(name, str) and len(name) > 0):
        raise ValueError("Invalid container configuration. parent_container_path, profile, and name must have "
                         "non-empty string values.")

    # Validate the selected profile
    if profile == 'Organization':
        profile_prefix = 'o'
    elif profile == 'OrganizationalUnit':
        profile_prefix = 'ou'
    elif profile == 'BPOrganization':
        profile_prefix = 'bp'
    elif profile == 'Location':
        profile_prefix = 'lo'
    elif profile == 'AdminDomain':
        profile_prefix = 'ad'
    else:
        raise ValueError("'" + profile + "' is not a valid container profile. Valid values are 'Organization', "
                                         "'OrganizationalUnit', 'BPOrganization', 'Location', or 'AdminDomain'.")

    # If any values are set to None, they must be replaced with empty values. This is because these values will be
    # passed to methods that interpret None as 'no change', whereas we want them to be explicitly set to empty values.
    if description is None:
        description = ""

    if associated_people is None:
        associated_people = []

    # Convert the parent container path into a DN that can be passed to the SOAP API. This also validates the parent
    # container path.
    dn_encoder = DNEncoder(isim_application)
    parent_container_dn = dn_encoder.container_path_to_dn(parent_container_path)

    # Convert the associated people names into DNs that can be passed to the SOAP API
    # We don't perform this step for an organization as an organization cannot have associated people
    associated_people_dns = []
    if profile != "Organization":
        for person in associated_people:
            associated_people_dns.append(dn_encoder.encode_to_isim_dn(container_path=str(person[0]),
                                                                      name=str(person[1]),
                                                                      object_type='person'))

    # Resolve the instance with the specified name in the specified container
    existing_container = dn_encoder.get_unique_object(container_path=parent_container_path,
                                                      name=profile_prefix + "::" + name,
                                                      object_type='container')

    if existing_container is None or force:
        # If the instance doesn't exist yet, create a new role and return the response
        if check_mode:
            return create_return_object(changed=True)
        else:
            return _create(
                isim_application=isim_application,
                parent_container_dn=parent_container_dn,
                profile=profile,
                name=name,
                description=description,
                associated_people_dns=associated_people_dns
            )
    else:
        # If an existing instance was found, compare it's attributes with the requested attributes and determine if a
        # modify operation is required.
        modify_required = False

        existing_description = get_soap_attribute(existing_container, 'description')

        if (profile == "Organization" or
                profile == "OrganizationalUnit" or
                profile == "Location" or
                profile == "AdminDomain"):

            if existing_description is None:
                if description != '':
                    modify_required = True
                else:
                    description = None  # set to None so that no change occurs
            elif description != existing_description[0]:
                modify_required = True
            else:
                description = None  # set to None so that no change occurs
        else:
            description = None  # set to None so that no change occurs

        existing_supervisor = get_soap_attribute(existing_container, 'erSupervisor')
        existing_sponsor = get_soap_attribute(existing_container, 'erSponsor')
        existing_administrators = get_soap_attribute(existing_container, 'erAdministrator')

        if (profile == "OrganizationalUnit" or
                profile == "Location"):

            if associated_people_dns == []:
                new_supervisor = ''
            else:
                new_supervisor = associated_people_dns[0]

            if existing_supervisor is None:
                if new_supervisor != '':
                    modify_required = True
                else:
                    associated_people_dns = None  # set to None so that no change occurs
            elif new_supervisor != existing_supervisor[0]:
                modify_required = True
            else:
                associated_people_dns = None  # set to None so that no change occurs

        elif profile == "BPOrganization":
            if associated_people_dns == []:
                new_sponsor = ''
            else:
                new_sponsor = associated_people_dns[0]

            if existing_sponsor is None:
                if new_sponsor != '':
                    modify_required = True
                else:
                    associated_people_dns = None  # set to None so that no change occurs
            elif new_sponsor != existing_sponsor[0]:
                modify_required = True
            else:
                associated_people_dns = None  # set to None so that no change occurs

        elif profile == "AdminDomain":
            if existing_administrators is None:
                if associated_people_dns != []:
                    modify_required = True
                else:
                    associated_people_dns = None  # set to None so that no change occurs
            elif Counter(associated_people_dns) != Counter(existing_administrators):
                modify_required = True
            else:
                associated_people_dns = None  # set to None so that no change occurs

        else:
            associated_people_dns = None  # set to None so that no change occurs

        if modify_required:
            if check_mode:
                return create_return_object(changed=True)
            else:
                existing_dn = existing_container['itimDN']

                return _modify(
                    isim_application=isim_application,
                    container_dn=existing_dn,
                    profile=profile,
                    description=description,
                    associated_people_dns=associated_people_dns
                )
        else:
            return create_return_object(changed=False)


def _create(isim_application: ISIMApplication,
            parent_container_dn: str,
            profile: str,
            name: str,
            description: str = "",
            associated_people_dns: List[str] = []) -> IBMResponse:
    """
    Create a Container. To set an attribute to an empty value, use an empty string or empty list. Do not use None as
    this indicates no change, which is not applicable to a create operation.
    :param isim_application: The ISIMApplication instance to connect to.
    :param parent_container_dn: The DN of the existing container (business unit) to create the container under. To
        create an Organization, you must specify the root container here, e.g. "ou=demo,dc=com".
    :param profile: The container profile to use. Valid values are 'Organization', 'OrganizationalUnit',
        'BPOrganization', 'Location', or 'AdminDomain'.
    :param name: The container name. This will be automatically applied to the correct attribute depending on the
        container profile selected.
    :param description: A description of the container. Will be ignored if the selected container profile doesn't use
        a description.
    :param associated_people_dns: A list of DNs corresponding to the people associated with the container. The way this
        list will be interpreted changes depending on the selected container profile. For an organization, it will be
        ignored. For an organizational unit or location, the first entry in the list will be set as the supervisor, and
        the other entries will be ignored. For a business partner unit, the first entry in the list will be set as the
        sponsor, and the other entries will be ignored. For an admin domain, each entry in the list will be set as an
        administrator of the admin domain.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the action taken by the server.
    """
    data = []

    # Get the required SOAP types
    container_type_response = isim_application.retrieve_soap_type(soap_service,
                                                                  "ns1:WSOrganizationalContainer",
                                                                  requires_version=requires_version)
    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if container_type_response['rc'] != 0:
        return container_type_response
    container_type = container_type_response['data']

    # Retrieve the attribute type
    attribute_type_response = isim_application.retrieve_soap_type(soap_service,
                                                                  "ns1:WSAttribute",
                                                                  requires_version=requires_version)
    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if attribute_type_response['rc'] != 0:
        return attribute_type_response
    attr_type = attribute_type_response['data']

    # Retrieve the parent container object (the business unit)
    parent_container_response = isimws.isim.container.get(isim_application=isim_application, container_dn=parent_container_dn)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if parent_container_response['rc'] != 0:
        return parent_container_response

    parent_container_object = parent_container_response['data']
    data.append(parent_container_object)

    # Setup the new container object
    container_object = container_type()

    container_object['select'] = False
    container_object['name'] = name

    # The SOAP API uses different profile names depending on which operation is being performed for some reason. We
    # set the profile name here according to what is expected for a create operation.
    if profile == "BPOrganization":
        container_object['profileName'] = "BusinessPartnerOrganization"
    elif profile == "AdminDomain":
        container_object['profileName'] = "SecurityDomain"
    else:
        container_object['profileName'] = profile

    # Populate the container attributes
    attribute_list = _build_container_attributes_list(
        attr_type=attr_type,
        name=name,
        profile=profile,
        description=description,
        associated_people_dns=associated_people_dns
    )

    container_object['attributes'] = {'item': attribute_list}
    data.append(container_object)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Creating a Container",
                                                   soap_service,
                                                   "createContainer",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def _modify(isim_application: ISIMApplication,
            container_dn: str,
            profile: str,
            description: Optional[str] = None,
            associated_people_dns: Optional[List[str]] = None) -> IBMResponse:
    """
    Modify the attributes of an existing Container. Only arguments with a value will be changed. Any arguments set to
        None will be left as they are. To set an attribute to an empty value, use an empty string or empty list.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The DN of the existing container to modify.
    :param profile: The container profile to use. Valid values are 'Organization', 'OrganizationalUnit',
        'BPOrganization', 'Location', or 'AdminDomain'. Note that this value cannot be modified- this argument is only
        used to determine how to process the other arguments.
    :param description: A description of the container. Will be ignored if the selected container profile doesn't use
        a description.
    :param associated_people_dns: A list of DNs corresponding to the people associated with the container. The way this
        list will be interpreted changes depending on the selected container profile. For an organization, it will be
        ignored. For an organizational unit or location, the first entry in the list will be set as the supervisor, and
        the other entries will be ignored. For a business partner unit, the first entry in the list will be set as the
        sponsor, and the other entries will be ignored. For an admin domain, each entry in the list will be set as an
        administrator of the admin domain.
    :return: An IBMResponse object. If the call was successful, the data field will be empty.
    """

    # Get the required SOAP types
    container_type_response = isim_application.retrieve_soap_type(soap_service,
                                                                  "ns1:WSOrganizationalContainer",
                                                                  requires_version=requires_version)
    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if container_type_response['rc'] != 0:
        return container_type_response
    container_type = container_type_response['data']

    # Retrieve the attribute type
    attribute_type_response = isim_application.retrieve_soap_type(soap_service,
                                                                  "ns1:WSAttribute",
                                                                  requires_version=requires_version)
    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if attribute_type_response['rc'] != 0:
        return attribute_type_response
    attr_type = attribute_type_response['data']

    data = []

    # Setup the container object
    container_object = container_type()

    container_object['select'] = False
    container_object['itimDN'] = container_dn

    # Populate the container attributes
    attribute_list = _build_container_attributes_list(
        attr_type=attr_type,
        name=None,
        profile=profile,
        description=description,
        associated_people_dns=associated_people_dns
    )

    container_object['attributes'] = {'item': attribute_list}
    data.append(container_object)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Modifying a Container",
                                                   soap_service,
                                                   "modifyContainer",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def _build_container_attributes_list(
        attr_type,
        profile: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        associated_people_dns: Optional[List[str]] = None) -> List:
    """
    Build a list of attributes to be passed in a SOAP request. Used by the _create and _modify functions. Only
        arguments with a value will be set. Any arguments set to None will be left as they are. To set an attribute to
        an empty value, use an empty string or empty list.
    :param attr_type: The SOAP type that can be used to instantiate an attribute object.
    :param profile: The container profile to use. Valid values are 'Organization', 'OrganizationalUnit',
        'BPOrganization', 'Location', or 'AdminDomain'. This will not be set here, it is only used to
        determine how to process the other arguments.
    :param name: The container name. This will be automatically applied to the correct attribute depending on the
        container profile selected.
    :param description: A description of the container. Will be ignored if the selected container profile doesn't use
        a description.
    :param associated_people_dns: A list of DNs corresponding to the people associated with the container. The way this
        list will be interpreted changes depending on the selected container profile. For an organization, it will be
        ignored. For an organizational unit or location, the first entry in the list will be set as the supervisor, and
        the other entries will be ignored. For a business partner unit, the first entry in the list will be set as the
        sponsor, and the other entries will be ignored. For an admin domain, each entry in the list will be set as an
        administrator of the admin domain.
    :return: A list of attributes formatted to be passed to the SOAP API.
    """

    attribute_list = []

    if name is not None:
        if profile == "Organization":
            attribute_list.append(build_attribute(attr_type, 'o', [name]))
        elif profile == "OrganizationalUnit" or profile == "BPOrganization" or profile == "AdminDomain":
            attribute_list.append(build_attribute(attr_type, 'ou', [name]))
        elif profile == "Location":
            attribute_list.append(build_attribute(attr_type, 'l', [name]))
        else:
            raise ValueError("'" + profile + "' is not a valid container profile. Valid values are 'Organization', "
                                             "'OrganizationalUnit', 'BPOrganization', 'Location', or 'AdminDomain'.")

    if description is not None:
        if profile == "Organization" or \
                profile == "OrganizationalUnit" or \
                profile == "Location" or \
                profile == "AdminDomain":
            if description == '':
                attribute_list.append(build_attribute(attr_type, 'description', []))
            else:
                attribute_list.append(build_attribute(attr_type, 'description', [description]))
        elif profile == "BPOrganization":
            pass
        else:
            raise ValueError("'" + profile + "' is not a valid container profile. Valid values are 'Organization', "
                                             "'OrganizationalUnit', 'BPOrganization', 'Location', or 'AdminDomain'.")

    if associated_people_dns is not None:
        if profile == "Organization":
            pass
        elif profile == "OrganizationalUnit" or profile == "Location":
            attribute_list.append(build_attribute(attr_type, 'erSupervisor', [associated_people_dns[0]]))
        elif profile == "BPOrganization":
            attribute_list.append(build_attribute(attr_type, 'erSponsor', [associated_people_dns[0]]))
        elif profile == "AdminDomain":
            attribute_list.append(build_attribute(attr_type, 'erAdministrator', associated_people_dns))
        else:
            raise ValueError("'" + profile + "' is not a valid container profile. Valid values are 'Organization', "
                                             "'OrganizationalUnit', 'BPOrganization', 'Location', or 'AdminDomain'.")

    return attribute_list
