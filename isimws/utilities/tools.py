from typing import List, Dict, Optional
from collections import OrderedDict
import re

from isimws.application.isimapplication import IBMResponse


def build_attribute(attribute_type, key: str, value_list: List):
    """
    Build a SOAP ns1:WSAttribute object.
    :param attribute_type: The SOAP type that can be used to instantiate the object.
    :param key: Attribute key
    :param value_list: List of attribute values. Provide an empty list to set the value to an empty value.
    :return: The Python representation of the SOAP object.
    """
    attr = attribute_type()
    attr['name'] = key
    attr['operation'] = 0
    attr['isEncoded'] = False
    attr['values'] = {'item': value_list}
    return attr


def get_soap_attribute(returned_object: Dict, key: str) -> Optional[List]:
    """
    A method to simplify parsing of objects (such as services or roles) returned by the SOAP API when using a search or
    get operation. This method can be used to easily access attributes stored in the object's 'attributes' list.
    Depending on the type of object being searched for, certain attributes such as 'select', 'name', and 'itimDN'
    aren't part of this list and can be referenced by their keys instead.
    :param returned_object: An OrderedDict representing an object such as a role or service, as returned by the get
    and search calls.
    :param key: The name of a key to retrieve.
    :return: A list of values for the requested key, or None if the key doesn't exist.
    """
    attributes = returned_object['attributes']['item']

    for attribute in attributes:
        if attribute['name'].lower() == key.lower():
            return attribute['values']['item']

    return None


def list_soap_attribute_keys(returned_object: Dict) -> Optional[List]:
    """
    A method to simplify parsing of objects (such as services or roles) returned by the SOAP API when using a search or
    get operation. This method can be used to get a list of all attribute keys stored in the object's 'attributes' list.
    Depending on the type of object being searched for, certain attributes such as 'select', 'name', and 'itimDN'
    aren't part of this list and can be referenced by their keys instead.
    :param returned_object: An OrderedDict representing an object such as a role or service, as returned by the get
    and search calls.
    :return: A list of keys in the object's attributes list.
    """
    attributes = returned_object['attributes']['item']
    keys = []
    for attribute in attributes:
        keys.append(attribute['name'].lower())
    return keys


def strip_zeep_element_data(response: IBMResponse) -> IBMResponse:
    """
    There is a limitation with the Zeep library where the zeep.helpers.serialize_object() function does not properly
    serialize the Zeep Element objects returned by some SOAP calls. In cases where we want to return an IBMResponse
    object to be processed by Ansible, we need to strip this unserialized data because Ansible won't be able to
    interpret it properly. This function removes the part of the data attribute containing raw Zeep Elements. This
    functionality was not included in the ISIMApplication class because there are cases when we want to use the
    raw Element data, so we don't want to strip it every time.
    :param response: An IBMResponse object returned by a call to ISIMApplication.invoke_soap_request().
    :return: The IBMResponse object with the Zeep Element data removed from it's data attribute.
    """
    if isinstance(response['data'], list):
        for result in response['data']:
            for element in result['children']['item']:
                del element['_raw_elements']
    elif isinstance(response['data'], OrderedDict):
        for element in response['data']['children']['item']:
            del element['_raw_elements']

    return response
