from imaplib import IMAP4, IMAP4_SSL
from typing import Any, List, Optional

from pydantic import BaseModel, PrivateAttr, SecretStr

from .exception import (
    AlreadyConnected,
    LoginFailed,
    MailboxAlreadyExists,
    MailboxFetchingFailed,
    MailboxNotFound,
    NotConnected,
)
from .mailbox import Mailbox, MailboxKind, mailbox_factory


class Account(BaseModel):
    username: str
    password: SecretStr

    _imap: IMAP4_SSL = PrivateAttr()
    _mailboxes: List[Mailbox] = PrivateAttr([])

    selected_mailbox: Optional[Mailbox] = None

    is_connected: bool = False

    gmail_imap_host: str = "imap.gmail.com"
    gmail_imap_port: int = 993

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

    def mailboxes(self, force: bool = True) -> List[Mailbox]:
        """
        Fetch all mailboxes

        :param force: Force the account to reload all mailboxes
        :raises NotConnected: If the user is not connected
        :raises MailboxFetchingFailed: If there is a problem with imap
        :return: The list of mailboxes
        """
        if not self.is_connected:
            raise NotConnected("You should be connected to perform this operation")

        if not self._mailboxes or force:
            status, raw_list = self._imap.list()

            if status != "OK":
                raise MailboxFetchingFailed("Unable to fetch mailboxes")

            self._mailboxes = [
                mailbox_factory(raw_mailbox_description, self)
                for raw_mailbox_description in raw_list
            ]

        return self._mailboxes

    def _mailboxes_from_attr(self, attr: str, value: Any) -> List[Mailbox]:
        """
        Retrieve mailboxes from an attribute

        :param attr: The attribute
        :param attr: The value expected from the attribute
        :return: The list of mailboxes
        """
        mailboxes = self.mailboxes()
        return [mailbox for mailbox in mailboxes if getattr(mailbox, attr) is value]

    def _mailbox_from_attr(self, attr: str, value: Any) -> List[Mailbox]:
        """
        Retrieve the first mailbox from an attribute

        :param attr: The attribute
        :param attr: The value expected from the attribute
        :return: The first mailbox
        """
        try:
            return self._mailboxes_from_attr(attr, value)[0]
        except IndexError:
            raise MailboxNotFound(f"Mailbox of {attr} {value} not found")

    def mailboxes_from_kind(self, kind: MailboxKind) -> List[Mailbox]:
        """
        Return mailboxes of a particular kind

        :param kind: The kind of mailbox
        :return: The list of mailboxes
        """
        return self._mailboxes_from_attr("kind", kind)

    def mailbox_from_kind(self, kind: MailboxKind) -> Mailbox:
        """
        Return a mailbox of a particular kind

        :param kind: The kind of mailbox
        :raises MailboxNotFound: If the mailbox is not found
        :return: The first mailbox of that kind
        """
        return self._mailbox_from_attr("kind", kind)

    def mailbox_from_path(self, path: str) -> Mailbox:
        """
        Return a mailbox of a particular path

        :param path: The path of mailbox
        :raises MailboxNotFound: If the mailbox is not found
        :return: The mailbox of that path
        """
        return self._mailbox_from_attr("path", path)

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

    def select_mailbox(self, mailbox: Mailbox):
        """
        Select a mailbox

        :param mailbox: The mailbox to select
        """
        self.selected_mailbox = mailbox
        self._imap.select(mailbox.path)

    def select_mailbox_from_path(self, path: str):
        """
        Select a mailbox from a path

        :param path: The path of tha mailbox
        """
        mailbox = self.mailbox_from_path(path)
        return self.select_mailbox(mailbox)

    def move_mailbox(self, mailbox: Mailbox, path: str):
        """
        Move a mailbox to another place

        :param mailbox: The mailbox to move
        :param path: The new path of the mailbox
        """
        if path == mailbox.path:
            return

        old_path = mailbox.path

        for mailbox in self.mailboxes():
            if mailbox.path == path:
                raise MailboxAlreadyExists(
                    f"A mailbox already exists at '{mailbox.path}'"
                )

        self._imap.rename(old_path, path)

        for mailbox in self.mailboxes():
            if mailbox.path.startswith(old_path):
                mailbox.path = mailbox.path.replace(old_path, path)
                mailbox.label = mailbox.path.split("/")[-1]

    def rename_mailbox(self, mailbox: Mailbox, label: str):
        """
        Rename a mailbox

        :param mailbox: The mailbox to rename
        :param path: The new label of the mailbox
        """
        parent_path = "/".join(mailbox.path.split("/")[0:-1])
        path = f"{parent_path}/{label}" if parent_path else label
        return self.move_mailbox(mailbox, path)
