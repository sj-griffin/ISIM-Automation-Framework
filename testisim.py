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
    # Create a user credential for ISIM application
    u = ISIMApplicationUser(username="itim manager", password="Object00")
    # Create an ISIM application with above credential
    isim_server = ISIMApplication(hostname="192.168.1.56", user=u, port=9082)

    # Get a list of organizations
    print("Getting organizations...")
    pretty_print(isimws.isim.organization.get_all(
        isim_application=isim_server
    ))

    # # Search for a container
    # print("Searching for a container...")
    # pretty_print(isimws.isim.container.search(
    #     isim_application=isim_server,
    #     parent_dn="erglobalid=00000000000000000000,ou=demo,dc=com",
    #     container_name="testou",
    #     profile="organizationalunit"
    # ))

    # Search for a provisioning policy
    # print("Searching for a provisioning policy...")
    # pretty_print(isimws.isim.provisioningpolicy.search(
    #     isim_application=isim_server,
    #     container_dn="erglobalid=00000000000000000000,ou=demo,dc=com",
    #     policy_name="test"
    # ))
    #
    # # Idempotently apply a provisioning policy configuration
    # print("Applying a provisioning policy configuration...")
    # pretty_print(isimws.isim.provisioningpolicy.apply(
    #     isim_application=isim_server,
    #     container_dn="erglobalid=00000000000000000000,ou=demo,dc=com",
    #     name="Provisioning policy test 1",
    #     priority=50,
    #     description="Here's a description",
    #     keywords="here are some keywords",
    #     caption="Here's a caption",
    #     available_to_subunits=False,
    #     enabled=True,
    #     membership_type="all",
    #     membership_roles=[],
    #     entitlements=[
    #         {
    #             'automatic': False,
    #             'ownership_type': 'all',
    #             'target_type': 'all',
    #             'service_type': None,
    #             'service_dn': None,
    #             'workflow': None
    #         }
    #     ],
    #     check_mode=False,
    #     force=False
    # ))


    # pretty_print(isimws.isim.provisioningpolicy.apply(
    #     isim_application=isim_server,
    #     container_dn="erglobalid=00000000000000000000,ou=demo,dc=com",
    #     name="PP apply test",
    #     priority=50,
    #     description="Here's a description",
    #     keywords="here are some keywords",
    #     caption="Here's a caption",
    #     available_to_subunits=False,
    #     enabled=True,
    #     membership_type="roles",
    #     membership_roles=['erglobalid=3882214986171532768,ou=roles,erglobalid=00000000000000000000,ou=demo,dc=com',
    #                       'erglobalid=3886333847069531567,ou=roles,erglobalid=00000000000000000000,ou=demo,dc=com'],
    #     entitlements=[
    #         {
    #             'automatic': False,
    #             'ownership_type': 'all',
    #             'target_type': 'all',
    #             'service_type': None,
    #             'service_dn': None,
    #             'workflow': None
    #         },
    #         {
    #             'automatic': True,
    #             'ownership_type': 'device',
    #             'target_type': 'policy',
    #             'service_type': 'ADprofile',
    #             'service_dn': None,
    #             'workflow': 'erglobalid=00000000000000000050,ou=workflow,erglobalid=00000000000000000000,ou=demo,dc=com'
    #         },
    #         {
    #             'automatic': False,
    #             'ownership_type': 'individual',
    #             'target_type': 'specific',
    #             'service_type': None,
    #             'service_dn': 'erglobalid=8710749904858128313,ou=services,erglobalid=00000000000000000000,ou=demo,dc=com',
    #             'workflow': 'erglobalid=00000000000000000050,ou=workflow,erglobalid=00000000000000000000,ou=demo,dc=com'
    #         }
    #     ],
    #     check_mode=False,
    #     force=False
    # ))

    # # Search for services
    # print("Searching for services...")
    # pretty_print(isimws.isim.service.search(
    #     isim_application=isim_server,
    #     container_dn="erglobalid=00000000000000000000,ou=demo,dc=com",
    #     ldap_filter="(erservicename=ad-test-feed)"
    # ))
    #
    # # Get a service
    # print("Getting a service...")
    # pretty_print(isimws.isim.service.get(
    #     isim_application=isim_server,
    #     service_dn="erglobalid=5621731231346846233,ou=services,erglobalid=00000000000000000000,ou=demo,dc=com"
    # ))
    #
    # Idempotently apply an account service configuration
    # print("Applying an account service configuration...")
    # pretty_print(isimws.isim.service.apply_account_service(
    #     isim_application=isim_server,
    #     container_dn="erglobalid=00000000000000000000,ou=demo,dc=com",
    #     name="soap-test-service 7",
    #     service_type="ADprofile",
    #     description="Here's a description",
    #     owner=None, # "erglobalid=544203505143873735,ou=0,ou=people,erglobalid=00000000000000000000,ou=demo,dc=com",
    #     service_prerequisite="erglobalid=8710749904858128313,ou=services,erglobalid=00000000000000000000,ou=demo,dc=com",
    #     define_access=True,
    #     access_name="Test access",
    #     access_type="role",
    #     access_description="Access description...",
    #     access_image_uri="test.test",
    #     access_search_terms=['search', 'term'],
    #     access_additional_info="More information",
    #     access_badges=[{'text': 'A badge', 'colour': 'blue'}],
    #     configuration={
    #         'erURL': 'demo.demo',
    #         'erUid': 'admin',
    #         'erPassword': 'Object00',
    #         'erADBasePoint': 'abc',
    #         'erADGroupBasePoint': 'def',
    #         'erADDomainUser': 'ghi',
    #         'erADDomainPassword': 'jkl',
    #         'erURI': ['test1', 'test2']
    #     },
    #     check_mode=False,
    #     force=False
    # ))
    #
    # # Idempotently apply an identity feed configuration
    # print("Applying an identity feed configuration...")
    # pretty_print(isimws.isim.service.apply_identity_feed(
    #     isim_application=isim_server,
    #     container_dn="erglobalid=00000000000000000000,ou=demo,dc=com",
    #     name="soap-test-feed 6",
    #     service_type="ADFeed",
    #     description="Here's a description",
    #     use_workflow=True,
    #     evaluate_sod=True,
    #     placement_rule="Here's a rule",
    #     configuration={
    #         'erURL': 'demo.demo',
    #         'erUid': 'admin',
    #         'erPassword': 'Object00',
    #         'erNamingContexts': ['erglobalid=00000000000000000000,ou=demo,dc=com'],
    #         'erPersonProfileName': 'Person',
    #         'erAttrMapFilename': '/test',
    #         'ernamingattribute': 'uid'  # will appear as 'sAMAccountName' in the UI
    #     },
    #     check_mode=False,
    #     force=False
    # ))

    # # Idempotently apply a role configuration
    # print("Applying a role configuration...")
    # pretty_print(isimws.isim.role.apply(
    #     isim_application=isim_server,
    #     container_dn="erglobalid=00000000000000000000,ou=demo,dc=com",
    #     name='Applied Role 5',
    #     role_classification='business',
    #     description='A role to test the SOAP API.',
    #     role_owners=[
    #         "erglobalid=3882214986171532768,ou=roles,erglobalid=00000000000000000000,ou=demo,dc=com"],
    #     user_owners=[
    #         "erglobalid=544203505143873735,ou=0,ou=people,erglobalid=00000000000000000000,ou=demo,dc=com"],
    #     enable_access=True,
    #     common_access=True,
    #     access_type='emailgroup',
    #     access_image_uri="test.demo/test",
    #     access_search_terms=["test", "testing"],
    #     access_additional_info="Some additional information",
    #     access_badges=[{'text': 'An orange badge', 'colour': 'orange'},
    #                    {'text': 'A red badge', 'colour': 'red'}],
    #     assignment_attributes=['attribute1', 'attribute2'],
    #     check_mode=False,
    #     force=False
    # ))

    # Search for roles
    # print("Searching for roles...")
    # pretty_print(isimws.isim.role.search(
    #     isim_application=isim_server,
    #     container_dn=None,
    #     ldap_filter="(errolename=test-role-2)"
    # ))
    #
    # # Get a role
    # print("Getting a role...")
    # pretty_print(isimws.isim.role.get(
    #     isim_application=isim_server,
    #     role_dn="erglobalid=7148929463058980179,ou=roles,erglobalid=00000000000000000000,ou=demo,dc=com"
    # ))

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
