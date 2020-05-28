import logging


class ISIMApplicationUser:
    super_user = "itim manager"

    def __init__(self, password: str, username: str = None):
        self.logger = logging.getLogger(__name__)
        self.logger.debug('Creating a user')

        if username is None:
            self.username = self.super_user
            self.logger.debug('Creating a super-user')
        else:
            self.username = username
        self.password = password
