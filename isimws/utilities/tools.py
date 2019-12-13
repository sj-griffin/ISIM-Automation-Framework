from typing import List, Dict, Optional
import re


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
