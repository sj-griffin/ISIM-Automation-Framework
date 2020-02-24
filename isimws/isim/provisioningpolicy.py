from typing import List, Dict, Optional
import logging
from isimws.application.isimapplication import ISIMApplication, IBMResponse, create_return_object
from isimws.utilities.tools import build_attribute
from isimws.utilities.dnencoder import DNEncoder

import isimws

logger = logging.getLogger(__name__)

# service name for this module
soap_service = "WSProvisioningPolicyService"

# minimum version required by this module
requires_version = None


def search(isim_application: ISIMApplication,
           container_dn: str,
           policy_name: str,
           check_mode=False,
           force=False) -> IBMResponse:
    """
    Search for a provisioning policy by it's name.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The DN of the container to search in.
    :param policy_name: The name of the provisioning policy to search for.
    :param check_mode: Set to True to enable check mode
    :param force: Set to True to force execution regardless of current state
    :return: An IBMResponse object. If the call was successful, the data field will contain a lst of the Python dict
        representations of each provisioning policy matching the criteria.
    """
    data = []
    # Add the add the container object to the request
    container_response = isimws.isim.container.get(isim_application=isim_application, container_dn=container_dn)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if container_response['rc'] != 0:
        return container_response

    container_object = container_response['data']
    data.append(container_object)

    # Add the policy name to the request
    data.append(str(policy_name))

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Searching for a provisioning policy",
                                                   soap_service,
                                                   "getPolicies",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def apply(isim_application: ISIMApplication,
          container_path: str,
          name: str,
          priority: int,
          description: Optional[str] = None,
          keywords: Optional[str] = None,
          caption: Optional[str] = None,
          available_to_subunits: Optional[bool] = None,
          enabled: Optional[bool] = None,
          membership_type: Optional[str] = None,
          membership_role_names: Optional[List[str]] = None,
          entitlements: List[Dict] = [],
          check_mode=False,
          force=False) -> IBMResponse:
    """
    Apply a provisioning policy configuration. This function will dynamically choose whether to to create or modify
        based on whether a provisioning policy with the same name exists in the same container. Unlike other apply
        methods for different types of objects, all attributes will be explicitly set regardless of whether they are
        already set or not. This is a condition imposed by the SOAP API itself. Note that the name and container_dn of
        an existing provisioning policy can't be changed because they are used to identify the provisioning policy. If
        they don't match an existing provisioning policy, a new provisioning policy will be created with the specified
        name and container_dn.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_path: A path representing the container (business unit) that the policy exists in. The expected
            format is '//organization_name//profile::container_name//profile::container_name'. Valid values for profile
            are 'ou' (organizational unit), 'bp' (business partner unit), 'lo' (location), or 'ad' (admin domain).
    :param name: The provisioning policy name.
    :param priority: An integer greater than 0 representing the priority of the policy.
    :param description: A description for the policy.
    :param keywords: A keywords string for the policy.
    :param caption: A caption for the policy.
    :param available_to_subunits: Set to True to make the policy available to services in subunits of the selected
        business unit, or False to make it available to this business unit only.
    :param enabled: Set to True to enable the policy, or False to disable it.
    :param membership_type: A string value determining how membership of the policy will be determined. Valid values
        are 'all' (for all users in the organization), 'other' (for all other users who are not granted to the
        entitlement(s) defined by this provisioning policy via other policies), or 'roles' (to specify specific roles
        using the membership_roles argument).
    :param membership_role_names: A list of names of the roles to use to determine membership. This argument will be
        ignored if membership_type is not set to 'roles'. This list cannot be empty if membership_type is set to
        'roles'.
    :param entitlements: A list of dicts representing entitlements for the policy. This list must contain at least
        one entry. Each entry is expected to contain the following keys:
            {
                automatic: bool # Set to True for automatic provisioning, or False for manual provisioning.
                ownership_type: str # Valid values are 'all', 'device', 'individual', 'system', or 'vendor'.
                target_type: str # Determines how services will be targeted. Valid values are 'all' (for all services),
                    'type' (for a service type), 'policy' (for a service selection policy), or 'specific' (for a
                    specific service).
                service_type: str # This attribute is only required if the target_type is set to 'type' or 'policy'.
                    Provide the exact name of the service profile to target. Note that it is case-sensitive.
                service_name: str # This attribute is only required if the target_type is set to 'specific'. Provide the
                    name of the service to target.
                workflow_name: str # Set to the name of a workflow to use, or None to not use a workflow.
            }
        Note: This API does not currently support adding service tags to entitlements.
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state. This will always result in a new policy
        being created, regardless of whether a policy with the same name in the same container already exists. Use with
        caution.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the action taken by the server. If a modify request was used, the data field will be empty.
    """

    # Check that the compulsory attributes are set properly
    if not (isinstance(container_path, str) and len(container_path) > 0 and
            isinstance(name, str) and len(name) > 0 and
            isinstance(priority, int) and priority > 0):
        raise ValueError("Invalid provisioning policy configuration. organization, container_dn and name must have "
                         "non-empty string values. priority must have an integer value greater than 0.")

    if len(entitlements) < 1:
        raise ValueError("The entitlements argument must be a list containing at least one entry.")

    # Validate that each entitlement contains the expected keys
    for entitlement in entitlements:
        keys = list(entitlement.keys())
        if 'automatic' not in keys or \
                'ownership_type' not in keys or \
                'target_type' not in keys or \
                'workflow_name' not in keys:
            raise ValueError('Missing expected key in entitlement.')

        if entitlement['target_type'] == 'type' or entitlement['target_type'] == 'policy':
            if 'service_type' not in keys:
                raise ValueError('Missing expected key in entitlement.')
        elif entitlement['target_type'] == 'specific':
            if 'service_name' not in keys:
                raise ValueError('Missing expected key in entitlement.')

    if membership_type == 'roles':
        if membership_role_names is None or len(membership_role_names) < 1:
            raise ValueError("The membership_role_names argument must contain a list with at least one entry if "
                             "membership_type is set to 'roles'.")

    # Unlike with other object types, None will be interpreted as an empty value rather than as 'no change' by the
    # _create and _modify methods, so we want None values to remain as None. The exception is for boolean values, which
    # we set to False by default, as None values won't be accepted by the API.
    if available_to_subunits is None:
        available_to_subunits = False

    if enabled is None:
        enabled = False

    # Convert the container path into a DN that can be passed to the SOAP API. This also validates the container path.
    dn_encoder = DNEncoder(isim_application)
    container_dn = dn_encoder.container_path_to_dn(container_path)

    # Extract the organisation name from the container path.
    organization = container_path.split('//')[1]

    # Convert the membership role names into DNs that can be passed to the SOAP API
    dn_encoder = DNEncoder(isim_application)
    membership_role_dns = []
    for membership_role_name in membership_role_names:
        membership_role_dns.append(dn_encoder.encode_to_isim_dn(organization=organization,
                                                                name=str(membership_role_name),
                                                                object_type='role'))

    # Convert the entitlement workflow and service names into DNs that can be passed to the SOAP API
    for entitlement in entitlements:
        keys = list(entitlement.keys())

        if 'workflow_name' in keys:
            if entitlement['workflow_name'] is not None:
                entitlement['workflow'] = dn_encoder.encode_to_isim_dn(organization=organization,
                                                                       name=str(entitlement['workflow_name']),
                                                                       object_type='workflow')
            else:
                entitlement['workflow'] = None
            del entitlement['workflow_name']

        if 'service_name' in keys:
            if entitlement['service_name'] is not None:
                entitlement['service_dn'] = dn_encoder.encode_to_isim_dn(organization=organization,
                                                                         name=str(entitlement['service_name']),
                                                                         object_type='service')
            else:
                entitlement['service_dn'] = None
            del entitlement['service_name']

    # Search for instances with the specified name in the specified container
    search_response = search(
        isim_application=isim_application,
        container_dn=container_dn,
        policy_name=name
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
        # If there are no results, create a new policy and return the response
        if check_mode:
            return create_return_object(changed=True)
        else:
            return _create(
                isim_application=isim_application,
                container_dn=container_dn,
                name=name,
                priority=priority,
                description=description,
                keywords=keywords,
                caption=caption,
                available_to_subunits=available_to_subunits,
                enabled=enabled,
                membership_type=membership_type,
                membership_roles=membership_role_dns,
                entitlements=entitlements
            )
    elif len(exact_matches) == 1:
        # If exactly one result is found, compare it's attributes with the requested attributes and determine if a
        # modify operation is required.
        existing_policy = exact_matches[0]
        modify_required = False

        existing_priority = existing_policy['priority']
        if existing_priority is None or priority != existing_priority:
            modify_required = True

        existing_description = existing_policy['description']
        if description != existing_description:
            modify_required = True

        existing_keywords = existing_policy['keywords']
        if keywords != existing_keywords:
            modify_required = True

        existing_caption = existing_policy['caption']
        if caption != existing_caption:
            modify_required = True

        # Scope should be set to 1 for 'this business unit only' and 2 for 'this business unit and its subunits'
        existing_scope = existing_policy['scope']
        if available_to_subunits and existing_scope != 2:
            modify_required = True
        elif not available_to_subunits and existing_scope != 1:
            modify_required = True

        existing_enabled = existing_policy['enabled']
        if enabled != existing_enabled:
            modify_required = True

        existing_memberships = existing_policy['membership']['item']
        if membership_type == 'all':
            if len(existing_memberships) != 1:
                modify_required = True

            if existing_memberships[0]['name'] != '*':
                modify_required = True

            if existing_memberships[0]['type'] != 2:
                modify_required = True
        elif membership_type == 'other':
            if len(existing_memberships) != 1:
                modify_required = True

            if existing_memberships[0]['name'] != '*':
                modify_required = True

            if existing_memberships[0]['type'] != 4:
                modify_required = True
        elif membership_type == 'roles':
            if len(existing_memberships) != len(membership_role_dns):
                modify_required = True

            # Check each role DN in the target membership list to make sure it has a match in the existing memberships
            for role_dn in membership_role_dns:
                match_found = False
                for membership in existing_memberships:
                    if membership['name'] == role_dn:
                        match_found = True
                        break

                    if membership['type'] != 3:
                        modify_required = True
                        break
                if not match_found:
                    modify_required = True

                if modify_required:
                    break
        else:
            raise ValueError("Invalid value for membership_type. Valid values are 'all', 'other', or 'roles'.")

        existing_entitlements = existing_policy['entitlements']['item']
        if len(entitlements) != len(existing_entitlements):
            modify_required = True

        # Check each entitlement in the target entitlements list to make sure it has a match in the existing
        # entitlements.
        for entitlement in entitlements:
            match_found = False
            for existing_entitlement in existing_entitlements:
                match_found = False
                automatic_match = False
                ownership_match = False
                service_target_match = False
                workflow_match = False

                # Set type 0 for a service type (specify the name of the service profile in the name. MAKE SURE IT IS EXACT-
                # IT IS CASE_SENSITIVE).
                # Set type 1 for a specific service (specify it's DN in the name).
                # Set type 2 for all services (specify * as the name).
                # Set type 3 for a service selection policy (specify the name of the service profile in the name. MAKE SURE IT
                # IS EXACT- IT IS CASE_SENSITIVE). The service selection policy will be automatically selected based on the
                # service profile selected.

                if entitlement['target_type'] == 'all':
                    if existing_entitlement['serviceTarget']['name'] == '*' and \
                            existing_entitlement['serviceTarget']['type'] == 2:
                        service_target_match = True
                elif entitlement['target_type'] == 'type':
                    if existing_entitlement['serviceTarget']['name'] == entitlement['service_type'] and \
                            existing_entitlement['serviceTarget']['type'] == 0:
                        service_target_match = True
                elif entitlement['target_type'] == 'policy':
                    if existing_entitlement['serviceTarget']['name'] == entitlement['service_type'] and \
                            existing_entitlement['serviceTarget']['type'] == 3:
                        service_target_match = True
                elif entitlement['target_type'] == 'specific':
                    if existing_entitlement['serviceTarget']['name'] == entitlement['service_dn'] and \
                            existing_entitlement['serviceTarget']['type'] == 1:
                        service_target_match = True
                else:
                    raise ValueError(
                        "Invalid target_type value in entitlement. Valid values are 'all', 'type', 'policy', "
                        "or 'specific'.")

                # The type value should be set to 0 for manual provisioning, or 1 for automatic provisioning
                if entitlement['automatic']:
                    if existing_entitlement['type'] == 1:
                        automatic_match = True
                else:
                    if existing_entitlement['type'] == 0:
                        automatic_match = True

                if existing_entitlement['processDN'] == entitlement['workflow']:
                    workflow_match = True

                if entitlement['ownership_type'].lower() == 'all':
                    if existing_entitlement['ownershipType'] == '*':
                        ownership_match = True
                elif entitlement['ownership_type'].lower() == 'device':
                    if existing_entitlement['ownershipType'] == 'Device':
                        ownership_match = True
                elif entitlement['ownership_type'].lower() == 'individual':
                    if existing_entitlement['ownershipType'] == 'Individual':
                        ownership_match = True
                elif entitlement['ownership_type'].lower() == 'system':
                    if existing_entitlement['ownershipType'] == 'System':
                        ownership_match = True
                elif entitlement['ownership_type'].lower() == 'vendor':
                    if existing_entitlement['ownershipType'] == 'Vendor':
                        ownership_match = True
                else:
                    raise ValueError(
                        "Invalid value for entitlement ownership_type. Valid values are 'all', 'device', "
                        "'individual', 'system', or 'vendor'.")

                if automatic_match and ownership_match and service_target_match and workflow_match:
                    match_found = True
                    break

            if not match_found:
                modify_required = True
                break

        if modify_required:
            if check_mode:
                return create_return_object(changed=True)
            else:
                existing_dn = existing_policy['itimDN']

                return _modify(
                    isim_application=isim_application,
                    policy_dn=existing_dn,
                    container_dn=container_dn,
                    name=name,
                    priority=priority,
                    description=description,
                    keywords=keywords,
                    caption=caption,
                    available_to_subunits=available_to_subunits,
                    enabled=enabled,
                    membership_type=membership_type,
                    membership_roles=membership_role_dns,
                    entitlements=entitlements
                )
        else:
            return create_return_object(changed=False)

    else:
        return create_return_object(changed=False,
                                    warnings=["More than one instance of the provisioning policy' " + name + "' was "
                                              "found in container '" + container_dn + "'. No action was taken as it is "
                                              "unclear which provisioning policy is being referred to."])


def _create(isim_application: ISIMApplication,
            container_dn: str,
            name: str,
            priority: int,
            description: Optional[str] = None,
            keywords: Optional[str] = None,
            caption: Optional[str] = None,
            available_to_subunits: Optional[bool] = None,
            enabled: Optional[bool] = None,
            membership_type: Optional[str] = None,
            membership_roles: Optional[List[str]] = None,
            entitlements: List[Dict] = []) -> IBMResponse:
    """
    Create a provisioning policy. Due to differences in the SOAP API, this function works differently to the _create
        functions for other types of objects. Ordinarily None would indicate no change, but here it applies an empty
        value. Setting an empty string or list will set the value to a literal empty string or list, which may cause
        problems.
    :param isim_application: The ISIMApplication instance to connect to.
    :param container_dn: The DN of the container (business unit) to create the provisioning policy under.
    :param name: The name of the policy.
    :param priority: An integer greater than 0 representing the priority of the policy.
    :param description: A description for the policy.
    :param keywords: A keywords string for the policy.
    :param caption: A caption for the policy.
    :param available_to_subunits: Set to True to make the policy available to services in subunits of the selected
        business unit, or False to make it available to this business unit only.
    :param enabled: Set to True to enable the policy, or False to disable it.
    :param membership_type: A string value determining how membership of the policy will be determined. Valid values
        are 'all' (for all users in the organization), 'other' (for all other users who are not granted to the
        entitlement(s) defined by this provisioning policy via other policies), or 'roles' (to specify specific roles
        using the membership_roles argument).
    :param membership_roles: A list of DNs of the roles to use to determine membership. This argument will be
        ignored if membership_type is not set to 'roles'. This list cannot be empty if membership_type is set to
        'roles'.
    :param entitlements: A list of dicts representing entitlements for the policy. This list must contain at least
        one entry. Each entry is expected to contain the following keys:
            {
                automatic: bool # Set to True for automatic provisioning, or False for manual provisioning.
                ownership_type: str # Valid values are 'all', 'device', 'individual', 'system', or 'vendor'.
                target_type: str # Determines how services will be targeted. Valid values are 'all' (for all services),
                    'type' (for a service type), 'policy' (for a service selection policy), or 'specific' (for a
                    specific service).
                service_type: str # This attribute is only required if the target_type is set to 'type' or 'policy'.
                    Provide the exact name of the service profile to target. Note that it is case-sensitive.
                service_dn: str # This attribute is only required if the target_type is set to 'specific'. Provide the
                    DN of the service to target.
                workflow: str # Set to the DN of a workflow to use, or None to not use a workflow.
            }
        Note: This API does not currently support adding service tags to entitlements.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the action taken by the server.
    """
    data = []

    # Get the required SOAP types

    # Get the policy type
    policy_type_response = isim_application.retrieve_soap_type(soap_service,
                                                               "ns1:WSProvisioningPolicy",
                                                               requires_version=requires_version)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if policy_type_response['rc'] != 0:
        return policy_type_response
    policy_type = policy_type_response['data']

    # Get the policy membership type
    policy_membership_type_response = isim_application.retrieve_soap_type(soap_service,
                                                                          "ns1:WSProvisioningPolicyMembership",
                                                                          requires_version=requires_version)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if policy_membership_type_response['rc'] != 0:
        return policy_membership_type_response
    policy_membership_type = policy_membership_type_response['data']

    # Get the policy entitlement type
    policy_entitlement_type_response = isim_application.retrieve_soap_type(soap_service,
                                                                           "ns1:WSProvisioningPolicyEntitlement",
                                                                           requires_version=requires_version)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if policy_entitlement_type_response['rc'] != 0:
        return policy_entitlement_type_response
    policy_entitlement_type = policy_entitlement_type_response['data']

    # Get the service target type
    service_target_type_response = isim_application.retrieve_soap_type(soap_service,
                                                                       "ns1:WSServiceTarget",
                                                                       requires_version=requires_version)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if service_target_type_response['rc'] != 0:
        return service_target_type_response
    service_target_type = service_target_type_response['data']

    # Retrieve the container object (the business unit)
    container_response = isimws.isim.container.get(isim_application=isim_application, container_dn=container_dn)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if container_response['rc'] != 0:
        return container_response

    container_object = container_response['data']
    data.append(container_object)

    # Setup the policy object
    policy_object = _setup_policy_object(
        policy_type=policy_type,
        policy_entitlement_type=policy_entitlement_type,
        service_target_type=service_target_type,
        policy_membership_type=policy_membership_type,
        container_object=container_object,
        name=name,
        priority=priority,
        description=description,
        keywords=keywords,
        caption=caption,
        available_to_subunits=available_to_subunits,
        enabled=enabled,
        membership_type=membership_type,
        membership_roles=membership_roles,
        entitlements=entitlements
    )

    data.append(policy_object)

    # Leave the date object empty
    data.append(None)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Creating a provisioning policy",
                                                   soap_service,
                                                   "createPolicy",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def _modify(isim_application: ISIMApplication,
            policy_dn: str,
            container_dn: str,
            name: str,
            priority: int,
            description: Optional[str] = None,
            keywords: Optional[str] = None,
            caption: Optional[str] = None,
            available_to_subunits: Optional[bool] = None,
            enabled: Optional[bool] = None,
            membership_type: Optional[str] = None,
            membership_roles: Optional[List[str]] = None,
            entitlements: List[Dict] = []) -> IBMResponse:
    """
    Modify an existing provisioning policy. Due to differences in the SOAP API, this function works differently to the
        _modify functions for other types of objects. Ordinarily None would indicate no change, but here it applies an
        empty value. Setting an empty string or list will set the value to a literal empty string or list, which may
        cause problems. There is no concept of 'no change' with this API- all attributes must be set regardless of
        whether they already have a value.
    :param isim_application: The ISIMApplication instance to connect to.
    :param policy_dn: The DN of the existing policy to modify.
    :param container_dn: The DN of the container (business unit) that the policy exists in.
    :param name: The name of the policy.
    :param priority: An integer greater than 0 representing the priority of the policy.
    :param description: A description for the policy.
    :param keywords: A keywords string for the policy.
    :param caption: A caption for the policy.
    :param available_to_subunits: Set to True to make the policy available to services in subunits of the selected
        business unit, or False to make it available to this business unit only.
    :param enabled: Set to True to enable the policy, or False to disable it.
    :param membership_type: A string value determining how membership of the policy will be determined. Valid values
        are 'all' (for all users in the organization), 'other' (for all other users who are not granted to the
        entitlement(s) defined by this provisioning policy via other policies), or 'roles' (to specify specific roles
        using the membership_roles argument).
    :param membership_roles: A list of DNs of the roles to use to determine membership. This argument will be
        ignored if membership_type is not set to 'roles'. This list cannot be empty if membership_type is set to
        'roles'.
    :param entitlements: A list of dicts representing entitlements for the policy. This list must contain at least
        one entry. Each entry is expected to contain the following keys:
            {
                automatic: bool # Set to True for automatic provisioning, or False for manual provisioning.
                ownership_type: str # Valid values are 'all', 'device', 'individual', 'system', or 'vendor'.
                target_type: str # Determines how services will be targeted. Valid values are 'all' (for all services),
                    'type' (for a service type), 'policy' (for a service selection policy), or 'specific' (for a
                    specific service).
                service_type: str # This attribute is only required if the target_type is set to 'type' or 'policy'.
                    Provide the exact name of the service profile to target. Note that it is case-sensitive.
                service_dn: str # This attribute is only required if the target_type is set to 'specific'. Provide the
                    DN of the service to target.
                workflow: str # Set to the DN of a workflow to use, or None to not use a workflow.
            }
        Note: This API does not currently support adding service tags to entitlements.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the action taken by the server.
    """
    data = []

    # Get the required SOAP types

    # Get the policy type
    policy_type_response = isim_application.retrieve_soap_type(soap_service,
                                                               "ns1:WSProvisioningPolicy",
                                                               requires_version=requires_version)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if policy_type_response['rc'] != 0:
        return policy_type_response
    policy_type = policy_type_response['data']

    # Get the policy membership type
    policy_membership_type_response = isim_application.retrieve_soap_type(soap_service,
                                                                          "ns1:WSProvisioningPolicyMembership",
                                                                          requires_version=requires_version)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if policy_membership_type_response['rc'] != 0:
        return policy_membership_type_response
    policy_membership_type = policy_membership_type_response['data']

    # Get the policy entitlement type
    policy_entitlement_type_response = isim_application.retrieve_soap_type(soap_service,
                                                                           "ns1:WSProvisioningPolicyEntitlement",
                                                                           requires_version=requires_version)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if policy_entitlement_type_response['rc'] != 0:
        return policy_entitlement_type_response
    policy_entitlement_type = policy_entitlement_type_response['data']

    # Get the service target type
    service_target_type_response = isim_application.retrieve_soap_type(soap_service,
                                                                       "ns1:WSServiceTarget",
                                                                       requires_version=requires_version)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if service_target_type_response['rc'] != 0:
        return service_target_type_response
    service_target_type = service_target_type_response['data']

    # Retrieve the container object (the business unit)
    container_response = isimws.isim.container.get(isim_application=isim_application, container_dn=container_dn)

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if container_response['rc'] != 0:
        return container_response

    container_object = container_response['data']
    data.append(container_object)

    # Setup the policy object
    policy_object = _setup_policy_object(
        policy_type=policy_type,
        policy_entitlement_type=policy_entitlement_type,
        service_target_type=service_target_type,
        policy_membership_type=policy_membership_type,
        container_object=container_object,
        name=name,
        priority=priority,
        description=description,
        keywords=keywords,
        caption=caption,
        available_to_subunits=available_to_subunits,
        enabled=enabled,
        membership_type=membership_type,
        membership_roles=membership_roles,
        entitlements=entitlements
    )

    policy_object['itimDN'] = policy_dn  # Add the policy DN so that the existing policy can be identified

    data.append(policy_object)

    # Leave the date object empty
    data.append(None)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Modifying a provisioning policy",
                                                   soap_service,
                                                   "modifyPolicy",
                                                   data,
                                                   requires_version=requires_version)
    return ret_obj


def _setup_policy_object(policy_type,
                         policy_entitlement_type,
                         service_target_type,
                         policy_membership_type,
                         container_object,
                         name: str,
                         priority: int,
                         description: Optional[str] = None,
                         keywords: Optional[str] = None,
                         caption: Optional[str] = None,
                         available_to_subunits: Optional[bool] = None,
                         enabled: Optional[bool] = None,
                         membership_type: Optional[str] = None,
                         membership_roles: Optional[List[str]] = None,
                         entitlements: List[Dict] = []):
    """
    Setup the policy object used in the create and modify SOAP requests.
    :param policy_type: The SOAP type that can be used to instantiate a policy object.
    :param policy_entitlement_type: The SOAP type that can be used to instantiate a policy entitlement object.
    :param service_target_type: The SOAP type that can be used to instantiate a service target object.
    :param policy_membership_type: The SOAP type that can be used to instantiate a policy membership type object.
    :param container_object: The SOAP container object to be included in the request.
    :param name: The name of the policy.
    :param priority: An integer greater than 0 representing the priority of the policy.
    :param description: A description for the policy.
    :param keywords: A keywords string for the policy.
    :param caption: A caption for the policy.
    :param available_to_subunits: Set to True to make the policy available to services in subunits of the selected
        business unit, or False to make it available to this business unit only.
    :param enabled: Set to True to enable the policy, or False to disable it.
    :param membership_type: A string value determining how membership of the policy will be determined. Valid values
        are 'all' (for all users in the organization), 'other' (for all other users who are not granted to the
        entitlement(s) defined by this provisioning policy via other policies), or 'roles' (to specify specific roles
        using the membership_roles argument).
    :param membership_roles: A list of DNs of the roles to use to determine membership. This argument will be
        ignored if membership_type is not set to 'roles'. This list cannot be empty if membership_type is set to
        'roles'.
    :param entitlements: A list of dicts representing entitlements for the policy. This list must contain at least
        one entry. Each entry is expected to contain the following keys:
            {
                automatic: bool # Set to True for automatic provisioning, or False for manual provisioning.
                ownership_type: str # Valid values are 'all', 'device', 'individual', 'system', or 'vendor'.
                target_type: str # Determines how services will be targeted. Valid values are 'all' (for all services),
                    'type' (for a service type), 'policy' (for a service selection policy), or 'specific' (for a
                    specific service).
                service_type: str # This attribute is only required if the target_type is set to 'type' or 'policy'.
                    Provide the exact name of the service profile to target. Note that it is case-sensitive.
                service_dn: str # This attribute is only required if the target_type is set to 'specific'. Provide the
                    DN of the service to target.
                workflow: str # Set to the DN of a workflow to use, or None to not use a workflow.
            }
        Note: This API does not currently support adding service tags to entitlements.
    :return:
    """

    policy_object = policy_type()

    if description is not None:
        policy_object['description'] = description
    policy_object['name'] = name

    if keywords is not None:
        policy_object['keywords'] = keywords

    if caption is not None:
        policy_object['caption'] = caption

    entitlement_list = []

    # Iterate through the entitlements argument and add each one to the request
    for entitlement in entitlements:
        keys = list(entitlement.keys())

        entitlement_object = policy_entitlement_type()
        service_target_object = service_target_type()

        # Set type 0 for a service type (specify the name of the service profile in the name. MAKE SURE IT IS EXACT-
        # IT IS CASE_SENSITIVE).
        # Set type 1 for a specific service (specify it's DN in the name).
        # Set type 2 for all services (specify * as the name).
        # Set type 3 for a service selection policy (specify the name of the service profile in the name. MAKE SURE IT
        # IS EXACT- IT IS CASE_SENSITIVE). The service selection policy will be automatically selected based on the
        # service profile selected.

        if entitlement['target_type'] is not None:
            if entitlement['target_type'] == 'all':
                service_target_object['name'] = '*'
                service_target_object['type'] = '2'
            elif entitlement['target_type'] == 'type':
                service_target_object['name'] = entitlement['service_type']
                service_target_object['type'] = '0'
            elif entitlement['target_type'] == 'policy':
                service_target_object['name'] = entitlement['service_type']
                service_target_object['type'] = '3'
            elif entitlement['target_type'] == 'specific':
                service_target_object['name'] = entitlement['service_dn']
                service_target_object['type'] = '1'
            else:
                raise ValueError("Invalid target_type value in entitlement. Valid values are 'all', 'type', 'policy', "
                                 "or 'specific'.")

        entitlement_object['serviceTarget'] = service_target_object

        if entitlement['automatic'] is not None:
            # The type value should be set to 0 for manual provisioning, or 1 for automatic provisioning
            if entitlement['automatic']:
                entitlement_object['type'] = 1
            else:
                entitlement_object['type'] = 0

        if entitlement['workflow'] is not None:
            entitlement_object['processDN'] = str(entitlement['workflow'])

        if entitlement['ownership_type'] is not None:
            if entitlement['ownership_type'].lower() == 'all':
                entitlement_object['ownershipType'] = '*'
            elif entitlement['ownership_type'].lower() == 'device':
                entitlement_object['ownershipType'] = 'Device'
            elif entitlement['ownership_type'].lower() == 'individual':
                entitlement_object['ownershipType'] = 'Individual'
            elif entitlement['ownership_type'].lower() == 'system':
                entitlement_object['ownershipType'] = 'System'
            elif entitlement['ownership_type'].lower() == 'vendor':
                entitlement_object['ownershipType'] = 'Vendor'
            else:
                raise ValueError("Invalid value for entitlement ownership_type. Valid values are 'all', 'device', "
                                 "'individual', 'system', or 'vendor'.")

        entitlement_list.append(entitlement_object)

    policy_object['entitlements'] = {'item': entitlement_list}

    # Add membership information to the request
    membership_list = []
    membership_object = policy_membership_type()

    if membership_type is not None:
        # Set type 2 for all users in the organization. Specify '*' as the name.
        # Set type 3 to specify a specific role. Specify the role DN as the name. Create more membership objects for
        # more roles.
        # Set type 4 for all other users who are not granted to the entitlement(s) defined by this provisioning policy
        # via other policies. Specify '*' as the name.
        if membership_type == 'all':
            membership_object['name'] = '*'
            membership_object['type'] = '2'
            membership_list.append(membership_object)
        elif membership_type == 'other':
            membership_object['name'] = '*'
            membership_object['type'] = '4'
            membership_list.append(membership_object)
        elif membership_type == 'roles':
            for role in membership_roles:
                membership_object = policy_membership_type()
                membership_object['name'] = str(role)
                membership_object['type'] = '3'
                membership_list.append(membership_object)
        else:
            raise ValueError("Invalid value for membership_type. Valid values are 'all', 'other', or 'roles'.")

    policy_object['membership'] = {'item': membership_list}

    if priority is not None:
        if priority < 1:
            raise ValueError("Invalid priority value. Priority must be an integer greater than 0.")
        policy_object['priority'] = priority

    if available_to_subunits is not None:
        # Scope should be set to 1 for 'this business unit only' and 2 for 'this business unit and its subunits'
        if available_to_subunits:
            policy_object['scope'] = 2
        else:
            policy_object['scope'] = 1

    if container_object is not None:
        policy_object['organizationalContainer'] = container_object

    if enabled is not None:
        policy_object['enabled'] = enabled

    return policy_object
