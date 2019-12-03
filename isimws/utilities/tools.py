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
    :param value_list: List of attribute values
    :return: The Python representation of the SOAP object.
    """
    attr = attribute_type()
    attr['name'] = key
    attr['operation'] = 0
    attr['isEncoded'] = False
    attr['values'] = {'item': value_list}
    return attr
