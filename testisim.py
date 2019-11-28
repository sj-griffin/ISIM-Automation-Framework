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
    isim_server = ISIMApplication(hostname="192.168.42.106", user=u, port=9082)

    # Get a container
    print("Getting a container...")
    pretty_print(isimws.isim.container.get(isim_application=isim_server, container_dn="erglobalid=00000000000000000000,ou=demo,dc=com"))

    # Create a person
    print("Creating a person...")
    pretty_print(isimws.isim.person.create(isim_application=isim_server,
                                           container_dn="erglobalid=00000000000000000000,ou=demo,dc=com",
                                           profile_name="Person",
                                           username="jblow",
                                           surname="Blow",
                                           full_name="Joe Blow",
                                           aliases=["Jim", "Jack"],
                                           password="Object99",
                                           roles=[]))

     #
     # # Get the current SNMP monitoring setup details
     # p(ibmsecurity.isam.base.snmp_monitoring.get(isamAppliance=isam_server))
     # # Set the V2 SNMP monitoring
     # p(ibmsecurity.isam.base.snmp_monitoring.set_v1v2(isamAppliance=isam_server, community="IBM"))
     # # Commit or Deploy the changes
     # p(ibmsecurity.isam.appliance.commit(isamAppliance=isam_server))
