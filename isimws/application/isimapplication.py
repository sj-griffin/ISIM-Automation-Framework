import json
import requests
# from requests.packages.urllib3.exceptions import InsecureRequestWarning
import logging
from .ibmappliance import IBMAppliance
from .ibmappliance import IBMError
from .ibmappliance import IBMFatal
from ibmsecurity.utilities import tools

try:
    basestring
except NameError:
    basestring = (str, bytes)


class ISIMApplication:
    def __init__(self, hostname, user, port=9082):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating an ISIMApplication')
        if isinstance(port, basestring):
            self.lmi_port = int(port)
        else:
            self.port = port
        self.session = requests.session()
        self.session.auth = (user.username, user.password)
        self.hostname = hostname
        self.user = user