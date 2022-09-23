from abc import ABC, abstractmethod
from imaplib import IMAP4

from pydantic import BaseModel, SecretStr

from .exception import LoginFailed


class Authentication(BaseModel, ABC):
    username: str
    host: str
    port: int

    @abstractmethod
    def login(self, imap: IMAP4):
        """
        Login to the account

        :param imap: the imap account instance
        :raises LoginFailed: If there is a problem with imap
        """


class Google(Authentication):
    password: SecretStr
    host: str = "imap.gmail.com"
    port: int = 993

    def login(self, imap: IMAP4):
        try:
            imap.login(self.username, self.password.get_secret_value())
        except IMAP4.error:
            raise LoginFailed(
                "Can't login to your email account, verify your credentials "
                "and ensure you granted access to less secure app."
            )


class GoogleOAuth2(Authentication):
    token: SecretStr
    host: str = "imap.gmail.com"
    port: int = 993

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

class Outlook(Authentication):
    password: SecretStr
    host: str = "outlook.office365.com"
    port: int = 993

    def login(self, imap: IMAP4):
        try:
            imap.login(self.username, self.password.get_secret_value())
        except IMAP4.error:
            raise LoginFailed(
                "Can't login to your email account, verify your credentials "
                "and ensure you granted access to less secure app."
            )