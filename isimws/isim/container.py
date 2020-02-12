from typing import List, Dict, Optional
import logging
from isimws.application.isimapplication import ISIMApplication, IBMResponse, create_return_object
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
    :param parent_dn: The DN of the parent container.
    :param container_name: The name of the container to search for.
    :param profile: The type of container to search for. Options are 'organization', 'admindomain', 'location',
        'businesspartnerunit', or 'organizationalunit'.
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
    if profile.lower() == "organization":
        data.append('Organization')
    elif profile.lower() == "admindomain":
        data.append('admindomain')
    elif profile.lower() == "location":
        data.append('location')
    elif profile.lower() == "businesspartnerunit":
        data.append('bporganization')
    elif profile.lower() == "organizationalunit":
        data.append('OrganizationalUnit')
    else:
        raise ValueError(profile + "is not a valid container type. Must be 'organization', 'admindomain', "
                                   "'location', 'businesspartnerunit', or 'organizationalunit'.")

    # Add the container name to the request
    data.append(container_name)

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Searching for containers",
                                                   soap_service,
                                                   "searchContainerByName",
                                                   data,
                                                   requires_version=requires_version)

    # There seems to be an issue with the Zeep library where The zeep.helpers.serialize_object() function being used by
    # the isimapplication class to serialize the SOAP response does not properly serialize all the data returned by
    # this particular call. We need to perform some post processing here to remove the unserialized data so that
    # Ansible can interpret it properly. This is a temporary workaround pending a better solution.
    for result in ret_obj['data']:
        for element in result['children']['item']:
            del element['_raw_elements']

    return ret_obj


# get a container by it's DN
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
