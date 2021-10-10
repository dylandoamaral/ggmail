from datetime import datetime
from email import message_from_bytes
from email.header import decode_header
from email.message import Message as EmailMessage
from email.utils import parsedate_to_datetime
from enum import Enum, auto
from imaplib import ParseFlags
from typing import List, Optional, Tuple

from pydantic import BaseModel

from .flag import Flag


class ContentType(Enum):
    MULTIPART = auto()
    TEXT = auto()


class Message(BaseModel):
    from_: str
    to: str
    subject: str
    body: str
    html: Optional[str]
    date: datetime
    content_type: ContentType
    flags: List[Flag]

    def is_answered(self) -> bool:
        """
        Return if the message is answered

        :return: True if the message is answered, False else
        """
        return Flag.ANSWERED in self.flags

    def is_deleted(self) -> bool:
        """
        Return if the message is deleted

        :return: True if the message is deleted, False else
        """
        return Flag.DELETED in self.flags

    def is_draft(self) -> bool:
        """
        Return if the message is draft

        :return: True if the message is draft, False else
        """
        return Flag.DRAFT in self.flags

    def is_starred(self) -> bool:
        """
        Return if the message is starred

        :return: True if the message is starred, False else
        """
        return Flag.FLAGGED in self.flags

    def is_seen(self) -> bool:
        """
        Return if the message is seen

        :return: True if the message is seen, False else
        """
        return Flag.SEEN in self.flags


def decode_subject(subject: str) -> str:
    """
    Decode the subject

    :param subject: The encoded subject
    :return: The decoded subject
    """
    pairs = decode_header(subject)
    strs = [string.decode(charset) if charset else string for string, charset in pairs]
    return "".join(strs)


def decode_content(message: EmailMessage) -> Tuple[str, Optional[str]]:
    """
    Decode the content giving the html and the body

    :param message: The message
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
    return [Flag(flag.decode("utf8")[1:]) for flag in raw_flags]


def get_content_type(content_type: str) -> ContentType:
    return ContentType.MULTIPART if content_type == "multipart" else ContentType.TEXT


def message_factory(raw_message_description: List[bytes]) -> Message:
    message = message_from_bytes(raw_message_description[1])

    from_ = message["From"]
    to = message["To"]
    subject = decode_subject(message["Subject"])
    body, html = decode_content(message)
    date = parsedate_to_datetime(message["Date"])
    content_type = get_content_type(message.get_content_maintype())
    flags = decode_flags(raw_message_description[0])

    return Message(
        from_=from_,
        to=to,
        subject=subject,
        html=html,
        body=body,
        date=date,
        content_type=content_type,
        flags=flags,
    )
