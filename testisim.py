import logging.config
import pprint
from isimws.application.isimapplication import ISIMApplication
from isimws.user.isimapplicationuser import ISIMApplicationUser
from isimws.utilities.dnencoder import DNEncoder
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
    isim_server = ISIMApplication(hostname="192.168.1.56", root_dn="ou=demo,dc=com", user=u, port=9082)

    dn_encoder = DNEncoder(isim_server)

    # Convert a path to a DN
    # print("Converting a path to a DN...")
    # pretty_print(dn_encoder.container_path_to_dn('//demo//lo::Sydney//ou::ou1//bp::testing'))
    # pretty_print(dn_encoder.container_path_to_dn('//IBM'))
    # pretty_print(dn_encoder.container_path_to_dn('//'))
    #
    # # Convert a DN to a path
    # print("Converting a DN to a path...")
    # pretty_print(dn_encoder.dn_to_container_path('erglobalid=3955740627586799273,ou=orgChart,erglobalid=00000000000000000000,ou=demo,dc=com'))
    # pretty_print(dn_encoder.dn_to_container_path('erglobalid=2668832026328970745,ou=demo,dc=com'))
    # pretty_print(dn_encoder.dn_to_container_path('ou=demo,dc=com'))

    #
    # # Decode a DN
    # print("Decoding a DN...")
    # pretty_print(dn_encoder.decode_from_isim_dn('erglobalid=3882214986171532768,ou=roles,erglobalid=00000000000000000000,ou=demo,dc=com'))
    # pretty_print(dn_encoder.decode_from_isim_dn('erglobalid=DOESNTEXIST,ou=roles,erglobalid=00000000000000000000,ou=demo,dc=com'))
    #
    # pretty_print(dn_encoder.decode_from_isim_dn('erglobalid=00000000000000000050,ou=workflow,erglobalid=00000000000000000000,ou=demo,dc=com'))
    # pretty_print(dn_encoder.decode_from_isim_dn('erglobalid=DOESNTEXIST,ou=workflow,erglobalid=00000000000000000000,ou=demo,dc=com'))
    #
    # pretty_print(dn_encoder.decode_from_isim_dn('erglobalid=8625498261252005197,ou=services,erglobalid=00000000000000000000,ou=demo,dc=com'))
    # pretty_print(dn_encoder.decode_from_isim_dn('erglobalid=DOESNTEXIST,ou=services,erglobalid=00000000000000000000,ou=demo,dc=com'))
    #
    # pretty_print(dn_encoder.decode_from_isim_dn('erglobalid=4352532358240739134,ou=0,ou=people,erglobalid=00000000000000000000,ou=demo,dc=com'))
    # pretty_print(dn_encoder.decode_from_isim_dn('erglobalid=DOESNTEXIST,ou=0,ou=people,erglobalid=00000000000000000000,ou=demo,dc=com'))

    # pretty_print(dn_encoder.decode_from_isim_dn('erglobalid=4740767743419216325,ou=0,ou=people,erglobalid=2668832026328970745,ou=demo,dc=com'))
    # pretty_print(dn_encoder.decode_from_isim_dn('erglobalid=00000000000000000007,ou=0,ou=people,erglobalid=00000000000000000000,ou=demo,dc=com'))

    # # Encode a DN
    # print("Encoding a DN...")
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo', name='new-role', object_type='role'))
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo', name='DOESNT EXIST', object_type='role'))
    #
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo//lo::Sydney//ad::ggg', name='sublevel workflow', object_type='workflow'))
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo//lo::Sydney//ad::ggg', name='DOESNT EXIST', object_type='workflow'))
    #
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo//lo::Sydney//ou::ou1//bp::testing', name='ad-test-service', object_type='service'))
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo//lo::Sydney//ou::ou1//bp::testing', name='DOESNT EXIST', object_type='service'))
    #
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo//lo::Sydney//ou::ou1', name='bjones', object_type='person'))
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo//lo::Sydney//ou::ou1', name='DOESNT EXIST', object_type='person'))
    #
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//IBM', name='ayang', object_type='person'))
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo', name='itimadmin', object_type='person'))
    #
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo//lo::Sydney//ou::ou1//bp::testing', name='Provisioning policy test 1', object_type='provisioningpolicy'))
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo//lo::Sydney//ou::ou1//bp::testing', name='DOESNT EXIST', object_type='provisioningpolicy'))

    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo//lo::Sydney//ou::ou1//bp::testing', name='ad::123', object_type='container'))
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo//lo::Sydney//ou::ou1', name='bp::testing', object_type='container'))
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo//lo::Sydney', name='ou::ou1', object_type='container'))
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//demo', name='lo::Sydney', object_type='container'))
    # pretty_print(dn_encoder.encode_to_isim_dn(container_path='//', name='o::IBM', object_type='container'))

    # # Get a list of organizations
    # print("Getting organizations...")
    # pretty_print(isimws.isim.organization.get_all(
    #     isim_application=isim_server
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
    #     container_path="//demo//lo::Sydney//ou::ou1//bp::testing",
    #     name="Provisioning policy test 999",
    #     priority=50,
    #     description="Here's a description.",
    #     keywords="here are some keywords",
    #     caption="Here's a caption",
    #     available_to_subunits=False,
    #     enabled=True,
    #     membership_type="roles",
    #     membership_roles=[
    #         ('//demo', 'new-role'),
    #         ('//demo//lo::Sydney//ou::ou1//bp::testing', 'Applied Role 88')
    #     ],
    #     entitlements=[
    #         {
    #             'automatic': False,
    #             'ownership_type': 'all',
    #             'target_type': 'specific',
    #             'service_type': None,
    #             'service': ('//demo', 'ITIM Service'),
    #             'workflow': ('//demo', 'Default Account Request Workflow')
    #         }
    #     ],
    #     check_mode=False,
    #     force=False
    # ))
    #
    # pretty_print(isimws.isim.provisioningpolicy.apply(
    #     isim_application=isim_server,
    #     container_path="//demo//lo::Sydney//ou::ou1//bp::testing",
    #     name="PP apply test 999",
    #     priority=50,
    #     description="Here's a description.",
    #     keywords="here are some keywords",
    #     caption="Here's a caption",
    #     available_to_subunits=False,
    #     enabled=True,
    #     membership_type="roles",
    #     membership_roles=[
    #         ('//demo', 'new-role'),
    #         ('//demo', 'Demo Role')
    #     ],
    #     entitlements=[
    #         {
    #             'automatic': False,
    #             'ownership_type': 'all',
    #             'target_type': 'all',
    #             'service_type': None,
    #             'service': None,
    #             'workflow': None
    #         },
    #         {
    #             'automatic': True,
    #             'ownership_type': 'device',
    #             'target_type': 'policy',
    #             'service_type': 'ADprofile',
    #             'service': None,
    #             'workflow': ('//demo', 'Default Account Request Workflow')
    #         },
    #         {
    #             'automatic': False,
    #             'ownership_type': 'individual',
    #             'target_type': 'specific',
    #             'service_type': None,
    #             'service': ('//demo', 'ITIM Service'),
    #             'workflow': ('//demo', 'Default Account Request Workflow')
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
    #     service_dn="erglobalid=8416561955645170234,ou=services,erglobalid=00000000000000000000,ou=demo,dc=com"
    # ))
    #
    # Idempotently apply an account service configuration
    # print("Applying an account service configuration...")
    # pretty_print(isimws.isim.service.apply_account_service(
    #     isim_application=isim_server,
    #     container_path="//demo//lo::Sydney//ou::ou1//bp::testing",
    #     name="soap-test-service 105",
    #     service_type="ADprofile",
    #     description="Here's a description",
    #     owner=("//demo//lo::Sydney//ou::ou1", "bjones"),
    #     service_prerequisite=("//demo", "ITIM Service"),
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
    #     container_path="//demo//lo::Sydney//ou::ou1//bp::testing",
    #     name="soap-test-feed 105",
    #     service_type="ADFeed",
    #     description="Here's a description",
    #     use_workflow=True,
    #     evaluate_sod=True,
    #     placement_rule="Here's a rule",
    #     configuration={
    #         'erURL': 'demo.demo',
    #         'erUid': 'admin',
    #         'erPassword': 'Object00',
    #         'erNamingContexts': ['//demo//lo::Sydney//ou::ou1//bp::testing'],
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
    #     container_path="//demo//lo::Sydney//ou::ou1//bp::testing",
    #     name='Applied Role 181',
    #     role_classification='business',
    #     description='A role to test the SOAP API.',
    #     role_owners=[
    #         ("//demo", "new-role")
    #     ],
    #     user_owners=[
    #         ("//demo//lo::Sydney//ou::ou1", "bjones")
    #     ],
    #     enable_access=True,
    #     common_access=True,
    #     access_type='emailgroup',
    #     access_image_uri="test.demo/test",
    #     access_search_terms=["test", "testing", "test1"],
    #     access_additional_info="Some additional information",
    #     access_badges=[{'text': 'An orange badge', 'colour': 'orange'},
    #                    {'text': 'A red badge', 'colour': 'red'}],
    #     assignment_attributes=['attribute1', 'attribute2'],
    #     check_mode=False,
    #     force=False
    # ))

    # # Search for roles
    # print("Searching for roles...")
    # pretty_print(isimws.isim.role.search(
    #     isim_application=isim_server,
    #     container_dn=None,
    #     ldap_filter="(errolename=new-role)"
    # ))
    #
    # # Get a role
    # print("Getting a role...")
    # pretty_print(isimws.isim.role.get(
    #     isim_application=isim_server,
    #     role_dn="erglobalid=8395026297284492323,ou=roles,erglobalid=00000000000000000000,ou=demo,dc=com"
    # ))

    # # Get a container
    # print("Getting a container...")
    # pretty_print(isimws.isim.container.get(isim_application=isim_server, container_dn="erglobalid=00000000000000000000,ou=demo,dc=com"))
    #

    # # Search for people
    # print("Searching for people...")
    # pretty_print(isimws.isim.person.search(
    #     isim_application=isim_server,
    #     ldap_filter="(uid=cspeed)"
    # ))
    #
    # # Idempotently apply a person configuration
    # print("Applying a person configuration...")
    # pretty_print(isimws.isim.person.apply(isim_application=isim_server,
    #                                       container_path="//demo//lo::Sydney//ou::ou1//bp::testing",
    #                                       uid="djohnson",
    #                                       profile="Person",
    #                                       full_name="Darl Johnson",
    #                                       surname="Johnson",
    #                                       aliases=["Darl", "DJ"],
    #                                       password="Object99",
    #                                       roles=[
    #                                           ("//demo", "new-role"),
    #                                           ("//demo//lo::Sydney//ou::ou1//bp::testing", "Applied Role 78")
    #                                       ]))

    # # Get a person
    # print("Getting a person...")
    # pretty_print(isimws.isim.person.get(
    #     isim_application=isim_server,
    #     person_dn="erglobalid=1502785756771677767,ou=0,ou=people,erglobalid=00000000000000000000,ou=demo,dc=com"
    # ))
    #
    # Get a workflow
    # print("Getting a workflow...")
    # pretty_print(isimws.isim.workflow.get_attribute(
    #     isim_application=isim_server,
    #     workflow_dn="erglobalid=7338783908939776126,ou=workflow,erglobalid=00000000000000000000,ou=demo,dc=com",
    #     attribute_name="erprocessname"
    # ))

    # pretty_print(isimws.isim.workflow.search_attribute(
    #     isim_application=isim_server,
    #     container_dn="erglobalid=1509441815409121811,ou=orgChart,erglobalid=00000000000000000000,ou=demo,dc=com",
    #     ldap_filter="(erprocessname=*)",
    #     attribute_name="erglobalid"
    # ))

    # pretty_print(isimws.isim.workflow._get_attribute_by_filter(
    #     isim_application=isim_server,
    #     search_filter="(erparent=*)",
    #     attribute_name="erglobalid"
    # ))

    # # Get a container
    # print("Getting a container...")
    # pretty_print(isimws.isim.container.get(
    #     isim_application=isim_server,
    #     container_dn="erglobalid=2420248246759289552,ou=orgChart,erglobalid=00000000000000000000,ou=demo,dc=com"
    # ))
    #
    # print("Getting a container...")
    # pretty_print(isimws.isim.container.get(
    #     isim_application=isim_server,
    #     container_dn="ou=demo,dc=com"
    # ))

    # pretty_print(isimws.isim.container.get(isim_application=isim_server, container_dn="erglobalid=1510274102677986934,ou=orgChart,erglobalid=00000000000000000000,ou=demo,dc=com"))

    # Search for a container
    # print("Searching for a container...")
    # pretty_print(isimws.isim.container.search(
    #     isim_application=isim_server,
    #     parent_dn="erglobalid=2395356699390379214,ou=orgChart,erglobalid=00000000000000000000,ou=demo,dc=com",
    #     container_name="ad1",
    #     profile="AdminDomain",
    #     direct_children_only=True,
    #     exact_name_only=True
    # ))

    # Idempotently apply a container configuration
    print("Applying a container configuration...")
    pretty_print(isimws.isim.container.apply(isim_application=isim_server,
                                             parent_container_path="//",
                                             profile="Organization",
                                             name="org1",
                                             description="here's a description",
                                             associated_people=[
                                                 ('//demo//lo::Sydney//ou::ou1//bp::testing', 'cspeed'),
                                                 ('//demo//lo::Sydney//ou::ou1', 'bjones'),
                                                 ('//IBM', 'ayang')
                                             ]))

    print("Applying a container configuration...")
    pretty_print(isimws.isim.container.apply(isim_application=isim_server,
                                             parent_container_path="//demo",
                                             profile="OrganizationalUnit",
                                             name="ou1",
                                             description="here's a description",
                                             associated_people=[
                                                 ('//demo//lo::Sydney//ou::ou1//bp::testing', 'cspeed'),
                                                 ('//demo//lo::Sydney//ou::ou1', 'bjones'),
                                                 ('//IBM', 'ayang')
                                             ]))

    print("Applying a container configuration...")
    pretty_print(isimws.isim.container.apply(isim_application=isim_server,
                                             parent_container_path="//demo//ou::ou1",
                                             profile="Location",
                                             name="loc1",
                                             description="here's a description",
                                             associated_people=[
                                                 ('//demo//lo::Sydney//ou::ou1//bp::testing', 'cspeed'),
                                                 ('//demo//lo::Sydney//ou::ou1', 'bjones')
                                             ]))

    print("Applying a container configuration...")
    pretty_print(isimws.isim.container.apply(isim_application=isim_server,
                                             parent_container_path="//demo//ou::ou1//lo::loc1",
                                             profile="AdminDomain",
                                             name="ad1",
                                             description="here's a description",
                                             associated_people=[
                                                 ('//demo//lo::Sydney//ou::ou1//bp::testing', 'cspeed'),
                                                 ('//demo//lo::Sydney//ou::ou1', 'bjones')
                                             ]))

    print("Applying a container configuration...")
    pretty_print(isimws.isim.container.apply(isim_application=isim_server,
                                             parent_container_path="//demo//ou::ou1//lo::loc1//ad::ad1",
                                             profile="BPOrganization",
                                             name="bp1",
                                             description="here's a description",
                                             associated_people=[
                                                 ('//demo//lo::Sydney//ou::ou1//bp::testing', 'cspeed'),
                                                 ('//demo//lo::Sydney//ou::ou1', 'bjones')
                                             ]))

    # Modify a parent container after giving it a child
    print("Applying a container configuration...")
    pretty_print(isimws.isim.container.apply(isim_application=isim_server,
                                             parent_container_path="//demo//ou::ou1//lo::loc1",
                                             profile="AdminDomain",
                                             name="ad1",
                                             description="here's a description...",
                                             associated_people=[
                                                 ('//demo//lo::Sydney//ou::ou1//bp::testing', 'cspeed')
                                             ]))
