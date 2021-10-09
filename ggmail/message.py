from datetime import datetime
from email import message_from_bytes
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime
from enum import Enum, auto
from typing import List, Optional, Tuple

from pydantic import BaseModel


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

    return Message(
        from_=from_,
        to=to,
        subject=subject,
        html=html,
        body=body,
        date=date,
        content_type=content_type,
    )
