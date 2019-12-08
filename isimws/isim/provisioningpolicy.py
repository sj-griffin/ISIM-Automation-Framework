from typing import List, Dict, Optional
import logging
from isimws.application.isimapplication import ISIMApplication
from isimws.utilities.tools import build_attribute
import isimws

logger = logging.getLogger(__name__)

# service name for this module
soap_service = "WSProvisioningPolicyService"

# minimum version required by this module
requires_version = None


def search(isim_application: ISIMApplication, container_dn: str, policy_name: str, check_mode=False, force=False):
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


def create(isim_application: ISIMApplication,
           container_dn: str,
           name: str,
           priority: int,
           description: str = "",
           keywords: str = "",
           caption: str = "",
           available_to_subunits: bool = False,
           enabled: bool = True,
           membership_type: str = "all",
           membership_roles: List[str] = [],
           entitlements: List[Dict] = [],
           check_mode=False,
           force=False):
    """
    Create a provisioning policy.
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
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state.
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
    policy_object = policy_type()

    policy_object['description'] = description
    policy_object['name'] = name
    policy_object['keywords'] = keywords
    policy_object['caption'] = caption

    if len(entitlements) < 1:
        raise ValueError("The entitlements argument must be a list containing at least one entry.")

    entitlement_list = []

    # Iterate through the entitlements argument and add each one to the request
    for entitlement in entitlements:

        # Validate that the entitlement contains the expected keys.
        keys = list(entitlement.keys())
        if 'automatic' not in keys or \
                'ownership_type' not in keys or \
                'target_type' not in keys or \
                'workflow' not in keys:
            raise ValueError('Missing expected key in entitlement.')

        entitlement_object = policy_entitlement_type()
        service_target_object = service_target_type()

        # Set type 0 for a service type (specify the name of the service profile in the name. MAKE SURE IT IS EXACT-
        # IT IS CASE_SENSITIVE).
        # Set type 1 for a specific service (specify it's DN in the name).
        # Set type 2 for all services (specify * as the name).
        # Set type 3 for a service selection policy (specify the name of the service profile in the name. MAKE SURE IT
        # IS EXACT- IT IS CASE_SENSITIVE). The service selection policy will be automatically selected based on the
        # service profile selected.

        if entitlement['target_type'] == 'all':
            service_target_object['name'] = '*'
            service_target_object['type'] = '2'
        elif entitlement['target_type'] == 'type':
            if 'service_type' not in keys:
                raise ValueError('Missing expected key in entitlement.')
            service_target_object['name'] = entitlement['service_type']
            service_target_object['type'] = '0'
        elif entitlement['target_type'] == 'policy':
            if 'service_type' not in keys:
                raise ValueError('Missing expected key in entitlement.')
            service_target_object['name'] = entitlement['service_type']
            service_target_object['type'] = '3'
        elif entitlement['target_type'] == 'specific':
            if 'service_dn' not in keys:
                raise ValueError('Missing expected key in entitlement.')
            service_target_object['name'] = entitlement['service_dn']
            service_target_object['type'] = '1'
        else:
            raise ValueError("Invalid target_type value in entitlement. Valid values are 'all', 'type', 'policy', "
                             "or 'specific'.")

        entitlement_object['serviceTarget'] = service_target_object

        # The type value should be set to 0 for manual provisioning, or 1 for automatic provisioning
        if entitlement['automatic']:
            entitlement_object['type'] = 1
        else:
            entitlement_object['type'] = 0

        entitlement_object['processDN'] = str(entitlement['workflow'])

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

    # Set type 2 for all users in the organization. Specify '*' as the name.
    # Set type 3 to specify a specific role. Specify the role DN as the name. Create more membership objects for more
    # roles.
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
        if len(membership_roles) < 1:
            raise ValueError("The membership_roles argument must contain a list with at least one entry if "
                             "membership_type is set to 'roles'.")
        for role in membership_roles:
            membership_object = policy_membership_type()
            membership_object['name'] = str(role)
            membership_object['type'] = '3'
            membership_list.append(membership_object)
    else:
        raise ValueError("Invalid value for membership_type. Valid values are 'all', 'other', or 'roles'.")

    policy_object['membership'] = {'item': membership_list}

    if priority < 1:
        raise ValueError("Invalid priority value. Priority must be an integer greater than 0.")
    policy_object['priority'] = priority

    # Scope should be set to 1 for 'this business unit only' and 2 for 'this business unit and its subunits'
    if available_to_subunits:
        policy_object['scope'] = 2
    else:
        policy_object['scope'] = 1

    policy_object['organizationalContainer'] = container_object
    policy_object['enabled'] = enabled

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
