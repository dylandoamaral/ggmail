from imaplib import IMAP4, IMAP4_SSL
from typing import List

from pydantic import BaseModel, PrivateAttr, SecretStr

from .exception import (
    AlreadyConnected,
    LoginFailed,
    MailboxFetchingFailed,
    MailboxNotFound,
    NotConnected,
)
from .mailbox import Mailbox, MailboxKind, mailbox_factory


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

    def mailboxes_from_kind(self, kind: MailboxKind) -> List[Mailbox]:
        """
        Return mailboxes of a particular kind

        :param kind: The kind of mailbox
        :return: The list of mailboxes
        """
        mailboxes = self.fetch_mailboxes()
        return [mailbox for mailbox in mailboxes if mailbox.kind is kind]

    def mailbox_from_kind(self, kind: MailboxKind) -> Mailbox:
        """
        Return a mailbox of a particular kind

        :param kind: The kind of mailbox
        :raises MailboxNotFound: If the mailbox is not found
        :return: The first mailbox of that kind
        """
        try:
            return self.mailboxes_from_kind(kind)[0]
        except IndexError:
            raise MailboxNotFound(f"Mailbox of kind {kind} not found")

    def inbox(self) -> Mailbox:
        """
        Return inbox mailbox

        :return: The inbox mailbox
        """
        return self.mailbox_from_kind(MailboxKind.INBOX)

    def trash(self) -> Mailbox:
        """
        Return trash mailbox

        :return: The trash mailbox
        """
        return self.mailbox_from_kind(MailboxKind.TRASH)

    def drafts(self) -> Mailbox:
        """
        Return drafts mailbox

        :return: The drafts mailbox
        """
        return self.mailbox_from_kind(MailboxKind.DRAFTS)

    def important(self) -> Mailbox:
        """
        Return important mailbox

        :return: The important mailbox
        """
        return self.mailbox_from_kind(MailboxKind.IMPORTANT)

    def sent(self) -> Mailbox:
        """
        Return important mailbox

        :return: The important mailbox
        """
        return self.mailbox_from_kind(MailboxKind.SENT)

    def no_select(self) -> Mailbox:
        """
        Return no select mailbox

        :return: The no select mailbox
        """
        return self.mailbox_from_kind(MailboxKind.NOSELECT)

    def flagged(self) -> Mailbox:
        """
        Return flagged mailbox

        :return: The flagged mailbox
        """
        return self.mailbox_from_kind(MailboxKind.FLAGGED)

    def all_(self) -> Mailbox:
        """
        Return all mailbox

        :return: The all mailbox
        """
        return self.mailbox_from_kind(MailboxKind.ALL)

    def junk(self) -> Mailbox:
        """
        Return junk mailbox

        :return: The junk mailbox
        """
        return self.mailbox_from_kind(MailboxKind.JUNK)

    def customs(self) -> List[Mailbox]:
        """
        Return custom mailboxes

        :return: The custom mailboxes
        """
        return self.mailboxes_from_kind(MailboxKind.CUSTOM)
