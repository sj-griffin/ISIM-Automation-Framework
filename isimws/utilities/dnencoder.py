from typing import List, Dict, Optional
from isimws.application.isimapplication import ISIMApplication, IBMResponse
from isimws.isim import container


class DNEncoder:
    isim_application: ISIMApplication
    organization_map: Dict  # maps organization names to DNs
    dn_map: Dict  # maps DNs to organization names

    def __init__(self, isim_application: ISIMApplication):
        self.isim_application = isim_application
        # Retrieve organization DN mappings from the ISIMApplication
        self.organization_map = {}
        self.dn_map = {}
        response = isim_application.invoke_soap_request("Retrieving organizations list",
                                                        "WSOrganizationalContainerService",
                                                        "getOrganizationTree",
                                                        [])

        if response['rc'] != 0:
            raise ValueError('Cannot retrieve organization information from the application server.')

        organization_info = response['data']
        for org in organization_info:
            self.organization_map[org['name']] = org['itimDN']
            self.dn_map[org['itimDN']] = org['name']

    def decode_from_isim_dn(self, dn: str) -> Dict:
        """
        Takes an ISIM DN referring to a non-container object and makes it human-readable by retrieving the name, type,
            and organization. Supports the following object types: 'role', 'person', 'service',
            and 'workflow'.
        :param dn: An ISIM DN referring to a non-container object.
        :return: A Dict containing the keys 'name', 'type', and 'organization'.
        """
        # Extract the organization component by comparing the DN to known organization components
        non_org_component = None
        organization_name = None
        for org_component in self.dn_map:
            if dn.endswith(org_component):
                non_org_component = dn[:-(len(org_component) + 1)]
                organization_name = self.dn_map[org_component]
                break

        if organization_name is None:
            raise ValueError("ISIM DN " + str(dn) + " doesn't match any organization in the system.")

        # Get the required SOAP types for the API call
        search_arguments_type_response = self.isim_application.retrieve_soap_type("WSSearchDataService",
                                                                                  "ns1:WSSearchArguments")

        # If an error was encountered and ignored, raise an error.
        if search_arguments_type_response['rc'] != 0:
            raise ValueError('Cannot retrieve object information for ' + str(dn) + ' from the application server.')
        search_arguments_type = search_arguments_type_response['data']

        data = []

        search_arguments_object = search_arguments_type()

        # Extract the type component by comparing the DN to known type components
        if non_org_component.endswith('ou=roles'):
            object_type = 'role'
            search_arguments_object['category'] = 'Role'
            search_arguments_object['returnedAttributeName'] = 'erRoleName'
        elif non_org_component.endswith('ou=people'):
            object_type = 'person'
            search_arguments_object['category'] = 'Person'
            search_arguments_object['returnedAttributeName'] = 'uid'  # or cn
        elif non_org_component.endswith('ou=services'):
            object_type = 'service'
            search_arguments_object['category'] = 'Service'
            search_arguments_object['returnedAttributeName'] = 'erServiceName'
        elif non_org_component.endswith('ou=workflow'):
            object_type = 'workflow'
            search_arguments_object['category'] = 'Workflow'
            search_arguments_object['returnedAttributeName'] = 'erProcessName'
        else:
            raise ValueError("ISIM DN " + str(dn) + " doesn't match any supported object types. Supported types are "
                                                    "'role', 'person', 'service', and 'workflow'.")

        # extract the erglobalid value from the dn
        erglobalid = non_org_component.split(',')[0][11:]

        # We use different logic to find a person compared to other object types
        if object_type != 'person':
            search_arguments_object['filter'] = '(&(erglobalid=' + str(erglobalid) + ')(erparent=' + \
                                                self.organization_map[organization_name] + '))'
        else:
            search_arguments_object['filter'] = '(erglobalid=' + str(erglobalid) + ')'

        search_arguments_object['base'] = 'org'  # 'global' or 'org'

        data.append(search_arguments_object)

        # Make a call to the API to retrieve the object name
        response = self.isim_application.invoke_soap_request("Retrieving an object",
                                                             "WSSearchDataService",
                                                             "findSearchFilterObjects",
                                                             data)
        if response['rc'] != 0:
            raise ValueError('Cannot retrieve object information for ' + str(dn) + ' from the application server.')

        # There should only be one result from the search.
        if len(response['data']) == 0:
            raise ValueError("No results found for DN " + str(dn))
        elif len(response['data']) > 1:
            raise ValueError("Could not identify a unique " + object_type + " from the DN " + str(dn))

        object_name = str(response['data'][0])

        return {'organization': organization_name, 'type': object_type, 'name': object_name}

    def encode_to_isim_dn(self, organization: str, name: str, object_type: str) -> str:
        """
        Takes an organization, a name and a type referring to an ISIM object and retrieves it's ISIM DN. Supports the
        following object types: 'role', 'person', 'service', and 'workflow'.
        :param organization: The organization the object belongs to.
        :param name: The name of the object.
        :param object_type: The type of the object. Valid options are 'role', 'person', 'service', and
            'workflow'.
        :return: The ISIM DN referring to the object.
        """
        # Translate the organization name to a root DN
        organization_component = self.organization_map[str(organization)]

        # Get the required SOAP types for the API call
        search_arguments_type_response = self.isim_application.retrieve_soap_type("WSSearchDataService",
                                                                                  "ns1:WSSearchArguments")

        # If an error was encountered and ignored, raise an error.
        if search_arguments_type_response['rc'] != 0:
            raise ValueError('Cannot retrieve object information for ' + str(object_type) + ' ' + str(name) + 'from '
                                                                                                              'the application server.')
        search_arguments_type = search_arguments_type_response['data']

        data = []

        search_arguments_object = search_arguments_type()

        # Translate the type to an OU
        if object_type.lower() == 'role':
            ou_component = 'ou=roles'
            search_arguments_object['category'] = 'Role'
            search_arguments_object['filter'] = '(&(erRoleName=' + str(name) + ')(erparent=' + \
                                                self.organization_map[organization] + '))'
        elif object_type.lower() == 'person':
            ou_component = 'ou=people'
            search_arguments_object['category'] = 'Person'
            search_arguments_object['filter'] = '(uid=' + str(
                name) + ')'  # we don't search based on erparent for a person object
        elif object_type.lower() == 'service':
            ou_component = 'ou=services'
            search_arguments_object['category'] = 'Service'
            search_arguments_object['filter'] = '(&(erServiceName=' + str(name) + ')(erparent=' + \
                                                self.organization_map[organization] + '))'
        elif object_type.lower() == 'workflow':
            ou_component = 'ou=workflow'
            search_arguments_object['category'] = 'Workflow'
            search_arguments_object['filter'] = '(&(erProcessName=' + str(name) + ')(erparent=' + \
                                                self.organization_map[organization] + '))'
        else:
            raise ValueError(str(object_type) + " is not a supported object type. Supported types are 'role', 'person',"
                                                " 'service', and 'workflow'.")

        search_arguments_object['returnedAttributeName'] = 'erglobalid'
        search_arguments_object['base'] = 'org'  # 'global' or 'org'

        data.append(search_arguments_object)

        # Make a call to the API to retrieve the erglobalid value
        response = self.isim_application.invoke_soap_request("Retrieving an object",
                                                             "WSSearchDataService",
                                                             "findSearchFilterObjects",
                                                             data)
        if response['rc'] != 0:
            raise ValueError('Cannot retrieve object information for ' + str(object_type) + ' ' + str(name) + 'from '
                                                                                                              'the application server.')

        # There should only be one result from the search.
        if len(response['data']) == 0:
            raise ValueError("No results found for " + str(object_type) + " " + str(name))
        elif len(response['data']) > 1:
            raise ValueError("Could not identify a unique " + str(object_type) + " for " + str(name))

        erglobalid = str(response['data'][0])

        # We use different logic to form a person DN compared to other object types
        if object_type != 'person':
            dn = 'erglobalid=' + erglobalid + ',' + ou_component + ',' + organization_component
        else:
            # This may need to be changed. Need to test on a system with a large number of people objects.
            dn = 'erglobalid=' + erglobalid + ',ou=0,' + ou_component + ',' + organization_component
        return dn

    def container_path_to_dn(self, path: str) -> str:
        """
        Takes a path referring to an ISIM organizational container and converts it to a valid ISIM DN. This function
            assumes that all containers with the same parent have unique names.
        :param path: The path to convert. The expected format is
            '//organization_name//profile::container_name//profile::container_name'. Valid values for profile are 'ou'
            (organizational unit), 'bp' (business partner unit), 'lo' (location), or 'ad' (admin domain).
        :return: An ISIM DN referring to the specified container.
        """
        # Validate the path format
        components = path.split('//')
        if len(components) < 2:
            raise ValueError(str(path) + " is not a valid path. Paths must be of the format "
                                         "'//organization_name//profile::container_name//profile::container_name'.")
        if components[0] != "":
            raise ValueError(str(path) + " is not a valid path. Paths must be of the format "
                                         "'//organization_name//profile::container_name//profile::container_name'.")
        for index in range(1, len(components)):
            if len(components[index]) == 0:
                raise ValueError(str(path) + " is not a valid path. Paths must be of the format "
                                             "'//organization_name//profile::container_name//profile::container_name'.")

        # Convert the organization name to a DN using the existing map.
        if components[1] not in self.organization_map:
            raise ValueError("The organization '" + components[1] + "' could not be found.")

        organization_dn = self.organization_map[components[1]]

        # No further action is required if the organization is the only component in the path
        if len(components) == 2:
            return organization_dn

        parent_dn = organization_dn
        next_component_index = 2

        # Iterate through the components in the path, searching under each container for the next container in the path.
        while next_component_index < len(components):
            # Search among the parent's children for the next container in the path.
            next_component = components[next_component_index].split('::')
            if len(next_component) != 2:
                raise ValueError(str(path) + " is not a valid path. Paths must be of the format "
                                             "'//organization_name//profile::container_name//profile::container_name'.")

            if next_component[0] == 'ou':
                next_component_profile = 'organizationalunit'
            elif next_component[0] == 'bp':
                next_component_profile = 'businesspartnerunit'
            elif next_component[0] == 'lo':
                next_component_profile = 'location'
            elif next_component[0] == 'ad':
                next_component_profile = 'admindomain'
            else:
                raise ValueError(next_component[0] + " is not a valid profile. Valid values for profile are 'ou' "
                                                     "(organizational unit), 'bp' (business partner unit), 'lo' "
                                                     "(location), or 'ad' (admin domain).")

            next_component_name = next_component[1]

            search_results = container.search(self.isim_application,
                                              parent_dn,
                                              next_component_name,
                                              next_component_profile
                                              )

            if len(search_results['data']) == 0:
                raise ValueError("The " + next_component_profile + " container '" + next_component_name + "' could not "
                                 "be found. Make sure that the path and profile is correct.")
            elif len(search_results['data']) > 1:
                raise ValueError("Could not uniquely identify the container '" + next_component_name + "'. There was "
                                 "more than one container found with the same name, profile, and parent.")

            # Get the DN of the found container so that it's children can be searched on the next iteration.
            parent_dn = search_results['data'][0]['itimDN']
            next_component_index += 1

        return parent_dn
