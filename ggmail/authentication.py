from abc import ABC, abstractmethod
from imaplib import IMAP4

from pydantic import BaseModel, SecretStr

from .exception import LoginFailed


class Authentication(BaseModel, ABC):
    @abstractmethod
    def login(self, imap: IMAP4):
        """
        Login to the account

        :param imap: the imap account instance
        :raises LoginFailed: If there is a problem with imap
        """


class Login(Authentication):
    username: str
    password: SecretStr

    def login(self, imap: IMAP4):
        try:
            imap.login(self.username, self.password.get_secret_value())
        except IMAP4.error:
            raise LoginFailed(
                "Can't login to your email account, verify your credentials "
                "and ensure you granted access to less secure app."
            )


class OAuth2(Authentication):
    username: str
    token: SecretStr

    def login(self, imap: IMAP4):
        try:
            user = self.username
            token = self.token.get_secret_value()
            auth_string = "user=%s\1auth=Bearer %s\1\1" % (user, token)
            imap.authenticate("XOAUTH2", lambda x: auth_string)
        except IMAP4.error:
            raise LoginFailed(
                "Can't login to your email account, verify your credentials "
                "and ensure you granted access using gcp."
            )
