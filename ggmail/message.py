import re
from datetime import datetime
from email import message_from_bytes
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime
from enum import Enum, auto
from imaplib import ParseFlags
from typing import List, Optional, Tuple

from pydantic import BaseModel, PrivateAttr

from .flag import Flag


class ContentType(Enum):
    MULTIPART = auto()
    TEXT = auto()


class Message(BaseModel):
    uid: str
    from_: str
    to: str
    subject: str
    body: str
    html: Optional[str]
    date: datetime
    content_type: ContentType
    flags: List[Flag]

    _account = PrivateAttr()

    def __init__(self, _account, **data):
        super().__init__(**data)
        self._account = _account

    def add_flag(self, flag: Flag):
        """
        Add the flag to the message

        :param flag: The flag to add
        """
        return self._account.add_flag_message(self, flag)

    def remove_flag(self, flag: Flag):
        """
        Remove the flag to the message

        :param flag: The flag to remove
        """
        return self._account.remove_flag_message(self, flag)

    def is_answered(self) -> bool:
        """
        Return if the message is answered

        :return: True if the message is answered, False else
        """
        return Flag.ANSWERED in self.flags

    def answer(self):
        """
        Add answered flag to the message
        """
        return self.add_flag(Flag.ANSWERED)

    def unanswer(self):
        """
        Remove answered flag to the message
        """
        return self.remove_flag(Flag.ANSWERED)

    def is_deleted(self) -> bool:
        """
        Return if the message is deleted

        :return: True if the message is deleted, False else
        """
        return Flag.DELETED in self.flags

    def delete(self):
        """
        Add delete flag to the message
        """
        return self.add_flag(Flag.DELETED)

    def undelete(self):
        """
        Remove delete flag to the message
        """
        return self.remove_flag(Flag.DELETED)

    def is_draft(self) -> bool:
        """
        Return if the message is draft

        :return: True if the message is draft, False else
        """
        return Flag.DRAFT in self.flags

    def draft(self):
        """
        Add draft flag to the message
        """
        return self.add_flag(Flag.DRAFT)

    def undraft(self):
        """
        Remove draft flag to the message
        """
        return self.remove_flag(Flag.DRAFT)

    def is_starred(self) -> bool:
        """
        Return if the message is starred

        :return: True if the message is starred, False else
        """
        return Flag.FLAGGED in self.flags

    def star(self):
        """
        Add flagged flag to the message
        """
        return self.add_flag(Flag.FLAGGED)

    def unstar(self):
        """
        Remove flagged flag to the message
        """
        return self.remove_flag(Flag.FLAGGED)

    def is_seen(self) -> bool:
        """
        Return if the message is seen

        :return: True if the message is seen, False else
        """
        return Flag.SEEN in self.flags

    def seen(self):
        """
        Add seen flag to the message
        """
        return self.add_flag(Flag.SEEN)

    def unseen(self):
        """
        Remove seen flag to the message
        """
        return self.remove_flag(Flag.SEEN)


def decode_subject(subject: str) -> str:
    """
    Decode the subject

    :param subject: The encoded subject
    :return: The decoded subject
    """
    pairs = decode_header(subject)
    strs = [string.decode(charset) if charset else string for string, charset in pairs]
    return "".join(strs)


def decode_content(message: Message) -> Tuple[str, Optional[str]]:
    """
    Decode the content giving the html and the body

    :param body: The message
    :return: The decoded body and html
    """
    body, html = None, None
    if message.get_content_maintype() == "multipart":
        for content in message.walk():
            if content.get_content_type() == "text/plain":
                body = content.get_payload(decode=True)
            elif content.get_content_type() == "text/html":
                html = content.get_payload(decode=True)
    elif message.get_content_maintype() == "text":
        body = message.get_payload()

    return body, html


def decode_flags(header: bytes) -> List[Flag]:
    """
    Decode flags from the header

    :param header: The header
    :return: The message flags
    """
    raw_flags = ParseFlags(header)
    return [Flag(flag.decode("utf8")) for flag in raw_flags]


def decode_uid(header: bytes) -> str:
    """
    Decode uid from the header

    :param header: The header
    :return: The uid
    """
    return re.search(r"UID (\d+)", header.decode("utf8")).groups(1)[0]


def get_content_type(content_type: str) -> ContentType:
    return ContentType.MULTIPART if content_type == "multipart" else ContentType.TEXT


def message_factory(raw_message_description: List[bytes], account) -> Message:
    """
    Create a message from a raw byte description of the message

    :param raw_message_description: The description of the message
    :paam account: The account
    :return: The message
    """
    raw_header, raw_message = raw_message_description
    message = message_from_bytes(raw_message)

    uid = decode_uid(raw_header)
    from_ = message["From"]
    to = message["To"]
    subject = decode_subject(message["Subject"])
    body, html = decode_content(message)
    date = parsedate_to_datetime(message["Date"])
    content_type = get_content_type(message.get_content_maintype())
    flags = decode_flags(raw_header)

    return Message(
        uid=uid,
        from_=from_,
        to=to,
        subject=subject,
        html=html,
        body=body,
        date=date,
        content_type=content_type,
        flags=flags,
        _account=account,
    )
