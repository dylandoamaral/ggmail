from imaplib import IMAP4, IMAP4_SSL
from typing import Any, List, Optional

from pydantic import BaseModel, PrivateAttr, SecretStr

from .exception import (
    AlreadyConnected,
    FlagAlreadyAttached,
    FlagNotAttached,
    LoginFailed,
    MailboxAlreadyExists,
    MailboxFetchingFailed,
    MailboxNotDeletable,
    MailboxNotFound,
    MessageFetchingFailed,
    MessageSearchingFailed,
    NotConnected,
)
from .flag import Flag
from .mailbox import Mailbox, MailboxKind, mailbox_factory
from .message import Message, message_factory
from .policy import Policy
from .policy import all_ as all_policy


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

    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.logout()

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
        self._check_is_connected()

        self._imap.logout()
        self.is_connected = False

    def _check_path_empty(self, path: str):
        """
        Assert that the target path is free

        :param path: The targeted path
        """
        for mailbox in self.mailboxes():
            if mailbox.path == path:
                raise MailboxAlreadyExists(
                    f"A mailbox already exists at '{mailbox.path}'"
                )

    def _check_is_connected(self):
        """
        Assert that the account is connected
        """
        if not self.is_connected:
            raise NotConnected("You should be connected to perform this operation")

    def mailboxes(self, force: bool = True) -> List[Mailbox]:
        """
        Fetch all mailboxes

        :param force: Force the account to reload all mailboxes
        :raises NotConnected: If the user is not connected
        :raises MailboxFetchingFailed: If there is a problem with imap
        :return: The list of mailboxes
        """
        self._check_is_connected()

        if not self._mailboxes and force:
            status, raw_response = self._imap.list()

            if status != "OK":
                raise MailboxFetchingFailed("Unable to fetch mailboxes")

            self._mailboxes = [
                mailbox_factory(raw_mailbox_description, self)
                for raw_mailbox_description in raw_response
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
        return [mailbox for mailbox in mailboxes if getattr(mailbox, attr) == value]

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

    def expunge(self):
        """
        Permanently delete messages that have the Deleted flag.
        """
        self._imap.expunge()

    def select_mailbox(self, mailbox: Mailbox):
        """
        Select a mailbox

        :param mailbox: The mailbox to select
        :raises NotConnected: If the user is not connected
        """
        self._check_is_connected()

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
        :raises NotConnected: If the user is not connected
        :raises MailboxAlreadyExists: If the mailbox already exists for the path
        """
        if path == mailbox.path:
            return

        self._check_is_connected()
        self._check_path_empty(path)

        old_path = mailbox.path

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

    def create_mailbox(self, path: str) -> Mailbox:
        """
        Create a mailbox from a path

        :param path: The path of the mailbox to create
        :return: The newly mailbox
        """
        self._check_is_connected()
        self._check_path_empty(path)

        mailbox = Mailbox(
            label=path.split("/")[-1],
            path=path,
            kind=MailboxKind.CUSTOM,
            has_children=False,
            _account=self,
        )

        self._mailboxes.append(mailbox)
        self._imap.create(path)

        return mailbox

    def delete_mailbox(self, mailbox: Mailbox):
        """
        Delete a particular mailbox

        :param path: The mailbox to delete
        """
        self._check_is_connected()

        if mailbox.kind is not MailboxKind.CUSTOM:
            raise MailboxNotDeletable("You can't delete a not custom mailbox")

        try:
            self._mailboxes = self.mailboxes().remove(mailbox)
            self._imap.delete(mailbox.path)
        except ValueError:
            raise MailboxNotFound(f"The mailbox {mailbox.path} is not found")

    def delete_mailbox_from_path(self, path: str):
        """
        Delete a particular mailbox from path

        :param path: The path of the mailbox to delete
        """
        mailbox = self.mailbox_from_path(path)
        return self.delete_mailbox(mailbox)

    def search_message_uids(self, policy: Policy = all_policy) -> List[str]:
        """
        Search all message ids from the selected mailbox according to the policy

        :param policy: The policy to fetch message, defaults to all_
        :raises NotConnected: If the user is not connected
        :return: The list of ids
        """
        self._check_is_connected()

        status, raw_response = self._imap.uid("SEARCH", None, policy.to_imap_standard())

        if status != "OK":
            raise MessageSearchingFailed("Unable to retrieve message uids")

        raw_list = raw_response[0].decode("utf8").split(" ")

        if raw_list == [""]:
            return []

        return [n for n in raw_list]

    def fetch_messages(self, policy: Policy = all_policy) -> List[Message]:
        """
        Search all messages from the selected mailbox according to the policy

        :param policy: The policy to fetch message, defaults to all_
        :raises NotConnected: If the user is not connected
        :return: The list of messages
        """
        self._check_is_connected()

        message_uids = self.search_message_uids(policy)

        if not message_uids:
            return []

        status, raw_response = self._imap.fetch(
            ",".join(message_uids), "(BODY.PEEK[] FLAGS)"
        )

        if status != "OK":
            raise MessageFetchingFailed("Unable to fetch messages")

        raw_messages = [
            raw_message_description
            for (index, raw_message_description) in enumerate(raw_response)
            if index % 2 == 0
        ]

        return [
            message_factory(uid, raw_message_description, self)
            for (uid, raw_message_description) in zip(message_uids, raw_messages)
        ]

    def search_messages(self, policy: Policy = all_policy) -> List[Message]:
        """
        Alias of `ggmail.account.Account.fetch_messages`
        """
        return self.fetch_messages(policy)

    def copy_message(self, message: Message, mailbox: Mailbox):
        """
        Copy a message to another mailbox

        :param message: The message to copy
        :param mailbox: The mailbox containing the new copy
        """
        self.copy_message_using_uid(message.uid, mailbox)

    def copy_messages(self, messages: List[Message], mailbox: Mailbox):
        """
        Copy messages to another mailbox

        :param messages: The messages to copy
        :param mailbox: The mailbox containing the new copy
        """
        uids = [message.uid for message in messages]
        self.copy_messages_using_uids(uids, mailbox)

    def copy_message_using_uid(self, uid: str, mailbox: Mailbox):
        """
        Copy a message to another mailbox using its uid

        :param uid: The message's uid
        :param mailbox: The mailbox containing the new copy
        :raises NotConnected: If the user is not connected
        """
        self._check_is_connected()
        self._imap.uid("COPY", uid, mailbox.path)

    def copy_messages_using_uids(self, uids: List[str], mailbox: Mailbox):
        """
        Copy message to another mailbox using their uids

        :param uids: The message's uids
        :param mailbox: The mailbox containing the new copy
        :raises NotConnected: If the user is not connected
        """
        self._check_is_connected()
        self._imap.uid("COPY", ",".join(uids), mailbox.path)

    def move_message(
        self, message: Message, mailbox: Mailbox, with_expunge: bool = False
    ):
        """
        Move a message to another mailbox, if you don't set with_expunge to True, you
        will still see the mail in the source mailbox.

        :param message: The message to move
        :param mailbox: The other mailbox
        :param with_expunge: True if you permanently delete the message from the source,
                             False else
        :raises NotConnected: If the user is not connected
        """
        self.move_message_using_uid(message.uid, mailbox, with_expunge)
        message.flags.append(Flag.DELETED)

    def move_messages(
        self, messages: List[Message], mailbox: Mailbox, with_expunge: bool = False
    ):
        """
        Move messages to another mailbox, if you don't set with_expunge to True, you
        will still see the mail in the source mailbox.

        :param messages: The messages to move
        :param mailbox: The other mailbox
        :param with_expunge: True if you permanently delete the message from the source,
                             False else
        :raises NotConnected: If the user is not connected
        """
        uids = [message.uid for message in messages]
        self.move_messages_using_uids(uids, mailbox, with_expunge)
        for message in messages:
            message.flags.append(Flag.DELETED)

    def move_message_using_uid(
        self, uid: str, mailbox: Mailbox, with_expunge: bool = False
    ):
        """
        Move a message to another mailbox using its uid, if you don't set with_expunge
        to True, you will still see the mail in the source mailbox.

        :param uid: The message's uid
        :param mailbox: The mailbox containing the new copy
        :param with_expunge: True if you permanently delete the message from the source,
                             False else
        :raises NotConnected: If the user is not connected
        """
        self.copy_message_using_uid(uid, mailbox)
        self.add_flag_message_using_uid(uid, Flag.DELETED)
        if with_expunge:
            self.expunge()

    def move_messages_using_uids(
        self, uids: List[str], mailbox: Mailbox, with_expunge: bool = False
    ):
        """
        Move messages to another mailbox using their uids, if you don't set
        with_expunge to True, you will still see the mail in the source mailbox.

        :param uids: The message's uids
        :param mailbox: The mailbox containing the new copy
        :param with_expunge: True if you permanently delete the message from the source,
                             False else
        :raises NotConnected: If the user is not connected
        """
        self.copy_messages_using_uids(uids, mailbox)
        self.add_flag_messages_using_uids(uids, Flag.DELETED)
        if with_expunge:
            self.expunge()

    def add_flag_message(self, message: Message, flag: Flag, using_uid: bool = True):
        """
        Add a flag to the message

        :param message: The message to update
        :param flag: The flag to add

        :raises NotConnected: If the user is not connected
        """
        if flag in message.flags:
            raise FlagAlreadyAttached(
                f"The flag {flag} is already attached to the message with the uid "
                f"{message.uid}"
            )

        self.add_flag_message_using_uid(message.uid, flag)
        self._imap.uid("STORE", message.uid, "+FLAGS", flag.value)

        message.flags.append(flag)

    def add_flag_messages(self, messages: List[Message], flag: Flag):
        """
        Add a flag to all messages

        :param messages: The messages to update
        :param flag: The flag to add
        :raises NotConnected: If the user is not connected
        """
        for message in messages:
            if flag in message.flags:
                raise FlagAlreadyAttached(
                    f"The flag {flag} is already attached to the message with the uid "
                    f"{message.uid}"
                )

        uids = [message.uid for message in messages]
        self.add_flag_messages_using_uids(uids, flag)

        for message in messages:
            message.flags.append(flag)

    def add_flag_message_using_uid(self, uid: str, flag: Flag):
        """
        Add a flag to the message using its uid

        :param uid: The message's uid
        :param flag: The flag to add
        :raises NotConnected: If the user is not connected
        """
        self._check_is_connected()
        self._imap.uid("STORE", uid, "+FLAGS", flag.value)

    def add_flag_messages_using_uids(self, uids: List[str], flag: Flag):
        """
        Add a flag to all messages referenced by one of the uids

        :param uids: The message's uids
        :param flag: The flag to add
        :raises NotConnected: If the user is not connected
        """
        self._check_is_connected()
        self._imap.uid("STORE", ",".join(uids), "+FLAGS", flag.value)

    def remove_flag_message(self, message: Message, flag: Flag):
        """
        Remove a flag from the message

        :param message: The message to update
        :param flag: The flag to remove
        :raises NotConnected: If the user is not connected
        :raises FlagAlreadyAttached: If the flag is not attached
        """
        self._check_is_connected()

        if flag not in message.flags:
            raise FlagNotAttached(
                f"The flag {flag} not attached to the message with the uid "
                f"{message.uid}"
            )

        self.remove_flag_message_using_uid(message.uid, flag)

        message.flags.remove(flag)

    def remove_flag_messages(self, messages: List[Message], flag: Flag):
        """
        Remove a flag to all messages

        :param messages: The messages to remove
        :param flag: The flag to add
        :raises NotConnected: If the user is not connected
        """
        self._check_is_connected()

        for message in messages:
            if flag not in message.flags:
                raise FlagNotAttached(
                    f"The flag {flag} is already attached to the message with the uid "
                    f"{message.uid}"
                )

        uids = [message.uid for message in messages]
        self.remove_flag_messages_using_uids(uids, flag)

        for message in messages:
            message.flags.remove(flag)

    def remove_flag_message_using_uid(self, uid: str, flag: Flag):
        """
        Remove a flag to the message using its uid

        :param uid: The message's uid
        :param flag: The flag to add
        :raises NotConnected: If the user is not connected
        """
        self._check_is_connected()
        self._imap.uid("STORE", uid, "-FLAGS", flag.value)

    def remove_flag_messages_using_uids(self, uids: List[str], flag: Flag):
        """
        Remove a flag to all messages referenced by one of the uids

        :param uids: The message's uids
        :param flag: The flag to add
        :raises NotConnected: If the user is not connected
        """
        self._check_is_connected()
        self._imap.uid("STORE", ",".join(uids), "-FLAGS", flag.value)
