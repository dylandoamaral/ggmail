from enum import Enum, auto
from typing import List

from pydantic import BaseModel, PrivateAttr

from .message import Message
from .policy import Policy
from .policy import all_ as all_policy
from .utf7 import decode


class MailboxKind(Enum):
    INBOX = auto()
    TRASH = auto()
    DRAFTS = auto()
    IMPORTANT = auto()
    SENT = auto()
    NOSELECT = auto()
    FLAGGED = auto()
    ALL = auto()
    JUNK = auto()
    CUSTOM = auto()


class Mailbox(BaseModel):
    label: str
    path: str
    kind: MailboxKind
    has_children: bool

    _account = PrivateAttr()

    def __init__(self, _account, **data):
        super().__init__(**data)
        self._account = _account

    def rename(self, label: str):
        """
        Rename the mailbox

        :param path: The new label of the mailbox
        """
        self._account.rename_mailbox(self, label)

    def move(self, path: str):
        """
        Move the mailbox, every nested mailbox of the mailbox will be moved with it

        :param path: The name of the new path
        """
        self._account.move_mailbox(self, path)

    def select(self):
        """
        Select the mailbox
        """
        self._account.select_mailbox(self)

    def search_uids(self, policy: Policy = all_policy) -> List[Message]:
        """
        Search all message uids from the mailbox according to the policy, the mailbox
        become the selected mailbox

        :param policy: The policy to fetch message uids, defaults to all_
        :return: The list of message uids
        """
        self.select()
        return self._account.search_message_uids(policy)

    def fetch(self, policy: Policy = all_policy) -> List[Message]:
        """
        Search all messages from the mailbox according to the policy, the mailbox become
        the selected mailbox

        :param policy: The policy to fetch messages, defaults to all_
        :return: The list of messages
        """
        self.select()
        return self._account.fetch_messages(policy)

    def search(self, policy: Policy = all_policy) -> List[Message]:
        """
        Alias of `ggmail.mailbox.Mailbox.fetch`
        """
        return self.fetch(policy)


def mailbox_factory(raw_mailbox_description: bytes, account) -> Mailbox:
    """
    Create a mailbox from a raw byte description of the mailbox

    :param raw_mailbox_description: The description of the mailbox
    :paam account: The account
    :return: The mailbox
    """
    mailbox_description = raw_mailbox_description.decode("utf8")
    mailbox_description = mailbox_description.replace('"', "")
    raw_tags, path = mailbox_description.split("/", 1)
    path = decode(path.strip())
    label = path.split("/")[-1]
    tags = raw_tags.replace(" ", "")[1:-1].split("\\")[1:]
    has_children = "HasChildren" in tags

    if label == "INBOX":
        kind = MailboxKind.INBOX
        label = "Inbox"
        path = "Inbox"
    else:
        kind_tag = [tag for tag in tags if tag not in ["HasChildren", "HasNoChildren"]]
        kind = MailboxKind.CUSTOM if not kind_tag else MailboxKind[kind_tag[0].upper()]

    return Mailbox(
        label=label,
        path=path,
        kind=kind,
        has_children=has_children,
        _account=account,
    )
