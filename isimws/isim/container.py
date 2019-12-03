import logging
from isimws.application.isimapplication import ISIMApplication

logger = logging.getLogger(__name__)

# service name for this module
soap_service = "WSOrganizationalContainerService"

# minimum version required by this module
requires_version = None


# get a container by it's DN
def get(isim_application: ISIMApplication, container_dn: str, check_mode=False, force=False):
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
