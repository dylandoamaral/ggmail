from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from ggmail.flag import Flag
from ggmail.message import (
    ContentType,
    Message,
    decode_content,
    decode_flags,
    decode_subject,
    get_content_type,
    message_factory,
)


class TestMessageStatus:
    @pytest.mark.parametrize(
        "flag,function",
        [
            pytest.param(Flag.ANSWERED, "is_answered", id="answered"),
            pytest.param(Flag.DELETED, "is_deleted", id="deleted"),
            pytest.param(Flag.DRAFT, "is_draft", id="draft"),
            pytest.param(Flag.FLAGGED, "is_starred", id="starred"),
            pytest.param(Flag.SEEN, "is_seen", id="seen"),
        ],
    )
    def test_status(self, flag, function):
        message = Message(
            from_="",
            to="",
            subject="",
            html="",
            body="",
            date=datetime.now(),
            content_type=ContentType.MULTIPART,
            flags=[flag],
        )

        assert getattr(message, function)() is True


class TestMessageDecoders:
    @patch("ggmail.message.decode_header")
    def test_decode_subject(self, decode_header_mock):
        decode_header_mock.return_value = [("Subject", None)]
        assert decode_subject("") == "Subject"

    def test_decode_content_text(self):
        message = Mock()
        message.get_content_maintype.return_value = "text"
        message.get_payload.return_value = "body"
        # message.walk.return_value = [sub_message]

        assert decode_content(message) == ("body", None)

    def test_decode_content_multipart(self):
        message_body = Mock()
        message_body.get_payload.return_value = "body"
        message_body.get_content_type.return_value = "text/plain"
        message_html = Mock()
        message_html.get_payload.return_value = "<html>body<\html>"
        message_html.get_content_type.return_value = "text/html"
        message = Mock()
        message.get_content_maintype.return_value = "multipart"
        message.walk.return_value = [message_body, message_html]

        assert decode_content(message) == ("body", "<html>body<\html>")

    def test_decode_flags(self):
        header = b"6 (FLAGS (\\Flagged \\Seen) BODY[] {5043}"
        flags = decode_flags(header)

        assert Flag.FLAGGED in flags
        assert Flag.SEEN in flags
        assert len(flags) == 2


class TestMessageFactory:
    @patch("ggmail.message.message_from_bytes")
    @patch("ggmail.message.decode_subject")
    @patch("ggmail.message.decode_content")
    @patch("ggmail.message.decode_flags")
    def test_message_factory(
        self, decode_flags_mock, decode_content_mock, decode_subject_mock, email_mock
    ):
        message_dict = {
            "From": "from@gmail.com",
            "To": "to@gmail.com",
            "Subject": "Subject",
            "Date": "Sat, 9 Oct 2021 18:27:26 +0200",
        }

        message = Mock()
        message.__getitem__ = Mock()
        message.__getitem__.side_effect = message_dict.__getitem__
        message.get_content_maintype.return_value = "multipart"

        decode_content_mock.return_value = "body", "<html>body<\html>"
        decode_subject_mock.return_value = "Subject"
        decode_flags_mock.return_value = []

        email_mock.return_value = message

        message = message_factory([b"", b""])

        assert message.subject == "Subject"
        assert message.from_ == "from@gmail.com"
        assert message.to == "to@gmail.com"
        assert message.body == "body"
        assert message.html == "<html>body<\html>"
        assert message.content_type is ContentType.MULTIPART

        assert message.date.year == 2021
        assert message.date.month == 10
        assert message.date.day == 9
        assert message.date.hour == 18
        assert message.date.minute == 27
        assert message.date.second == 26

    def test_get_content_type(self):
        assert get_content_type("text") is ContentType.TEXT
        assert get_content_type("multipart") is ContentType.MULTIPART
