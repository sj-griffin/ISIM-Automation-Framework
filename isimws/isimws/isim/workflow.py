from typing import List, Dict, Optional
import logging
from isimws.application.isimapplication import ISIMApplication, IBMResponse, create_return_object

logger = logging.getLogger(__name__)

# service name for this module
# soap_service = None

# minimum version required by this module
requires_version = None


def get_attribute(isim_application: ISIMApplication,
                  workflow_dn: str,
                  attribute_name: str = "erglobalid",
                  check_mode=False,
                  force=False) -> IBMResponse:
    """
    Get an LDAP attribute value for a specific workflow. This function is provided as an alternative to a get() function
        as there is no appropriate SOAP API call.
    :param: isim_application: The ISIMApplication instance to connect to.
    :param: workflow_dn: The ITIM DN of the workflow.
    :param: attribute_name: The name of the LDAP attribute to retrieve.
    :param: check_mode: Set to True to enable check mode.
    :param: force: Set to True to force execution regardless of current state.
    :return: An IBMResponse object. If the call was successful, the data field will contain a list of values.
    """

    # Extract the organization DN and erglobalid value from the DN
    dn_components = workflow_dn.split(",ou=workflow,")
    if len(dn_components) != 2:
        raise ValueError("Invalid workflow DN")

    organization_dn = dn_components[1]

    non_org_components = dn_components[0].split("=")
    if len(non_org_components) != 2 or non_org_components[0] != "erglobalid":
        raise ValueError("Invalid workflow DN")

    erglobalid = non_org_components[1]

    # We can't search by ITIM DN, so we must use attributes to uniquely identify a workflow.
    # The value of erglobalid can be reused in different organizations, so it alone cannot uniquely identify a workflow.
    # The only other identifying information we can derive from the workflow DN is the DN of the organization it
    #   belongs to.
    # There is no guarantee that the value of erparent will match the DN of the organization. However, we do
    #   know that for a given organization, all it's workflows will contain the organization DN in the text of the value
    #   of erparent. Therefore, we can uniquely identify the workflow by searching for the erglobalid value among
    #   entries that contain the DN of the organization in the erparent value.
    search_filter = '(&(erglobalid=' + erglobalid + ')(erparent=*' + organization_dn + '))'

    return _get_attribute_by_filter(isim_application, search_filter, attribute_name)


def search_attribute(isim_application: ISIMApplication,
                     container_dn: str,
                     ldap_filter: str = "(erprocessname=*)",
                     attribute_name: str = "erglobalid",
                     check_mode=False,
                     force=False) -> IBMResponse:
    """
    Search for workflows using an LDAP filter and a container DN and return the value of a specific attribute
        for each result. This function is provided as an alternative to a search() function as there is no appropriate
        SOAP API call. Unlike other search functions, this function will only search direct children of the
        container_dn, not all its descendants.
    :param: isim_application: The ISIMApplication instance to connect to.
    :param: container_dn: The container DN of the parent container.
    :param: ldap_filter: An LDAP filter string to search for.
    :param: attribute_name: The name of the LDAP attribute to retrieve.
    :param: check_mode: Set to True to enable check mode.
    :param: force: Set to True to force execution regardless of current state.
    :return: An IBMResponse object. If the call was successful, the data field will contain a list of values.
    """
    search_filter = '(&' + ldap_filter + '(erparent=' + container_dn + '))'
    return _get_attribute_by_filter(isim_application, search_filter, attribute_name)


def _get_attribute_by_filter(isim_application: ISIMApplication,
                             search_filter: str,
                             attribute_name: str) -> IBMResponse:
    """
    Look up workflows using an LDAP filter and return a list of values for a specific LDAP attribute. Produces a list
        of attribute values with each entry corresponding to one of the workflows that was selected by the filter.
    :param: search_filter: An LDAP search filter to select workflows with.
    :param: attribute_name: The name of the LDAP attribute to retrieve.
    :return: An IBMResponse object. If the call was successful, the data field will contain a list of values.
    """

    # Get the required SOAP types for the API call
    search_arguments_type_response = isim_application.retrieve_soap_type("WSSearchDataService",
                                                                         "ns1:WSSearchArguments")

    # If an error was encountered and ignored, return the IBMResponse object so that Ansible can process it
    if search_arguments_type_response['rc'] != 0:
        return search_arguments_type_response
    search_arguments_type = search_arguments_type_response['data']

    # The session object is handled by the ISIMApplication instance

    data = []
    search_arguments_object = search_arguments_type()

    search_arguments_object['category'] = 'Workflow'
    search_arguments_object['returnedAttributeName'] = attribute_name
    search_arguments_object['filter'] = str(search_filter)
    search_arguments_object['base'] = 'global'  # 'global' or 'org'

    data.append(search_arguments_object)

    # Invoke the call
    return isim_application.invoke_soap_request("Retrieving a workflow",
                                                "WSSearchDataService",
                                                "findSearchFilterObjects",
                                                data)
