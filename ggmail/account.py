from imaplib import IMAP4, IMAP4_SSL
from typing import List

from pydantic import BaseModel, PrivateAttr, SecretStr

from .exception import (
    AlreadyConnected,
    LoginFailed,
    MailboxFetchingFailed,
    NotConnected,
)
from .mailbox import Mailbox, mailbox_factory


class Account(BaseModel):
    username: str
    password: SecretStr

    _imap: IMAP4_SSL = PrivateAttr()

    is_connected = False

    gmail_imap_host = "imap.gmail.com"
    gmail_imap_port = 993

    def __init__(self, **data):
        super().__init__(**data)
        self._imap = IMAP4_SSL(self.gmail_imap_host, self.gmail_imap_port)

    def login(self):
        """
        Login to the gmail account

        :raises AlreadyConnected: If the user is already connected
        :raises LoginFailed: If there is a problem with imap
        """
        if self.is_connected:
            raise AlreadyConnected("You are already connected")

        try:
            self._imap.login(self.username, self.password.get_secret_value())
        except IMAP4.error:
            raise LoginFailed(
                "Can't login to your email account, verify your credentials "
                "and ensure you granted access to less secure app."
            )
        self.is_connected = True

    def logout(self):
        """
        Logout from the gmail account

        :raises NotConnected: If the user is not connected
        """
        if not self.is_connected:
            raise NotConnected("You should be connected to perform this operation")

        self._imap.logout()
        self.is_connected = False

    def fetch_mailboxes(self) -> List[Mailbox]:
        """
        Fetch all mailboxes

        :raises NotConnected: If the user is not connected
        :raises MailboxFetchingFailed: If there is a problem with imap
        :return: The list of mailboxes
        """
        if not self.is_connected:
            raise NotConnected("You should be connected to perform this operation")

        status, raw_list = self._imap.list()

        if status != "OK":
            raise MailboxFetchingFailed("Unable to fetch mailboxes")

        return [
            mailbox_factory(raw_mailbox_description)
            for raw_mailbox_description in raw_list
        ]
