from typing import List, Dict, Optional
import logging
from isimws.application.isimapplication import ISIMApplication, IBMResponse, create_return_object
import isimws
from isimws.utilities.tools import strip_zeep_element_data

logger = logging.getLogger(__name__)

# service name for this module
soap_service = "WSOrganizationalContainerService"

# minimum version required by this module
requires_version = None


def get_all(isim_application: ISIMApplication, check_mode=False, force=False) -> IBMResponse:
    """
    Get a list of all organizations in the system.
    :param isim_application: The ISIMApplication instance to connect to.
    :param check_mode: Set to True to enable check mode.
    :param force: Set to True to force execution regardless of current state.
    :return: An IBMResponse object. If the call was successful, the data field will contain the Python dict
        representation of the role.
    """
    # The session object is handled by the ISIMApplication instance
    data = []

    # Invoke the call
    ret_obj = isim_application.invoke_soap_request("Retrieving organizations list",
                                                   soap_service,
                                                   "getOrganizationTree",
                                                   data,
                                                   requires_version=requires_version)

    ret_obj = strip_zeep_element_data(ret_obj)

    return ret_obj
