from typing import List, Dict, Optional
import requests
import logging
import re
from requests import Session
from requests.packages.urllib3.exceptions import InsecureRequestWarning
# from lxml import etree

import zeep
from zeep import Client, Settings, Plugin
from zeep.transports import Transport
from zeep.exceptions import Fault
from zeep.helpers import serialize_object

from isimws.user.isimapplicationuser import ISIMApplicationUser


# Zeep plugin used to extract the XML payload for use in debugging
class ZeepLoggingPlugin(Plugin):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        super().__init__()

    def ingress(self, envelope, http_headers, operation):
        # print(etree.tostring(envelope))
        # self.logger.debug(etree.tostring(envelope))
        return envelope, http_headers

    def egress(self, envelope, http_headers, operation, binding_options):
        # print(etree.tostring(envelope))
        # self.logger.debug(etree.tostring(envelope))
        return envelope, http_headers


class IBMError(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class IBMFatal(Exception):
    def __init__(self, *args, **kwargs):
        Exception.__init__(self, *args, **kwargs)


class IBMResponse(dict):
    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def succeeded_with_data(self):
        """
        Determines whether the execution succeeded with data retrieved.
        :return: True if the execution succeeded and the data is retrieved.
        """
        if self.get('fault', True) is False and self.get("data"):
            return True
        return False

    def succeeded(self):
        """
        Determines whether the execution succeeded.
        :return: True if succeeded.
        """
        if self.get('fault', True) is False:
            return True
        return False

    def failed(self):
        """
        Determines whether the execution failed.
        :return: True if the execution failed.
        """
        if self.get('fault', True) is False:
            return False
        return True


def create_return_object(rc=0, data=None, warnings=[], changed=False):
    """
    Create a response object with the given properties.
    :param rc: The return code of the call. Should be set to 0 on success, or a meaningful error code on failure.
    :param data: the data object of the response. Often in Json.
    :param warnings: The warnings of the executed call.
    :param changed: Whether there was any change.
    :return: The IBMResponse object.
    """
    return IBMResponse({'rc': rc,
                        'data': data,
                        'changed': changed,
                        'warnings': warnings
                        })


def version_compare(version1, version2):
    """
    Compare two ISIM version strings. Please note that the versions should be all numeric separated by dots.

    Returns following values:
         0 - if version strings are equivalent
        >0 - if version1 is greater than version2
        <0 - if version1 is less than version2

    Test cases to run for verifying this code:
        assert version_compare("1", "1") == 0
        assert version_compare("2.1", "2.2") < 0
        assert version_compare("3.0.4.10", "3.0.4.2") > 0
        assert version_compare("4.08", "4.08.01") < 0
        assert version_compare("3.2.1.9.8144", "3.2") > 0
        assert version_compare("3.2", "3.2.1.9.8144") < 0
        assert version_compare("1.2", "2.1") < 0
        assert version_compare("2.1", "1.2") > 0
        assert version_compare("5.6.7", "5.6.7") == 0
        assert version_compare("1.01.1", "1.1.1") == 0
        assert version_compare("1.1.1", "1.01.1") == 0
        assert version_compare("1", "1.0") == 0
        assert version_compare("1.0", "1") == 0
        assert version_compare("1.0", "1.0.1") < 0
        assert version_compare("1.0.1", "1.0") > 0
        assert version_compare("1.0.2.0", "1.0.2") == 0
        assert version_compare("10.0", "9.0.3") > 0

    :param version1:
    :param version2:
    :return:
    """

    def normalize(v):
        v = re.sub(r'_b\d+$', '', v)
        return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]

    if normalize(version1) == normalize(version2):
        return 0
    elif normalize(version1) > normalize(version2):
        return 1
    elif normalize(version1) < normalize(version2):
        return -1

class ISIMApplication:
    host: str
    port: int
    user: ISIMApplicationUser
    clients: Dict
    soap_session: object
    version: str

    def __init__(self, hostname: str, user: ISIMApplicationUser, port: int = 9082):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating an ISIMApplication')
        if isinstance(port, str):
            self.port = int(port)
        else:
            self.port = port
        self.host = hostname
        self.user = user

        # Disable SSL validation
        session = Session()
        session.verify = False
        transport = Transport(session=session)

        settings = Settings(strict=False)
        base_url = "https://" + self.host + ":" + str(self.port) + "/itim/services/"

        session_response = None

        self._suppress_ssl_warning()  # suppress SSL warnings

        try:
            # Create client objects for each SOAP service
            self.clients: Dict[str, Client] = {
                "WSSessionService": Client(base_url + "WSSessionService?WSDL",
                                           transport=transport, settings=settings, plugins=[ZeepLoggingPlugin()]),
                "WSOrganizationalContainerService": Client(base_url + "WSOrganizationalContainerServiceService?WSDL",
                                                           transport=transport, settings=settings,
                                                           plugins=[ZeepLoggingPlugin()]),
                "WSPersonService": Client(base_url + "WSPersonServiceService?WSDL",
                                          transport=transport, settings=settings, plugins=[ZeepLoggingPlugin()]),
                "WSRoleService": Client(base_url + "WSRoleServiceService?WSDL",
                                        transport=transport, settings=settings, plugins=[ZeepLoggingPlugin()]),
                "WSServiceService": Client(base_url + "WSServiceServiceService?WSDL",
                                           transport=transport, settings=settings, plugins=[ZeepLoggingPlugin()]),
                "WSProvisioningPolicyService": Client(base_url + "WSProvisioningPolicyServiceService?WSDL",
                                                      transport=transport, settings=settings,
                                                      plugins=[ZeepLoggingPlugin()]),
                "WSPasswordService": Client(base_url + "WSPasswordServiceService?WSDL",
                                            transport=transport, settings=settings, plugins=[ZeepLoggingPlugin()]),
                "WSRequestService": Client(base_url + "WSRequestServiceService?WSDL",
                                           transport=transport, settings=settings, plugins=[ZeepLoggingPlugin()]),
                "WSSystemUserService": Client(base_url + "WSSystemUserServiceService?WSDL",
                                              transport=transport, settings=settings, plugins=[ZeepLoggingPlugin()]),
                "WSGroupService": Client(base_url + "WSGroupServiceService?WSDL",
                                         transport=transport, settings=settings, plugins=[ZeepLoggingPlugin()])
            }

            # Establish a session
            session_response = self.clients["WSSessionService"].service.login(user.username, user.password)

        # handle any connection errors
        except requests.exceptions.ConnectionError:
            self.logger.error("Can't connect to server.")
            raise IBMFatal("Can't connect to server.")

        if session_response is None:
            self.logger.error("Can't establish session with SOAP API. Invalid credentials.")
            raise IBMFatal("Can't establish session with SOAP API. Invalid credentials.")

        self.soap_session = session_response

        # Retrieve version info
        version_info = self.clients["WSSessionService"].service.getItimVersionInfo()
        self.version = version_info["version"] + "." + version_info["fixPackLevel"]

    def retrieve_soap_type(self, service: str, type_name: str, requires_version=None, warnings=[], ignore_error=False):
        """
        Get the SOAP type of the specified name from the specified service. This function returns a response object
        so that the calling function can process it the same way as other calls to this class, even though it does
        not actually make any SOAP calls. It still checks the version requirement and takes into account
        whether errors should be ignored.
        :param service: The name of the SOAP web service to use.
        :param type_name: The name of the SOAP type to retrieve, including the namespace (e.g. 'ns1:WSPerson').
        :param requires_version: The version required by the call.
        :param warnings: The current list of warnings for the call.
        :param ignore_error: Set to True if errors should be ignored.
        :return: An IBMResponse object with the SOAP type in the data attribute.
        """

        # Log the description
        self._log_description("Retrieving the SOAP type '" + type_name + "' from the " + service + " service.")

        # Update the list of warnings
        warnings = self._process_warnings(warnings=warnings)
        return_obj = create_return_object(warnings=warnings)

        # Check the minimum version requirement is met
        self._check_version(return_obj, requires_version, ignore_error=ignore_error)
        if return_obj['rc'] == 1:
            return return_obj

        # Attempt to retrieve the required type
        type_result = None
        try:
            type_result = self.clients[service].get_type(type_name)
        except (zeep.exceptions.LookupError, zeep.exceptions.NamespaceError, ValueError):
            error_message = type_name + " is  not a valid namespace and type for the " + service + " service."
            if not ignore_error:
                self.logger.error(error_message)
                raise IBMError(error_message)
            else:
                self.logger.debug(error_message)
                return_obj['rc'] = 1
                return return_obj

        return_obj['data'] = type_result
        return_obj['rc'] = 0
        return_obj['changed'] = False
        return return_obj

    def invoke_soap_request(self,
                            description: str,
                            service: str,
                            operation: str,
                            data: List,
                            requires_version=None,
                            warnings=[],
                            ignore_error=False):
        """
        Make a SOAP call to the application and perform all associated functions (logging, assessing any warnings,
        adding metadata to the response object, and handling connection errors)
        :param description: A description of the call.
        :param service: The name of the SOAP web service to use.
        :param operation: The name of the SOAP operation to call.
        :param data: An ordered list of objects to send as data. A session object should not be included as it will be handled automatically.
        :param requires_version: The version required by the call.
        :param warnings: The current list of warnings for the call.
        :param ignore_error: Set to True if errors should be ignored.
        :return: An IBMResponse object containing the following fields: {'rc', 'data', 'changed', 'warnings'}.
        """

        # Log the request
        self._log_request(service, operation, description)

        # Log the description
        self._log_description(description)

        # Update the list of warnings
        warnings = self._process_warnings(warnings=warnings)
        return_obj = create_return_object(warnings=warnings)

        # Check the minimum version requirement is met
        self._check_version(return_obj, requires_version, ignore_error=ignore_error)
        if return_obj['rc'] == 1:
            return return_obj

        self._suppress_ssl_warning()  # suppress SSL warnings

        soap_data = None
        soap_fault = None

        # Make the call to the soap service and get the response
        try:
            # Get a reference to the function to call. See https://stackoverflow.com/a/3071 for an explanation.
            function_pointer = getattr(self.clients[service].service, operation)
            soap_data = function_pointer(self.soap_session, *data)  # soap_data is an arbitrary Python data structure

        # handle any connection errors
        except requests.exceptions.ConnectionError:
            self._process_connection_error(ignore_error=ignore_error, return_obj=return_obj)

        # Record any SOAP fault that occurred during the call.
        except zeep.exceptions.Fault as fault:
            soap_fault = {'code': fault.code, 'message': fault.message, 'detail': {}}
            detail_keys = fault.detail.keys()
            for key in detail_keys:
                soap_fault['detail'][key] = self.clients[service].wsdl.types.deserialize(fault.detail[key])

        # Record whether the call resulted in a change
        # Anything other than methods with these prefixes should result in a change
        if not operation.lower().startswith(("get", "is", "login", "logout", "search", "lookup", "test", "find")):
            return_obj['changed'] = True

        # Process the response or fault
        self._process_response(return_obj, soap_data, soap_fault, ignore_error=ignore_error)

        # log the response
        self._log_response(return_obj)

        return return_obj

    def _suppress_ssl_warning(self):
        # Disable https warning because of non-standard certs on appliance
        try:
            self.logger.debug("Suppressing SSL Warnings.")
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        except AttributeError:
            self.logger.warning("load requests.packages.urllib3.disable_warnings() failed")

    # log a request
    def _log_request(self, service, method, description):
        self.logger.debug("Request: %s.%s Description: %s", service, method, description)

    # log the description of a task
    def _log_description(self, description):
        if description != "":
            self.logger.info('*** ' + description + ' ***')

    def _process_warnings(self, warnings: List = []):
        """
        Update the list of warnings for a request before a call to the SOAP API is made. At this stage this method is
        just a placeholder for any future warning conditions that may need ot be addressed.
        :param warnings: The current list of warnings for the call.
        :return: The updated list of warnings.
        """
        self.logger.debug("Warnings: {0}".format(warnings))
        return warnings

    def _check_version(self, return_obj, requires_version, ignore_error=False):
        """
        Check if the application meets a required minimum version for a request and handle the case where it doesn't.
        :param return_obj: The IBMResponse object to update.
        :param requires_version: The minimum version required.
        :param ignore_error: A flag which is set to True if errors should be ignored.
        :return: A flag that is True if the application version is sufficient or can't be determined.
        """
        self.logger.debug("Checking for minimum version: {0}.".format(requires_version))
        if not self._is_version_supported(requires_version):
            error_message = "API invoked requires minimum version: {0}, application is of lower version: {1}.".format(
                requires_version, self.version)
            if not ignore_error:
                self.logger.error(error_message)
                raise IBMError(error_message)
            else:
                self.logger.debug(error_message)
                return_obj['rc'] = 1
                return return_obj

    def _is_version_supported(self, requires_version):
        """
        Check if the application meets a required minimum version for a request.
        :param requires_version: The minimum version required.
        :return: A flag that is True if the application version is sufficient or can't be determined.
        """
        if requires_version is not None and self.version is not None:
            if version_compare(self.version, requires_version) < 0:
                return False
        return True

    def _process_connection_error(self, ignore_error, return_obj):
        """
        Handle a connection failure.
        :param ignore_error: A flag which is set to True if errors should be ignored.
        :param return_obj: An IBMResponse object to update.
        """
        if not ignore_error:
            self.logger.critical("Failed to connect to server.")
            raise IBMError("HTTP Return code: 502", "Failed to connect to server")
        else:
            self.logger.debug("Failed to connect to server.")
            return_obj['rc'] = 502  # setting the response code will prevent any further processing of the response

    def _process_response(self, return_obj, zeep_response, soap_fault, ignore_error):
        """
        Common soap_fault objects:
        Bad attribute values in an object, like an invalid session ID:
        {
          'code': 'axis2ns1:Server',
          'message': 'Internal Error',
          'detail': {}
        }

        Unauthorized actions produce the following fault. This applies if you can't perform that operation or you don't have access to the object you are trying to perform it on.         Note that it is also possible to not have the right authorization to see certain objects, like when searching for a container. In these cases, no error will be thrown, they just won't appear in results.:
        {
          'code': 'soapenv:Server',
          'message': 'com.ibm.itim.apps.exception.AppProcessingException: CTGIMS009E You do not have the authority to perform this operation.',
          'detail': {}
        }

        Accessing an object that doesn't exist:
        {
         'code': 'soapenv:Server',
         'message': 'com.ibm.itim.apps.ApplicationException: CTGIMF007E  The specified object cannot be found in the directory server. The object might have been moved or deleted before your request completed.\n\nThe following information was returned from the directory server:\nThe erglobalid=00000000000000000001,ou=roles,erglobalid=00000000000000000000,ou=pps,dc=com object cannot be found. The following error occurred.\nError: [LDAP: error code 32 - No Such Object].',
         'detail': {}
        }

        Missing attributes of an object when creating:
        {
         'code': 'soapenv:Server',
         'message': 'com.ibm.itim.apps.SchemaViolationException: CTGIMS001E At least one required attribute is missing.',
         'detail': {}
        }

        Can't connect to LDAP server, or trying to use an invlaid DN:
        {
         'code': 'soapenv:Server',
         'message': 'com.ibm.itim.apps.ApplicationException: CTGIMF002E A session with the directory server cannot be established.',
         'detail': {}
        }
        """

        # Do not perform further processing if the response code has already been set by a previous process
        if return_obj['rc'] != 0:
            return

        # We use SOAP faults rather than HTTP response codes to determine whether the call was successful or not and
        # infer the status code from that. The Zeep library will raise an exception for most errors before the call
        # is actually made, so we only need to account for a few cases when processing the response. All SOAP faults
        # are assumed to produce 500 status codes in accordance with the SOAP standard.
        if soap_fault is None:
            return_obj['rc'] = 0
            self.logger.debug("Request succeeded: ")
            self.logger.debug("     Status Code: 200")
            self.logger.debug("     Text: " + str(zeep_response))
        else:
            return_obj['rc'] = 500

            self.logger.error("Request failed: ")
            self.logger.error("     Status Code: 500")
            self.logger.error("     Fault Code: " + soap_fault['code'])
            self.logger.error("     Fault Message: " + soap_fault['message'])

            # in the event of an invalid session ID, unconditionally raise an exception to abort execution
            if soap_fault['code'] == 'axis2ns1:Server' and soap_fault['message'] == 'Internal Error':
                raise IBMFatal("HTTP Return code: 500. Fault message: " + soap_fault[
                    'message'] + "\n This can be caused by an invalid session with the server, or using invalid "
                                 "parameter values in the request.")

            if not ignore_error:
                raise IBMError("HTTP Return code: 500. Fault message: " + soap_fault['message'])
            return_obj['changed'] = False  # force changed to be False as there is an error

        return_obj['data'] = zeep.helpers.serialize_object(zeep_response)

    def _log_response(self, response):
        """
        Log an IBMResponse.
        :param response: An IBMResponse object to log.
        """
        if response:
            self.logger.debug("Response: " + str(response))
        else:
            self.logger.debug("Response: None")

