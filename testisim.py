import logging.config
import pprint
from isimws.application.isimapplication import ISIMApplication
from isimws.user.isimapplicationuser import ISIMApplicationUser
import pkgutil
import importlib


def import_submodules(package, recursive=True):
    """
    Import all submodules of a module, recursively, including subpackages

    :param package: package (name or actual module)
    :type package: str | module
    :rtype: dict[str, types.ModuleType]
    """
    if isinstance(package, str):
        package = importlib.import_module(package)
    results = {}
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        full_name = package.__name__ + '.' + name
        results[full_name] = importlib.import_module(full_name)
        if recursive and is_pkg:
            results.update(import_submodules(full_name))
    return results


import isimws

# Import all packages within ibmsecurity - recursively
# Note: Advisable to replace this code with specific imports for production code
import_submodules(isimws)

# Setup logging to send to stdout, format and set log level
# logging.getLogger(__name__).addHandler(logging.NullHandler())
logging.basicConfig()
# Valid values are 'DEBUG', 'INFO', 'ERROR', 'CRITICAL'
logLevel = 'INFO'
DEFAULT_LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] [PID:%(process)d TID:%(thread)d] [%(levelname)s] [%(name)s] [%(funcName)s():%(lineno)s] %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': logLevel,
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        '': {
            'level': logLevel,
            'handlers': ['default'],
            'propagate': True
        },
        'requests.packages.urllib3.connectionpool': {
            'level': 'ERROR',
            'handlers': ['default'],
            'propagate': True
        }
    }
}
logging.config.dictConfig(DEFAULT_LOGGING)


# Function to pretty print JSON data
def pretty_print(jdata):
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(jdata)


if __name__ == "__main__":
    """
    This test program should not execute when imported, which would otherwise
    cause problems when generating the documentation.
    """
    # Create a user credential for ISAM appliance
    u = ISIMApplicationUser(username="itim manager", password="Object00")
    # Create an ISAM appliance with above credential
    isim_server = ISIMApplication(hostname="192.168.1.56", user=u, port=9082)

    # Create a role
    print("Creating a role...")
    pretty_print(isimws.isim.role.create(isim_application=isim_server,
                                         container_dn="erglobalid=00000000000000000000,ou=demo,dc=com",
                                         role_classification='application',
                                         name='test-role',
                                         description='A role to test the SOAP API',
                                         role_owners=["erglobalid=3882214986171532768,ou=roles,erglobalid=00000000000000000000,ou=demo,dc=com"],
                                         user_owners=["erglobalid=544203505143873735,ou=0,ou=people,erglobalid=00000000000000000000,ou=demo,dc=com"],
                                         enable_access=True,
                                         common_access=False,
                                         access_type='emailgroup',
                                         access_image_uri=None,
                                         access_search_terms=["test", "testing"],
                                         access_additional_info="Some additional information",
                                         access_badges=[{'text': 'An orange badge', 'colour': 'orange'},
                                                        {'text': 'A red badge', 'colour': 'red'}],
                                         assignment_attributes=['attribute1', 'attribute2']))


    # Search for roles
    print("Searching for roles...")
    pretty_print(isimws.isim.role.search(isim_application=isim_server,
                                         container_dn=None,
                                         ldap_filter="(errolename=test-role)"))

    # Get a role
    print("Getting a role...")
    pretty_print(isimws.isim.role.get(isim_application=isim_server,
                                      role_dn="erglobalid=7148929463058980179,ou=roles,erglobalid=00000000000000000000,ou=demo,dc=com"))

    # # Get a container
    # print("Getting a container...")
    # pretty_print(isimws.isim.container.get(isim_application=isim_server, container_dn="erglobalid=00000000000000000000,ou=demo,dc=com"))
    #
    # # Create a person
    # print("Creating a person...")
    # pretty_print(isimws.isim.person.create(isim_application=isim_server,
    #                                        container_dn="erglobalid=00000000000000000000,ou=demo,dc=com",
    #                                        profile_name="Person",
    #                                        username="bbrow",
    #                                        surname="Brow",
    #                                        full_name="Boe Brow",
    #                                        aliases=["Jim", "Jack"],
    #                                        password="Object99",
    #                                        roles=[]))
