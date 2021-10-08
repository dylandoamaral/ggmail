from enum import Enum, auto

from pydantic import BaseModel

from .utf7 import decode


class MailboxKind(Enum):
    DRAFTS = auto()
    TRASH = auto()
    IMPORTANT = auto()
    SENT = auto()
    NOSELECT = auto()
    FLAGGED = auto()
    ALL = auto()
    JUNK = auto()
    INBOX = auto()
    CUSTOM = auto()


class Mailbox(BaseModel):
    label: str
    path: str
    kind: MailboxKind
    has_children: bool
    raw: bytes


def mailbox_factory(raw_mailbox_description: bytes) -> Mailbox:
    """
    Create a mailbox from a raw byte description of the mailbox

    :param raw_mailbox_description: The description of the mailbox
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
        raw=raw_mailbox_description,
    )
