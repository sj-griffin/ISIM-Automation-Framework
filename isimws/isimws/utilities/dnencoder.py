from typing import List, Dict, Optional
from isimws.application.isimapplication import ISIMApplication, IBMResponse, IBMError, IBMFatal
import isimws.isim
from isimws.utilities.tools import get_soap_attribute


class DNEncoder:
    isim_application: ISIMApplication
    organization_map: Dict  # maps organization names to DNs

    def __init__(self, isim_application: ISIMApplication):
        self.isim_application = isim_application

        # Retrieve organization DN mappings from the ISIMApplication
        self.organization_map = {}
        response = isim_application.invoke_soap_request("Retrieving organizations list",
                                                        "WSOrganizationalContainerService",
                                                        "getOrganizationTree",
                                                        [])

        if response['rc'] != 0:
            raise ValueError('Cannot retrieve organization information from the application server.')

        organization_info = response['data']
        for org in organization_info:
            self.organization_map[org['name']] = org['itimDN']

    def decode_from_isim_dn(self, dn: str) -> Optional[Dict]:
        """
        Takes an ISIM DN referring to an ISIM object and makes it human-readable by retrieving the container
            path, object name, and object type. Supports the following object types: 'role', 'person', 'service', and
            'workflow'. Returns None if the DN does not exist.
        :param: dn: An ISIM DN referring to a non-container object.
        :return: A Dict containing the keys 'container_path', 'name', and 'object_type'.
        """
        if dn is None:
            raise ValueError("You must supply a valid ISIM DN.")

        responses = []
        # Determine the object type
        if ',ou=roles,' in dn:
            object_type = 'role'
            try:
                responses.append(isimws.isim.role.get(
                    isim_application=self.isim_application,
                    role_dn=dn
                ))
            except IBMError as e:
                if "Role does not exist" in e.args[0]:
                    return None
                else:
                    raise e
        elif ',ou=people,' in dn:
            object_type = 'person'
            try:
                responses.append(isimws.isim.person.get(
                    isim_application=self.isim_application,
                    person_dn=dn
                ))
            except IBMError as e:
                if "LDAP: error code 32 - No Such Object" in e.args[0]:
                    return None
                else:
                    raise e
        elif ',ou=services,' in dn:
            object_type = 'service'
            try:
                responses.append(isimws.isim.service.get(
                    isim_application=self.isim_application,
                    service_dn=dn
                ))
            except IBMError as e:
                if "LDAP: error code 32 - No Such Object" in e.args[0]:
                    return None
                else:
                    raise e
        elif ',ou=workflow,' in dn:
            object_type = 'workflow'
            try:
                responses.append(isimws.isim.workflow.get_attribute(
                    isim_application=self.isim_application,
                    workflow_dn=dn,
                    attribute_name='erprocessname'
                ))

                responses.append(isimws.isim.workflow.get_attribute(
                    isim_application=self.isim_application,
                    workflow_dn=dn,
                    attribute_name='erparent'
                ))
            except IBMFatal as e:
                if "Internal Error" in e.args[0]:
                    return None
                else:
                    raise e
        else:
            raise ValueError("ISIM DN " + str(dn) + " doesn't match any supported object types. Supported types are "
                                                    "'role', 'person', 'service', and 'workflow'.")

        # Validate responses from the SOAP API
        for response in responses:
            if response['rc'] != 0:
                raise ValueError('Cannot retrieve object information for ' + str(dn) + ' from the application server.')

        # Process the SOAP API response
        if object_type == 'role':
            result = responses[0]['data']
            object_name = get_soap_attribute(result, "errolename")[0]
            container_dn = get_soap_attribute(result, "erparent")[0]
        elif object_type == 'person':
            result = responses[0]['data']
            object_name = get_soap_attribute(result, "uid")[0]
            container_dn = get_soap_attribute(result, "erparent")[0]
        elif object_type == 'service':
            result = responses[0]['data']
            object_name = get_soap_attribute(result, "erservicename")[0]
            container_dn = get_soap_attribute(result, "erparent")[0]
        elif object_type == 'workflow':
            object_name = responses[0]['data'][0]
            container_dn = responses[1]['data'][0]
        else:
            raise ValueError("ISIM DN " + str(dn) + " doesn't match any supported object types. Supported types are "
                                                    "'role', 'person', 'service', and 'workflow'.")

        # Convert the container DN to a container path
        container_path = self.dn_to_container_path(container_dn)

        return {'container_path': container_path, 'name': object_name, 'object_type': object_type}

    def encode_to_isim_dn(self, container_path: str, name: str, object_type: str) -> Optional[str]:
        """
        Takes a container path, a name and a type referring to an ISIM object and retrieves it's ISIM DN. Returns None
            if the specified object doesn't exist, and raises a ValueError if multiple objects exist that meet the
            criteria. Supports the following object types: 'role', 'person', 'service', 'provisioningpolicy',
            'container', and 'workflow'. This function is essentially just a wrapper for the get_unique_object()
            function which is also able to retrieve workflow DNs.
        :param: container_path: The container path of the parent container. Should be in the format
            '//organization_name//profile::container_name//profile::container_name'. Valid values for profile are 'ou'
            (organizational unit), 'bp' (business partner unit), 'lo' (location), or 'ad' (admin domain). The root
            container (i.e. the parent of all organizations) is specified as "//".
        :param: name: The name of the object. For a person, this is the uid. For a container, this includes the profile
            prefix. For example a location container called Sydney would be "lo::Sydney". MAKE SURE YOU USE THE EXACT,
            CASE-SENSITIVE NAME.
        :param: object_type: The type of the object. Valid options are 'role', 'person', 'service',
            'provisioningpolicy', 'container', and 'workflow'.
        :return: The ISIM DN referring to the object.
        """
        if container_path is None or \
                name is None or \
                object_type is None:
            raise ValueError("You must supply values for container_path, name, and object_type.")
        
        # Retrieving workflow objects is not supported by the get_unique_object() function, so the logic to resolve
        # a workflow to a DN is implemented here instead.
        if object_type == "workflow":
            try:
                search_response = isimws.isim.workflow.search_attribute(
                    isim_application=self.isim_application,
                    container_dn=self.container_path_to_dn(container_path),
                    ldap_filter="(erprocessname=" + name + ")",
                    attribute_name="erglobalid"
                )
            except IBMFatal as e:
                if "Internal Error" in e.args[0]:
                    return None
                else:
                    raise e

            if search_response['rc'] != 0:
                raise ValueError("An error was encountered while searching for a workflow with the name " +
                                 name + " in " + container_path + ".")

            # Validate that there is only one result
            if len(search_response['data']) > 1:
                raise ValueError(
                    "Unable to uniquely identify object. More than one workflow was found with the "
                    "name " + name + " in " + container_path + ".")
            elif len(search_response['data']) < 1:
                return None
            else:
                path_components = container_path.split("//")
                org_name = path_components[1]
                return "erglobalid=" + str(search_response["data"][0]) + ",ou=workflow," + self.organization_map[
                    str(org_name)]
        elif object_type == "role" or \
                object_type == "service" or \
                object_type == "person" or \
                object_type == "provisioningpolicy" or \
                object_type == "container":
            object_result = self.get_unique_object(container_path=container_path, name=name, object_type=object_type)
            if object_result is None:
                return None
            else:
                return object_result["itimDN"]
        else:
            raise ValueError(str(object_type) + " is not a valid value for object_type. Valid values are 'role', "
                                                "'person', 'service', 'provisioningpolicy', 'container', and "
                                                "'workflow'.")

    def get_unique_object(self, container_path: str, name: str, object_type: str) -> Optional[Dict]:
        """
        Takes a container path, a name and a type referring to an ISIM object and retrieves it. Returns None
            if the specified object doesn't exist, and raises a ValueError if multiple objects exist that meet the
            criteria. Supports the following object types: 'role', 'person', 'service', 'provisioningpolicy', and
            'container'.
        :param: container_path: The container path of the parent container. Should be in the format
            '//organization_name//profile::container_name//profile::container_name'. Valid values for profile are 'ou'
            (organizational unit), 'bp' (business partner unit), 'lo' (location), or 'ad' (admin domain). The root
            container (i.e. the parent of all organizations) is specified as "//".
        :param: name: The name of the object. For a person, this is the uid. For a container, this includes the profile
            prefix. For example a location container called Sydney would be "lo::Sydney". MAKE SURE YOU USE THE EXACT,
            CASE-SENSITIVE NAME.
        :param: object_type: The type of the object. Valid options are 'role', 'person', 'service',
            'provisioningpolicy', and 'container'.
        :return: The object as returned by the SOAP API.
        """
        if container_path is None or \
                name is None or \
                object_type is None:
            raise ValueError("You must supply values for container_path, name, and object_type.")

        # Convert the container path to a DN
        container_dn = self.container_path_to_dn(container_path)

        if object_type == "role":
            search_response = isimws.isim.role.search(
                isim_application=self.isim_application,
                container_dn=container_dn,
                ldap_filter="(errolename=" + name + ")"
            )
        elif object_type == "person":
            search_response = isimws.isim.person.search(
                isim_application=self.isim_application,
                ldap_filter="(uid=" + name + ")"
            )
        elif object_type == "service":
            search_response = isimws.isim.service.search(
                isim_application=self.isim_application,
                container_dn=container_dn,
                ldap_filter="(erservicename=" + name + ")"
            )
        elif object_type == "provisioningpolicy":
            search_response = isimws.isim.provisioningpolicy.search(
                isim_application=self.isim_application,
                container_dn=container_dn,
                policy_name=name
            )
        elif object_type == "container":
            name_components = name.split("::")
            if len(name_components) != 2:
                raise ValueError(str(name) + " is not a valid value for container name. Make sure you include the "
                                             "profile prefix component.")
            if name_components[0] == "o":
                profile = "Organization"
            elif name_components[0] == "ou":
                profile = "OrganizationalUnit"
            elif name_components[0] == "bp":
                profile = "BPOrganization"
            elif name_components[0] == "lo":
                profile = "Location"
            elif name_components[0] == "ad":
                profile = "AdminDomain"
            else:
                raise ValueError(name_components[0] + " is not a valid value for a profile prefix. Valid values are "
                                                      "'o', 'ou', 'bp', 'lo', and 'ad'.")
            name = name_components[1]
            search_response = isimws.isim.container.search(
                    isim_application=self.isim_application,
                    parent_dn=container_dn,
                    container_name=name,
                    profile=profile
                )
        else:
            raise ValueError(str(object_type) + " is not a valid value for object_type. Valid values are 'role', "
                                                "'person', 'service', 'provisioningpolicy', and 'container'.")

        if search_response['rc'] != 0:
            raise ValueError("An error was encountered while searching for a " + object_type + " with the name " +
                             name + " in " + container_path + ".")

        # Filter out results that don't match the exact name or that aren't direct children of the parent.
        # We iterate backwards through the results so we can delete entries as we go without breaking the loop logic
        for index in range(len(search_response['data']) - 1, -1, -1):
            result = search_response['data'][index]

            if object_type != "person":
                if result['name'] != name:
                    del search_response['data'][index]
            else:
                uid_attribute = get_soap_attribute(result, "uid")[0]
                if uid_attribute != name:
                    del search_response['data'][index]

            if object_type != "provisioningpolicy":
                parent_attribute = get_soap_attribute(result, "erparent")[0]
            else:
                parent_attribute = result["organizationalContainer"]["itimDN"]

            if parent_attribute != container_dn:
                del search_response['data'][index]

        # Validate that there is only one result left
        if len(search_response['data']) > 1:
            raise ValueError("Unable to uniquely identify object. More than one " + object_type + " was found with the "
                             "name " + name + " in " + container_path + ".")
        elif len(search_response['data']) < 1:
            return None
        else:
            return search_response["data"][0]

    def container_path_to_dn(self, path: str) -> str:
        """
        Takes a path referring to an ISIM organizational container and converts it to a valid ISIM DN. This function
            assumes that all containers with the same parent and profile have unique names.
        :param: path: The path to convert. The expected format is
            '//organization_name//profile::container_name//profile::container_name'. Valid values for profile are 'ou'
            (organizational unit), 'bp' (business partner unit), 'lo' (location), or 'ad' (admin domain). To specify 
            the root container (i.e. the parent of all organizations), use "//".
        :return: An ISIM DN referring to the specified container.
        """
        # Validate the path format and determine whether it refers to the root container
        components = path.split('//')
        if len(components) < 2:
            raise ValueError(str(path) + " is not a valid path. Paths must be of the format "
                                         "'//organization_name//profile::container_name//profile::container_name'.")
        if components[0] != "":
            raise ValueError(str(path) + " is not a valid path. Paths must be of the format "
                                         "'//organization_name//profile::container_name//profile::container_name'.")
        if len(components) == 2 and components[1] == "":
            return self.isim_application.root_dn

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
            parent_container_path = self.dn_to_container_path(parent_dn)

            next_container = self.get_unique_object(container_path=parent_container_path,
                                                    name=components[next_component_index],
                                                    object_type='container')

            if next_container is None:
                raise ValueError("The container '" + components[next_component_index] + "' could not "
                                 "be found. Make sure that the path and profile is correct.")

            # Get the DN of the found container so that it's children can be searched on the next iteration.
            parent_dn = next_container['itimDN']
            next_component_index += 1

        return parent_dn

    def dn_to_container_path(self, dn: str) -> str:
        """
        Takes an ISIM DN referring to an ISIM organizational container and converts it to a container path in the format
            '//organization_name//profile::container_name//profile::container_name'. Valid values for profile are 'ou'
            (organizational unit), 'bp' (business partner unit), 'lo' (location), or 'ad' (admin domain). The root
            container (i.e. the parent of all organizations) is specified as "//". This function assumes that all
            containers with the same parent and profile have unique names.
        :param: dn: The ISIM DN to convert.
        :return: The container path of the specified container.
            '//organization_name//profile::container_name//profile::container_name'. Valid values for profile are 'ou'
            (organizational unit), 'bp' (business partner unit), 'lo' (location), or 'ad' (admin domain). The root
            container (i.e. the parent of all organizations) is specified as "//".
        """

        # Check if the DN is the root DN
        if dn == self.isim_application.root_dn:
            return "//"
        
        container_path = ""
        current_dn = dn

        while True:
            # Look up the DN, add it to the container path, and retrieve it's parent's DN.
            get_response = isimws.isim.container.get(self.isim_application,
                                                     container_dn=current_dn
                                                     )

            # If an error was encountered and ignored, raise an exception
            if get_response['rc'] != 0:
                raise ValueError(
                    "There was an error while retrieving a container. Return code: " + get_response['rc'])
            result = get_response['data']

            # If the object is not a container, it will be missing expected fields.
            if 'name' not in result or \
                    'profileName' not in result or \
                    'attributes' not in result or \
                    'children' not in result or \
                    'supervisorDN' not in result:
                raise ValueError("The DN '" + current_dn + "' does not refer to a container. Make sure that the DN is "
                                 "correct.")

            if result['profileName'] is None:
                # If the DN doesn't exist, the API will return a result with empty values.
                raise ValueError("The DN '" + current_dn + "' could not be found in the system. Make sure that the DN "
                                 "is correct.")
            elif result['profileName'] == "BPOrganization":
                profile = "bp"
            elif result['profileName'] == "Location":
                profile = "lo"
            elif result['profileName'] == "AdminDomain":
                profile = "ad"
            elif result['profileName'] == "OrganizationalUnit":
                profile = "ou"
            elif result['profileName'] == "Organization":
                return "//" + result["name"] + container_path
            else:
                raise ValueError("The DN '" + current_dn + "' does not have a valid container profile. Make sure that "
                                 "the DN is correct.")

            container_path = "//" + profile + "::" + result['name'] + container_path
            current_dn = get_soap_attribute(result, "erparent")[0]
