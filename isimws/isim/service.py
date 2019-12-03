from typing import List, Dict, Optional
import logging
from isimws.application.isimapplication import ISIMApplication
from isimws.utilities.tools import build_attribute
import isimws

logger = logging.getLogger(__name__)

# service name for this module
soap_service = "WSServiceService"

# minimum version required by this module
requires_version = None


def search(isim_application: ISIMApplication,
           container_dn: str,
           ldap_filter: str = "(erservicename=*)",
           check_mode=False,
           force=False):
    """
    Search for a service using a filter.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The DN of the container to search in.
    :param ldap_filter: An LDAP filter string to search for.
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state.
    :return: An IBMResponse object. If the call was successful, the data field will contain a list of the Python dict
        representations of each service matching the filter.
    """
    # The session object is handled by the ISIMApplication instance
    data = []
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
    ret_obj = isim_application.invoke_soap_request("Searching for services in container " + container_dn,
                                                   soap_service,
                                                   "searchServices",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def get(isim_application: ISIMApplication, service_dn: str, check_mode=False, force=False):
    """
    Get a service by it's DN.
    :param isim_application: The ISIMApplication instance to connect to.
    :param service_dn: The ITIM DN of the service.
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the role.
    """
    # The session object is handled by the ISIMApplication instance
    # Add the dn string to the request
    data = [service_dn]

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Retrieving a service",
                                                   soap_service,
                                                   "lookupService",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def create_account_service(isim_application: ISIMApplication,
                           container_dn: str,
                           service_type: str,
                           name: str,
                           description: Optional[str],
                           owner: Optional[str] = None,
                           service_prerequisite: Optional[str] = None,
                           define_access: bool = False,
                           access_name: Optional[str] = None,
                           access_type: Optional[str] = None,
                           access_description: Optional[str] = None,
                           access_image_uri: Optional[str] = None,
                           access_search_terms: List[str] = [],
                           access_additional_info: str = None,
                           access_badges: List[Dict[str, str]] = [],
                           configuration: Dict = {},
                           check_mode=False,
                           force=False):
    """
    Create an account service.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The DN of the container (business unit) to create the service under.
    :param service_type: The type of service to create. Corresponds to the erobjectprofilename attribute in LDAP.
        Valid types out-of-the-box are 'ADprofile', 'LdapProfile', 'PIMProfile', 'PosixAixProfile', 'PosixHpuxProfile',
        'PosixLinuxProfile', 'PosixSolarisProfile', 'WinLocalProfile', or 'HostedService'.
    :param name: The service name.
    :param description: A description of the service.
    :param owner: A DN corresponding to the user that owns the service.
    :param service_prerequisite: A DN corresponding to a service that is a prerequisite for this one.
    :param define_access: Set to True to define an access for the service. If False, all access related attributes will
        be ignored.
    :param access_name: A name for the access.
    :param access_type: Set to one of 'application', 'emailgroup', 'sharedfolder' or 'role'.
    :param access_description: A description for the access.
    :param access_image_uri: The URI of an image to use for the access icon.
    :param access_search_terms: A list of search terms for the access.
    :param access_additional_info: Additional information about the acceess.
    :param access_badges: A list of dicts representing badges for the access. Each entry in the list must contain the
        keys 'text' and 'colour' with string values.
    :param configuration: A dict of key value pairs corresponding to the LDAP attributes specific to the profile
        being used to create the service.
    :param check_mode: Set to True to enable check mode
    :param force: Set to True to force execution regardless of current state
    :return: An IBMResponse object. If the call was successful, the data field will contain the DN of the service
        that was created.
    """
    # Get the required SOAP types
    attribute_type_response = isim_application.retrieve_soap_type(soap_service,
                                                                  "ns1:WSAttribute",
                                                                  requires_version=requires_version)
    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if attribute_type_response['rc'] != 0:
        return attribute_type_response
    attr_type = attribute_type_response['data']

    attribute_list, data = _initiate_create(attr_type,
                                            container_dn,
                                            service_type,
                                            name,
                                            description,
                                            configuration)

    if owner is not None:
        attribute_list.append(build_attribute(attr_type, 'owner', [owner]))

    if service_prerequisite is not None:
        attribute_list.append(build_attribute(attr_type, 'erprerequisite', [service_prerequisite]))

    if define_access is True:
        attribute_list.append(build_attribute(attr_type, 'eraccessoption', [2]))

        if access_name is None or access_name == "":
            raise ValueError("A valid access name must be supplied if define_access is True.")

        attribute_list.append(build_attribute(attr_type, 'eraccessname', [access_name]))
        attribute_list.append(build_attribute(attr_type, 'eraccessdescription', [access_description]))

        if access_type is not None:
            if access_type.lower() == "application":
                attribute_list.append(build_attribute(attr_type, 'eraccesscategory', ["Application"]))
            elif access_type.lower() == "sharedfolder":
                attribute_list.append(build_attribute(attr_type, 'eraccesscategory', ["SharedFolder"]))
            elif access_type.lower() == "emailgroup":
                attribute_list.append(build_attribute(attr_type, 'eraccesscategory', ["MailGroup"]))
            elif access_type.lower() == "role":
                attribute_list.append(build_attribute(attr_type, 'eraccesscategory', ["AccessRole"]))
            else:
                raise ValueError(access_type + "is not a valid access type. Must be 'application', 'sharedfolder', "
                                               "'emailgroup', or 'role'.")
        else:
            # application is the default access type when it is not specified
            attribute_list.append(build_attribute(attr_type, 'eraccesscategory', ["Application"]))

        if access_image_uri is not None:
            attribute_list.append(build_attribute(attr_type, 'erimageuri', [access_image_uri]))

        attribute_list.append(build_attribute(attr_type, 'eraccesstag', access_search_terms))

        if access_additional_info is not None:
            attribute_list.append(build_attribute(attr_type, 'eradditionalinformation', [access_additional_info]))

        badges = []
        for badge in access_badges:
            badges.append(str(badge['text'] + "~" + badge['colour']))
        attribute_list.append(build_attribute(attr_type, 'erbadge', badges))

    data.append(attribute_list)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Creating an account service",
                                                   soap_service,
                                                   "createService",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def create_identity_feed(isim_application: ISIMApplication,
                         container_dn: str,
                         service_type: str,
                         name: str,
                         description: Optional[str],
                         use_workflow: bool = False,
                         evaluate_sod: bool = False,
                         placement_rule: Optional[str] = None,
                         configuration: Dict = {},
                         check_mode=False,
                         force=False):
    """
    Create an identity feed.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The DN of the container (business unit) to create the feed under.
    :param service_type: The type of feed to create. Corresponds to the erobjectprofilename attribute in LDAP.
        Valid types out-of-the-box are: 'ADFeed' (AD OrganizationalPerson identity feed), 'CSVFeed' (Comma separated
        value identity feed), 'DSML2Service' (IDI data feed), 'DSMLInfo' (DSML identity feed), or 'RFC2798Feed'
        (iNetOrgPerson identity feed).
    :param name: The service name.
    :param description: A description of the service.
    :param use_workflow: Set to True to use a workflow.
    :param evaluate_sod: Set to True to evaluate separation of duties policy when a workflow is used.
    :param placement_rule: The placement rule to use.
    :param configuration: A dict of key value pairs corresponding to the LDAP attributes specific to the profile
        being used to create the feed.
    :param check_mode: Set to True to enable check mode
    :param force: Set to True to force execution regardless of current state
    :return: An IBMResponse object. If the call was successful, the data field will contain the DN of the service
        that was created.
    """
    # Get the required SOAP types
    attribute_type_response = isim_application.retrieve_soap_type(soap_service,
                                                                  "ns1:WSAttribute",
                                                                  requires_version=requires_version)
    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if attribute_type_response['rc'] != 0:
        return attribute_type_response
    attr_type = attribute_type_response['data']

    attribute_list, data = _initiate_create(attr_type,
                                            container_dn,
                                            service_type,
                                            name,
                                            description,
                                            configuration)

    attribute_list.append(build_attribute(attr_type, 'eruseworkflow', [use_workflow]))
    attribute_list.append(build_attribute(attr_type, 'erevaluatesod', [evaluate_sod]))
    if placement_rule is not None:
        attribute_list.append(build_attribute(attr_type, 'erplacementrule', [placement_rule]))

    data.append(attribute_list)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Creating an account service",
                                                   soap_service,
                                                   "createService",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def _initiate_create(attr_type,
                     container_dn: str,
                     service_type: str,
                     name: str,
                     description: Optional[str],
                     configuration: Dict = {}):
    """
    Initiate the creation of a generic service.
    :param attr_type: The SOAP type to use for creating attributes.
    :param container_dn: The DN of the container (business unit) to create the feed under.
    :param service_type: The type of feed to create. Corresponds to the erobjectprofilename attribute in LDAP.
    :param name: The service name.
    :param description: A description of the service.
    :param configuration: A dict of key value pairs corresponding to the LDAP attributes specific to the profile
        being used to create the feed.
    :return: The partially constructed attribute list and the partially constructed data object.
    """
    data = []

    # Add the container DN to the request
    data.append(str(container_dn))

    # Add the profile name to the request
    data.append(str(service_type))

    # Populate the service attributes
    attribute_list = []

    attribute_list.append(build_attribute(attr_type, 'erservicename', [name]))

    if description is not None:
        attribute_list.append(build_attribute(attr_type, 'description', [description]))

    # add the profile specific attributes
    for key in configuration:
        if type(configuration[key]) is list:
            attribute_list.append(build_attribute(attr_type, key, configuration[key]))
        else:
            attribute_list.append(build_attribute(attr_type, key, [configuration[key]]))

    return attribute_list, data
