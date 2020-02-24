from typing import List, Dict, Optional
import logging
from collections import Counter
from isimws.application.isimapplication import ISIMApplication, IBMResponse, create_return_object
from isimws.utilities.tools import build_attribute, get_soap_attribute, list_soap_attribute_keys
from isimws.utilities.dnencoder import DNEncoder
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


def apply_account_service(isim_application: ISIMApplication,
                          container_path: str,
                          name: str,
                          service_type: str,
                          description: Optional[str] = None,
                          owner_name: Optional[str] = None,
                          service_prerequisite_name: Optional[str] = None,
                          define_access: bool = None,
                          access_name: Optional[str] = None,
                          access_type: Optional[str] = None,
                          access_description: Optional[str] = None,
                          access_image_uri: Optional[str] = None,
                          access_search_terms: Optional[List[str]] = None,
                          access_additional_info: Optional[str] = None,
                          access_badges: Optional[List[Dict[str, str]]] = None,
                          configuration: Dict = {},
                          check_mode=False,
                          force=False) -> IBMResponse:
    """
    Apply an account service configuration. This function will dynamically choose whether to to create or modify based
        on whether a service with the same name exists in the same container. Only attributes which differ from the
        existing service will be changed. Note that encrypted attribute values such as passwords will always be updated
        because there is no way to determine whether the new value matches the existing one. Note that the name and
        container_dn of an existing service can't be changed because they are used to identify the service. If they
        don't match an existing service, a new service will be created with the specified name and container_dn.
        The service_type of an existing service cannot be changed either. To do this you will need to delete the old
        service and create a new one.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_path: A path representing the container (business unit) that the service exists in. The expected
        format is '//organization_name//profile::container_name//profile::container_name'. Valid values for profile
        are 'ou' (organizational unit), 'bp' (business partner unit), 'lo' (location), or 'ad' (admin domain).
    :param name: The service name.
    :param service_type: The type of service to create. Corresponds to the erobjectprofilename attribute in LDAP.
        Valid types out-of-the-box are 'ADprofile', 'LdapProfile', 'PIMProfile', 'PosixAixProfile', 'PosixHpuxProfile',
        'PosixLinuxProfile', 'PosixSolarisProfile', 'WinLocalProfile', or 'HostedService'.
    :param description: A description of the service.
    :param owner_name: The uid of the user that owns the service.
    :param service_prerequisite_name: The name of the service that is a prerequisite for this one.
    :param define_access: Set to True to define an access for the service.
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
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state. This will always result in a new service
        being created, regardless of whether a service with the same name in the same container already exists. Use with
        caution.
    :return: An IBMResponse object. If the call was successful, the data field will contain the DN of the service
        that was created. If a modify request was used, the data field will be empty.
    """

    # Check that the compulsory attributes are set properly
    if not (isinstance(container_path, str) and len(container_path) > 0 and
            isinstance(name, str) and len(name) > 0 and
            isinstance(service_type, str) and len(service_type) > 0 and
            isinstance(configuration, Dict) and len(list(configuration.keys())) > 0):
        raise ValueError("Invalid service configuration. organization, container_path, name, and service_type must "
                         "have non-empty string values. configuration must be a non-empty dictionary.")

    if define_access is True:
        if not (isinstance(access_name, str) and len(access_name) > 0):
            raise ValueError("Invalid service configuration. A valid access name must be supplied if define_access "
                             "is True.")

    # If any values are set to None, they must be replaced with empty values. This is because these values will be
    # passed to methods that interpret None as 'no change', whereas we want them to be explicitly set to empty values.
    if description is None:
        description = ""

    if owner_name is None:
        owner_name = ""

    if service_prerequisite_name is None:
        service_prerequisite_name = ""

    if define_access is None:
        define_access = False

    if access_name is None:
        access_name = ""

    if access_type is None:
        access_type = ""

    if access_description is None:
        access_description = ""

    if access_image_uri is None:
        access_image_uri = ""

    if access_search_terms is None:
        access_search_terms = []

    if access_additional_info is None:
        access_additional_info = ""

    if access_badges is None:
        access_badges = []

    for key in configuration:
        if configuration[key] is None:
            configuration[key] = ""

    # convert each configuration key to lower case
    list_of_keys = list(configuration.keys())
    for key_name in list_of_keys:
        if key_name.lower() != key_name:
            configuration[key_name.lower()] = configuration[key_name]
            del configuration[key_name]

    # Convert the container path into a DN that can be passed to the SOAP API. This also validates the container path.
    dn_encoder = DNEncoder(isim_application)
    container_dn = dn_encoder.container_path_to_dn(container_path)

    # Extract the organisation name from the container path.
    organization = container_path.split('//')[1]

    # Convert the owner name and service prerequisite name into DNs that can be passed to the SOAP API
    if owner_name != "":
        owner_dn = dn_encoder.encode_to_isim_dn(organization=organization,
                                                name=str(owner_name),
                                                object_type='person')
    else:
        owner_dn = ""

    if service_prerequisite_name != "":
        service_prerequisite_dn = dn_encoder.encode_to_isim_dn(organization=organization,
                                                               name=str(service_prerequisite_name),
                                                               object_type='service')
    else:
        service_prerequisite_dn = ""

    # Search for instances with the specified name in the specified container
    search_response = search(
        isim_application=isim_application,
        container_dn=container_dn,
        ldap_filter="(erservicename=" + name + ")"
    )
    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if search_response['rc'] != 0:
        return search_response
    search_results = search_response['data']

    # Because the search function can return results with names containing the specified name, we need to confirm which
    # results have the exact name that was searched for.
    exact_matches = []
    for result in search_results:
        if result['name'] == name:
            exact_matches.append(result)

    if len(exact_matches) == 0 or force:
        # If there are no results, create a new service and return the response
        if check_mode:
            return create_return_object(changed=True)
        else:
            return _create_account_service(isim_application=isim_application,
                                           container_dn=container_dn,
                                           name=name,
                                           service_type=service_type,
                                           description=description,
                                           owner=owner_dn,
                                           service_prerequisite=service_prerequisite_dn,
                                           define_access=define_access,
                                           access_name=access_name,
                                           access_type=access_type,
                                           access_description=access_description,
                                           access_image_uri=access_image_uri,
                                           access_search_terms=access_search_terms,
                                           access_additional_info=access_additional_info,
                                           access_badges=access_badges,
                                           configuration=configuration)

    elif len(exact_matches) == 1:
        # If exactly one result is found, compare it's attributes with the requested attributes and determine if a
        # modify operation is required.
        existing_service = exact_matches[0]
        modify_required = False

        existing_service_type = existing_service['profileName']

        if service_type != existing_service_type:
            return create_return_object(changed=False,
                                        warnings=["The service '" + name + "' in container '" + container_dn + "' is "
                                                  "of service type '" + existing_service_type + "'. You can't change "
                                                  "the service type to '" + service_type + "'. Create a new service "
                                                  "with a different name instead."])

        existing_description = get_soap_attribute(existing_service, 'description')
        if existing_description is None:
            if description != '':
                modify_required = True
            else:
                description = None  # set to None so that no change occurs
        elif description != existing_description[0]:
            modify_required = True
        else:
            description = None  # set to None so that no change occurs

        existing_owner = get_soap_attribute(existing_service, 'owner')
        if existing_owner is None:
            if owner_dn != '':
                modify_required = True
            else:
                owner = None  # set to None so that no change occurs
        elif owner_dn != existing_owner[0]:
            modify_required = True
        else:
            owner_dn = None  # set to None so that no change occurs

        existing_service_prerequisite = get_soap_attribute(existing_service, 'erprerequisite')
        if existing_service_prerequisite is None:
            if service_prerequisite_dn != '':
                modify_required = True
            else:
                service_prerequisite = None  # set to None so that no change occurs
        elif service_prerequisite_dn != existing_service_prerequisite[0]:
            modify_required = True
        else:
            service_prerequisite_dn = None  # set to None so that no change occurs

        existing_access_setting = get_soap_attribute(existing_service, 'eraccessoption')
        if existing_access_setting is None:
            if define_access is True:
                modify_required = True
            else:
                define_access = None  # set to None so that no change occurs
        elif not define_access and existing_access_setting[0] != '':
            modify_required = True
        elif define_access and existing_access_setting[0] != '2':
            modify_required = True
        else:
            define_access = None  # set to None so that no change occurs

        existing_access_name = get_soap_attribute(existing_service, 'eraccessname')
        if existing_access_name is None:
            if access_name != '':
                modify_required = True
            else:
                access_name = None  # set to None so that no change occurs
        elif access_name != existing_access_name[0]:
            modify_required = True
        else:
            access_name = None  # set to None so that no change occurs

        existing_access_type = get_soap_attribute(existing_service, 'eraccesscategory')

        if existing_access_type is None:
            if access_type != '':
                modify_required = True
            else:
                access_type = None  # set to None so that no change occurs
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

        existing_access_description = get_soap_attribute(existing_service, 'eraccessdescription')
        if existing_access_description is None:
            if access_description != '':
                modify_required = True
            else:
                access_description = None  # set to None so that no change occurs
        elif access_description != existing_access_description[0]:
            modify_required = True
        else:
            access_description = None  # set to None so that no change occurs

        existing_access_image_uri = get_soap_attribute(existing_service, 'erimageuri')
        if existing_access_image_uri is None:
            if access_image_uri != '':
                modify_required = True
            else:
                access_image_uri = None  # set to None so that no change occurs
        elif access_image_uri != existing_access_image_uri[0]:
            modify_required = True
        else:
            access_image_uri = None  # set to None so that no change occurs

        existing_access_search_terms = get_soap_attribute(existing_service, 'eraccesstag')
        if existing_access_search_terms is None:
            if access_search_terms != []:
                modify_required = True
            else:
                access_search_terms = None  # set to None so that no change occurs
        elif Counter(access_search_terms) != Counter(existing_access_search_terms):
            modify_required = True
        else:
            access_search_terms = None  # set to None so that no change occurs

        existing_access_additional_info = get_soap_attribute(existing_service, 'eradditionalinformation')
        if existing_access_additional_info is None:
            if access_additional_info != '':
                modify_required = True
            else:
                access_additional_info = None  # set to None so that no change occurs
        elif access_additional_info != existing_access_additional_info[0]:
            modify_required = True
        else:
            access_additional_info = None  # set to None so that no change occurs

        existing_access_badges = get_soap_attribute(existing_service, 'erbadge')

        new_badges = []
        for badge in access_badges:
            new_badges.append(str(badge['text'] + "~" + badge['colour']))

        if existing_access_badges is None:
            if new_badges != []:
                modify_required = True
            else:
                access_badges = None  # set to None so that no change occurs
        elif Counter(new_badges) != Counter(existing_access_badges):
            modify_required = True
        else:
            access_badges = None  # set to None so that no change occurs

        # A list of attribute values which have been checked already. Also includes special attributes which should
        # not be checked.
        do_not_check = [
            'description',
            'owner',
            'erprerequisite',
            'eraccessoption',
            'eraccessname',
            'eraccesscategory',
            'eraccessdescription',
            'erimageuri',
            'eraccesstag',
            'eradditionalinformation',
            'erbadge',
            'eradapterprofileversion',
            'eradapterlaststatustime',
            'erparent',
            'objectclass',
            'erlastmodifiedtime',
            'eradapteruptime',
            'erglobalid',
            'erservicename'
        ]

        # Iterate through each key in the service-specific configuration and check it against the same key in the
        # existing service.
        for key in configuration:
            existing_value = get_soap_attribute(existing_service, key)
            do_not_check.append(key.lower())  # mark the key as checked

            if existing_value is None:
                if configuration[key] != '' and configuration[key] != []:
                    modify_required = True
                else:
                    configuration[key] = None  # set to None so that no change occurs
                continue

            if type(configuration[key]) is list:
                if Counter(configuration[key]) != Counter(existing_value):
                    modify_required = True
                else:
                    configuration[key] = None  # set to None so that no change occurs
            else:
                if configuration[key] != existing_value[0]:
                    modify_required = True
                else:
                    configuration[key] = None  # set to None so that no change occurs

        # In addition to checking the service-specific attributes listed in the configuration dict, we also need to
        # check for existing service-specific attributes which weren't listed in the configuration dict. These
        # attributes are not part of the target configuration and must be explicitly set to empty values.

        existing_keys = list_soap_attribute_keys(existing_service)
        for key in existing_keys:
            if key in do_not_check:
                continue
            configuration[key] = ""  # Set to an empty string so that the attribute is explicitly cleared

        if modify_required:
            if check_mode:
                return create_return_object(changed=True)
            else:
                existing_dn = existing_service['itimDN']

                return _modify_account_service(
                    isim_application=isim_application,
                    service_dn=existing_dn,
                    description=description,
                    owner=owner_dn,
                    service_prerequisite=service_prerequisite_dn,
                    define_access=define_access,
                    access_name=access_name,
                    access_type=access_type,
                    access_description=access_description,
                    access_image_uri=access_image_uri,
                    access_search_terms=access_search_terms,
                    access_additional_info=access_additional_info,
                    access_badges=access_badges,
                    configuration=configuration
                )
        else:
            return create_return_object(changed=False)

    else:
        return create_return_object(changed=False, warnings=["More than one instance of the service '" + name + "' was "
                                                             "found in container '" + container_dn + "'. No action "
                                                             "was taken as it is unclear which service is being "
                                                             "referred to."])


def apply_identity_feed(isim_application: ISIMApplication,
                        container_path: str,
                        name: str,
                        service_type: str,
                        description: Optional[str] = None,
                        use_workflow: bool = None,
                        evaluate_sod: bool = None,
                        placement_rule: Optional[str] = None,
                        configuration: Dict = {},
                        check_mode=False,
                        force=False) -> IBMResponse:
    """
    Apply an identity feed configuration. This function will dynamically choose whether to to create or modify based
        on whether a service with the same name exists in the same container. Only attributes which differ from the
        existing service will be changed. Note that encrypted attribute values such as passwords will always be updated
        because there is no way to determine whether the new value matches the existing one. Note that the name and
        container_dn of an existing service can't be changed because they are used to identify the service. If they
        don't match an existing service, a new service will be created with the specified name and container_dn.
        The service_type of an existing service cannot be changed either. To do this you will need to delete the old
        service and create a new one.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_path: A path representing the container (business unit) that the feed exists in. The expected
        format is '//organization_name//profile::container_name//profile::container_name'. Valid values for profile
        are 'ou' (organizational unit), 'bp' (business partner unit), 'lo' (location), or 'ad' (admin domain).
    :param name: The service name.
    :param service_type: The type of feed to create. Corresponds to the erobjectprofilename attribute in LDAP.
        Valid types out-of-the-box are: 'ADFeed' (AD OrganizationalPerson identity feed), 'CSVFeed' (Comma separated
        value identity feed), 'DSML2Service' (IDI data feed), 'DSMLInfo' (DSML identity feed), or 'RFC2798Feed'
        (iNetOrgPerson identity feed).
    :param description: A description of the service.
    :param use_workflow: Set to True to use a workflow.
    :param evaluate_sod: Set to True to evaluate separation of duties policy when a workflow is used.
    :param placement_rule: The placement rule to use.
    :param configuration: A dict of key value pairs corresponding to the LDAP attributes specific to the profile
        being used to create the feed. When using the erNamingContexts attribute, you should specify containers as
        paths, not DNs. The expected format is '//organization_name//profile::container_name//profile::container_name'.
        Valid values for profile are 'ou' (organizational unit), 'bp' (business partner unit), 'lo' (location), or 'ad'
        (admin domain).
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state. This will always result in a new service
        being created, regardless of whether a service with the same name in the same container already exists. Use with
        caution.
    :return: An IBMResponse object. If the call was successful, the data field will contain the DN of the service
        that was created. If a modify request was used, the data field will be empty.
    """

    # Check that the compulsory attributes are set properly
    if not (isinstance(container_path, str) and len(container_path) > 0 and
            isinstance(name, str) and len(name) > 0 and
            isinstance(service_type, str) and len(service_type) > 0 and
            isinstance(configuration, Dict) and len(list(configuration.keys())) > 0):
        raise ValueError("Invalid service configuration. container_path, name, and service_type must have "
                         "non-empty string values. configuration must be a non-empty dictionary.")

    # If any values are set to None, they must be replaced with empty values. This is because these values will be
    # passed to methods that interpret None as 'no change', whereas we want them to be explicitly set to empty values.
    if description is None:
        description = ""

    if use_workflow is None:
        use_workflow = False

    if evaluate_sod is None:
        evaluate_sod = False

    if placement_rule is None:
        placement_rule = ""

    for key in configuration:
        if configuration[key] is None:
            configuration[key] = ""

    # convert each configuration key to lower case
    list_of_keys = list(configuration.keys())
    for key_name in list_of_keys:
        if key_name.lower() != key_name:
            configuration[key_name.lower()] = configuration[key_name]
            del configuration[key_name]

    # Convert the container path into a DN that can be passed to the SOAP API. This also validates the container path.
    dn_encoder = DNEncoder(isim_application)
    container_dn = dn_encoder.container_path_to_dn(container_path)

    # Convert the values of the erNamingContexts configuration attribute from paths into DNs
    if 'ernamingcontexts' in configuration:
        for index in range(0, len(configuration['ernamingcontexts'])):
            configuration['ernamingcontexts'][index] = dn_encoder.container_path_to_dn(configuration['ernamingcontexts'][index])

    # Search for instances with the specified name in the specified container
    search_response = search(
        isim_application=isim_application,
        container_dn=container_dn,
        ldap_filter="(erservicename=" + name + ")"
    )
    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if search_response['rc'] != 0:
        return search_response
    search_results = search_response['data']

    # Because the search function can return results with names containing the specified name, we need to confirm which
    # results have the exact name that was searched for.
    exact_matches = []
    for result in search_results:
        if result['name'] == name:
            exact_matches.append(result)

    if len(exact_matches) == 0 or force:
        # If there are no results, create a new feed and return the response
        if check_mode:
            return create_return_object(changed=True)
        else:
            return _create_identity_feed(isim_application=isim_application,
                                         container_dn=container_dn,
                                         name=name,
                                         service_type=service_type,
                                         description=description,
                                         use_workflow=use_workflow,
                                         evaluate_sod=evaluate_sod,
                                         placement_rule=placement_rule,
                                         configuration=configuration)

    elif len(exact_matches) == 1:
        # If exactly one result is found, compare it's attributes with the requested attributes and determine if a
        # modify operation is required.
        existing_service = exact_matches[0]
        modify_required = False

        existing_service_type = existing_service['profileName']

        if service_type != existing_service_type:
            return create_return_object(changed=False,
                                        warnings=["The service '" + name + "' in container '" + container_dn + "' is "
                                                  "of service type '" + existing_service_type + "'. You can't change "
                                                  "the service type to '" + service_type + "'. Create a new service "
                                                  "with a different name instead."])

        existing_description = get_soap_attribute(existing_service, 'description')
        if existing_description is None:
            if description != '':
                modify_required = True
            else:
                description = None  # set to None so that no change occurs
        elif description != existing_description[0]:
            modify_required = True
        else:
            description = None  # set to None so that no change occurs

        existing_use_workflow = get_soap_attribute(existing_service, 'eruseworkflow')
        if existing_use_workflow is None:
            modify_required = True
        elif use_workflow and existing_use_workflow[0] != 'True':
            modify_required = True
        elif not use_workflow and existing_use_workflow[0] != 'False':
            modify_required = True
        else:
            use_workflow = None  # set to None so that no change occurs

        existing_evaluate_sod = get_soap_attribute(existing_service, 'erevaluatesod')
        if existing_evaluate_sod is None:
            modify_required = True
        elif evaluate_sod and existing_evaluate_sod[0] != 'True':
            modify_required = True
        elif not evaluate_sod and existing_evaluate_sod[0] != 'False':
            modify_required = True
        else:
            evaluate_sod = None  # set to None so that no change occurs

        existing_placement_rule = get_soap_attribute(existing_service, 'erplacementrule')
        if existing_placement_rule is None:
            if placement_rule != '':
                modify_required = True
            else:
                placement_rule = None  # set to None so that no change occurs
        elif placement_rule != existing_placement_rule[0]:
            modify_required = True
        else:
            placement_rule = None  # set to None so that no change occurs

        # A list of attribute values which have been checked already. Also includes special attributes which should
        # not be checked.
        do_not_check = [
            'description',
            'eruseworkflow',
            'erevaluatesod',
            'erplacementrule',
            'eradapterprofileversion',
            'eradapterlaststatustime',
            'erparent',
            'objectclass',
            'erlastmodifiedtime',
            'eradapteruptime',
            'erglobalid',
            'erservicename'
        ]

        # Iterate through each key in the service-specific configuration and check it against the same key in the
        # existing service.
        for key in configuration:
            existing_value = get_soap_attribute(existing_service, key)
            do_not_check.append(key.lower())  # mark the key as checked

            if existing_value is None:
                if configuration[key] != '' and configuration[key] != []:
                    modify_required = True
                else:
                    configuration[key] = None  # set to None so that no change occurs
                continue

            if type(configuration[key]) is list:
                if Counter(configuration[key]) != Counter(existing_value):
                    modify_required = True
                else:
                    configuration[key] = None  # set to None so that no change occurs
            else:
                if configuration[key] != existing_value[0]:
                    modify_required = True
                else:
                    configuration[key] = None  # set to None so that no change occurs

        # In addition to checking the service-specific attributes listed in the configuration dict, we also need to
        # check for existing service-specific attributes which weren't listed in the configuration dict. These
        # attributes are not part of the target configuration and must be explicitly set to empty values.

        existing_keys = list_soap_attribute_keys(existing_service)
        for key in existing_keys:
            if key in do_not_check:
                continue
            configuration[key] = ""  # Set to an empty string so that the attribute is explicitly cleared

        if modify_required:
            if check_mode:
                return create_return_object(changed=True)
            else:
                existing_dn = existing_service['itimDN']

                return _modify_identity_feed(
                    isim_application=isim_application,
                    service_dn=existing_dn,
                    description=description,
                    use_workflow=use_workflow,
                    evaluate_sod=evaluate_sod,
                    placement_rule=placement_rule,
                    configuration=configuration
                )
        else:
            return create_return_object(changed=False)

    else:
        return create_return_object(changed=False, warnings=["More than one instance of the service '" + name + "' was "
                                                             "found in container '" + container_dn + "'. No action "
                                                             "was taken as it is unclear which service is being "
                                                             "referred to."])


def _create_account_service(isim_application: ISIMApplication,
                            container_dn: str,
                            name: str,
                            service_type: str,
                            description: str = "",
                            owner: str = "",
                            service_prerequisite: str = "",
                            define_access: bool = False,
                            access_name: str = "",
                            access_type: str = "",
                            access_description: str = "",
                            access_image_uri: str = "",
                            access_search_terms: List[str] = [],
                            access_additional_info: str = "",
                            access_badges: List[Dict[str, str]] = [],
                            configuration: Dict = {}) -> IBMResponse:
    """
    Create an account service. To set an attribute to an empty value, use an empty string or empty list. Do not use
        None as this indicates no change, which is not applicable to a create operation.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The DN of the container (business unit) to create the service under.
    :param name: The service name.
    :param service_type: The type of service to create. Corresponds to the erobjectprofilename attribute in LDAP.
        Valid types out-of-the-box are 'ADprofile', 'LdapProfile', 'PIMProfile', 'PosixAixProfile', 'PosixHpuxProfile',
        'PosixLinuxProfile', 'PosixSolarisProfile', 'WinLocalProfile', or 'HostedService'.
    :param description: A description of the service.
    :param owner: A DN corresponding to the user that owns the service.
    :param service_prerequisite: A DN corresponding to a service that is a prerequisite for this one.
    :param define_access: Set to True to define an access for the service.
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

    data = []

    # Add the container DN to the request
    data.append(str(container_dn))

    # Add the profile name to the request
    data.append(str(service_type))

    attribute_list = _build_service_attributes_list(attr_type,
                                                    name=name,
                                                    description=description,
                                                    owner=owner,
                                                    service_prerequisite=service_prerequisite,
                                                    define_access=define_access,
                                                    access_name=access_name,
                                                    access_type=access_type,
                                                    access_description=access_description,
                                                    access_image_uri=access_image_uri,
                                                    access_search_terms=access_search_terms,
                                                    access_additional_info=access_additional_info,
                                                    access_badges=access_badges,
                                                    use_workflow=None,
                                                    evaluate_sod=None,
                                                    placement_rule=None,
                                                    configuration=configuration)

    data.append(attribute_list)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Creating an account service",
                                                   soap_service,
                                                   "createService",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def _modify_account_service(isim_application: ISIMApplication,
                            service_dn: str,
                            description: Optional[str] = None,
                            owner: Optional[str] = None,
                            service_prerequisite: Optional[str] = None,
                            define_access: Optional[bool] = None,
                            access_name: Optional[str] = None,
                            access_type: Optional[str] = None,
                            access_description: Optional[str] = None,
                            access_image_uri: Optional[str] = None,
                            access_search_terms: Optional[List[str]] = None,
                            access_additional_info: Optional[str] = None,
                            access_badges: Optional[List[Dict[str, str]]] = None,
                            configuration: Optional[Dict] = None) -> IBMResponse:
    """
    Modify the attributes of an existing account service. Only arguments with a value will be changed. Any arguments
        set to None will be left as they are. This applies to the keys in the service-specific configuration dict as
        well. You must explicitly set them to empty values to remove keys.
    :param isim_application: The ISIMApplication instance to connect to.
    :param service_dn: The DN of the existing account service to modify.
    :param description: A description of the service.
    :param owner: A DN corresponding to the user that owns the service.
    :param service_prerequisite: A DN corresponding to a service that is a prerequisite for this one.
    :param define_access: Set to True to define an access for the service.
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

    # Add the service DN to the request
    data.append(service_dn)

    # Setup the list of modified attributes and add them to the request
    attribute_list = _build_service_attributes_list(attr_type,
                                                    name=None,
                                                    description=description,
                                                    owner=owner,
                                                    service_prerequisite=service_prerequisite,
                                                    define_access=define_access,
                                                    access_name=access_name,
                                                    access_type=access_type,
                                                    access_description=access_description,
                                                    access_image_uri=access_image_uri,
                                                    access_search_terms=access_search_terms,
                                                    access_additional_info=access_additional_info,
                                                    access_badges=access_badges,
                                                    use_workflow=None,
                                                    evaluate_sod=None,
                                                    placement_rule=None,
                                                    configuration=configuration)

    data.append(attribute_list)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Modifying an account service",
                                                   soap_service,
                                                   "modifyService",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def _create_identity_feed(isim_application: ISIMApplication,
                          container_dn: str,
                          name: str,
                          service_type: str,
                          description: str = "",
                          use_workflow: bool = False,
                          evaluate_sod: bool = False,
                          placement_rule: str = "",
                          configuration: Dict = {}) -> IBMResponse:
    """
    Create an identity feed. To set an attribute to an empty value, use an empty string or empty list. Do not use None
        as this indicates no change, which is not applicable to a create operation.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The DN of the container (business unit) to create the feed under.
    :param name: The service name.
    :param service_type: The type of feed to create. Corresponds to the erobjectprofilename attribute in LDAP.
        Valid types out-of-the-box are: 'ADFeed' (AD OrganizationalPerson identity feed), 'CSVFeed' (Comma separated
        value identity feed), 'DSML2Service' (IDI data feed), 'DSMLInfo' (DSML identity feed), or 'RFC2798Feed'
        (iNetOrgPerson identity feed).
    :param description: A description of the service.
    :param use_workflow: Set to True to use a workflow.
    :param evaluate_sod: Set to True to evaluate separation of duties policy when a workflow is used.
    :param placement_rule: The placement rule to use.
    :param configuration: A dict of key value pairs corresponding to the LDAP attributes specific to the profile
        being used to create the feed.
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

    data = []

    # Add the container DN to the request
    data.append(str(container_dn))

    # Add the profile name to the request
    data.append(str(service_type))

    attribute_list = _build_service_attributes_list(attr_type,
                                                    name=name,
                                                    description=description,
                                                    owner=None,
                                                    service_prerequisite=None,
                                                    define_access=None,
                                                    access_name=None,
                                                    access_type=None,
                                                    access_description=None,
                                                    access_image_uri=None,
                                                    access_search_terms=None,
                                                    access_additional_info=None,
                                                    access_badges=None,
                                                    use_workflow=use_workflow,
                                                    evaluate_sod=evaluate_sod,
                                                    placement_rule=placement_rule,
                                                    configuration=configuration)

    data.append(attribute_list)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Creating an identity feed",
                                                   soap_service,
                                                   "createService",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def _modify_identity_feed(isim_application: ISIMApplication,
                          service_dn: str,
                          description: Optional[str] = None,
                          use_workflow: Optional[bool] = None,
                          evaluate_sod: Optional[bool] = None,
                          placement_rule: Optional[str] = None,
                          configuration: Optional[Dict] = None) -> IBMResponse:
    """
    Modify the attributes of an existing identity feed. Only arguments with a value will be changed. Any arguments
        set to None will be left as they are. This applies to the keys in the service-specific configuration dict as
        well. You must explicitly set them to empty values to remove keys.
    :param isim_application: The ISIMApplication instance to connect to.
    :param service_dn: The DN of the existing account service to modify.
    :param description: A description of the service.
    :param use_workflow: Set to True to use a workflow.
    :param evaluate_sod: Set to True to evaluate separation of duties policy when a workflow is used.
    :param placement_rule: The placement rule to use.
    :param configuration: A dict of key value pairs corresponding to the LDAP attributes specific to the profile
        being used to create the feed.
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

    # Add the service DN to the request
    data.append(service_dn)

    attribute_list = _build_service_attributes_list(attr_type,
                                                    name=None,
                                                    description=description,
                                                    owner=None,
                                                    service_prerequisite=None,
                                                    define_access=None,
                                                    access_name=None,
                                                    access_type=None,
                                                    access_description=None,
                                                    access_image_uri=None,
                                                    access_search_terms=None,
                                                    access_additional_info=None,
                                                    access_badges=None,
                                                    use_workflow=use_workflow,
                                                    evaluate_sod=evaluate_sod,
                                                    placement_rule=placement_rule,
                                                    configuration=configuration)

    data.append(attribute_list)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Modifying an identity feed",
                                                   soap_service,
                                                   "modifyService",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def _build_service_attributes_list(attr_type,
                                   name: Optional[str] = None,
                                   description: Optional[str] = None,
                                   owner: Optional[str] = None,
                                   service_prerequisite: Optional[str] = None,
                                   define_access: Optional[bool] = None,
                                   access_name: Optional[str] = None,
                                   access_type: Optional[str] = None,
                                   access_description: Optional[str] = None,
                                   access_image_uri: Optional[str] = None,
                                   access_search_terms: Optional[List[str]] = None,
                                   access_additional_info: Optional[str] = None,
                                   access_badges: Optional[List[Dict[str, str]]] = None,
                                   use_workflow: Optional[bool] = None,
                                   evaluate_sod: Optional[bool] = None,
                                   placement_rule: Optional[str] = None,
                                   configuration: Optional[Dict] = None) -> List:
    """
    Build a list of attributes to be passed in a SOAP request. Used by the _create and _modify functions. Only
        arguments with a value will be set. Any arguments set to None will be left as they are. To set an attribute
        to an empty value, use an empty string or empty list. This function sets all attributes that can be passed to
        the modifyService API, regardless of whether they are for an account service or an identity feed.
    :param attr_type: The SOAP type that can be used to instantiate the an attribute object.
    :param name: The service name.
    :param description: A description of the service.
    :param owner: A DN corresponding to the user that owns the service.
    :param service_prerequisite: A DN corresponding to a service that is a prerequisite for this one.
    :param define_access: Set to True to define an access for the service.
    :param access_name: A name for the access.
    :param access_type: Set to one of 'application', 'emailgroup', 'sharedfolder' or 'role'.
    :param access_description: A description for the access.
    :param access_image_uri: The URI of an image to use for the access icon.
    :param access_search_terms: A list of search terms for the access.
    :param access_additional_info: Additional information about the acceess.
    :param access_badges: A list of dicts representing badges for the access. Each entry in the list must contain the
        keys 'text' and 'colour' with string values.
    :param use_workflow: Set to True to use a workflow.
    :param evaluate_sod: Set to True to evaluate separation of duties policy when a workflow is used.
    :param placement_rule: The placement rule to use.
    :param configuration: A dict of key value pairs corresponding to the LDAP attributes specific to the profile
        being used to create the feed.
    :return: A list of attributes formatted to be passed to the SOAP API.
    """
    attribute_list = []

    # Setup the attributes common to all services
    if name is not None:
        if name == '':
            attribute_list.append(build_attribute(attr_type, 'erservicename', []))
        else:
            attribute_list.append(build_attribute(attr_type, 'erservicename', [name]))

    if description is not None:
        if description == '':
            attribute_list.append(build_attribute(attr_type, 'description', []))
        else:
            attribute_list.append(build_attribute(attr_type, 'description', [description]))

    # Add the profile specific attributes
    if configuration is not None:
        for key in configuration:
            if configuration[key] is not None:
                if type(configuration[key]) is list:
                    attribute_list.append(build_attribute(attr_type, key, configuration[key]))
                else:
                    if configuration[key] == '':
                        attribute_list.append(build_attribute(attr_type, key, []))
                    else:
                        attribute_list.append(build_attribute(attr_type, key, [configuration[key]]))

    # Setup the attributes for an account service
    if owner is not None:
        if owner == '':
            attribute_list.append(build_attribute(attr_type, 'owner', []))
        else:
            attribute_list.append(build_attribute(attr_type, 'owner', [owner]))

    if service_prerequisite is not None:
        if service_prerequisite == '':
            attribute_list.append(build_attribute(attr_type, 'erprerequisite', []))
        else:
            attribute_list.append(build_attribute(attr_type, 'erprerequisite', [service_prerequisite]))

    if define_access is not None:
        # eraccessoption must be set to 2 to enable access, or empty to disable it
        if define_access is True:
            attribute_list.append(build_attribute(attr_type, 'eraccessoption', ["2"]))
        else:
            attribute_list.append(build_attribute(attr_type, 'eraccessoption', []))

    if access_name is not None:
        if access_name == '':
            attribute_list.append(build_attribute(attr_type, 'eraccessname', []))
        else:
            attribute_list.append(build_attribute(attr_type, 'eraccessname', [access_name]))

    if access_description is not None:
        if access_description == '':
            attribute_list.append(build_attribute(attr_type, 'eraccessdescription', []))
        else:
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

    if access_image_uri is not None:
        if access_image_uri == '':
            attribute_list.append(build_attribute(attr_type, 'erimageuri', []))
        else:
            attribute_list.append(build_attribute(attr_type, 'erimageuri', [access_image_uri]))

    if access_search_terms is not None:
        attribute_list.append(build_attribute(attr_type, 'eraccesstag', access_search_terms))

    if access_additional_info is not None:
        if access_additional_info == '':
            attribute_list.append(build_attribute(attr_type, 'eradditionalinformation', []))
        else:
            attribute_list.append(build_attribute(attr_type, 'eradditionalinformation', [access_additional_info]))

    if access_badges is not None:
        badges = []
        for badge in access_badges:
            badges.append(str(badge['text'] + "~" + badge['colour']))
        attribute_list.append(build_attribute(attr_type, 'erbadge', badges))

    # Setup the attributes for an identity feed
    if use_workflow is not None:
        attribute_list.append(build_attribute(attr_type, 'eruseworkflow', [use_workflow]))

    if evaluate_sod is not None:
        attribute_list.append(build_attribute(attr_type, 'erevaluatesod', [evaluate_sod]))

    if placement_rule is not None:
        if placement_rule == '':
            attribute_list.append(build_attribute(attr_type, 'erplacementrule', []))
        else:
            attribute_list.append(build_attribute(attr_type, 'erplacementrule', [placement_rule]))

    return attribute_list
