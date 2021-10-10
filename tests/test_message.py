from datetime import datetime
from imaplib import IMAP4_SSL
from unittest.mock import ANY, Mock, call, patch

import pytest
from pytest import raises

from ggmail.exception import FlagAlreadyAttached, FlagNotAttached
from ggmail.flag import Flag
from ggmail.message import (
    ContentType,
    Message,
    decode_content,
    decode_flags,
    decode_subject,
    decode_uid,
    get_content_type,
    message_factory,
)


class TestMessageFlag:
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
    def test_check_flag(self, flag, function):
        message = Message(
            uid="",
            from_="",
            to="",
            subject="",
            html="",
            body="",
            date=datetime.now(),
            content_type=ContentType.MULTIPART,
            flags=[flag],
            _account=Mock(),
        )

        assert getattr(message, function)() is True

    @patch.object(IMAP4_SSL, "uid")
    @pytest.mark.parametrize(
        "flag,function",
        [
            pytest.param(Flag.ANSWERED, "answer", id="answered"),
            pytest.param(Flag.DELETED, "delete", id="deleted"),
            pytest.param(Flag.DRAFT, "draft", id="draft"),
            pytest.param(Flag.FLAGGED, "star", id="starred"),
            pytest.param(Flag.SEEN, "seen", id="seen"),
        ],
    )
    def test_add_flag(self, imap_uid_mock, flag, function, logged_account):
        message = Message(
            uid="",
            from_="",
            to="",
            subject="",
            html="",
            body="",
            date=datetime.now(),
            content_type=ContentType.MULTIPART,
            flags=[],
            _account=logged_account,
        )

        getattr(message, function)()
        assert message.flags == [flag]

    @patch.object(IMAP4_SSL, "uid")
    def test_add_flag_already_attached(self, imap_uid_mock, logged_account):
        message = Message(
            uid="",
            from_="",
            to="",
            subject="",
            html="",
            body="",
            date=datetime.now(),
            content_type=ContentType.MULTIPART,
            flags=[Flag.FLAGGED],
            _account=logged_account,
        )

        with raises(FlagAlreadyAttached):
            message.star()

    @patch.object(IMAP4_SSL, "uid")
    @pytest.mark.parametrize(
        "flag,function",
        [
            pytest.param(Flag.ANSWERED, "unanswer", id="answered"),
            pytest.param(Flag.DELETED, "undelete", id="deleted"),
            pytest.param(Flag.DRAFT, "undraft", id="draft"),
            pytest.param(Flag.FLAGGED, "unstar", id="starred"),
            pytest.param(Flag.SEEN, "unseen", id="seen"),
        ],
    )
    def test_remove_flag(self, imap_uid_mock, flag, function, logged_account):
        message = Message(
            uid="",
            from_="",
            to="",
            subject="",
            html="",
            body="",
            date=datetime.now(),
            content_type=ContentType.MULTIPART,
            flags=[flag],
            _account=logged_account,
        )

        getattr(message, function)()
        assert message.flags == []

    @patch.object(IMAP4_SSL, "uid")
    def test_remove_flag_not_attached(self, imap_uid_mock, logged_account):
        message = Message(
            uid="",
            from_="",
            to="",
            subject="",
            html="",
            body="",
            date=datetime.now(),
            content_type=ContentType.MULTIPART,
            flags=[],
            _account=logged_account,
        )

        with raises(FlagNotAttached):
            message.unstar()


class TestMoveMessage:
    @patch.object(IMAP4_SSL, "uid")
    def test_copy_message(self, imap_uid_mock, logged_account):
        message = Message(
            uid="1",
            from_="",
            to="",
            subject="",
            html="",
            body="",
            date=datetime.now(),
            content_type=ContentType.MULTIPART,
            flags=[],
            _account=logged_account,
        )
        mailbox = Mock()
        mailbox.path = "Mailbox"

        message.copy(mailbox)

        imap_uid_mock.assert_called_once_with("Copy", "1", "Mailbox")

    @patch.object(IMAP4_SSL, "uid")
    def test_move_message(self, imap_uid_mock, logged_account):
        message = Message(
            uid="1",
            from_="",
            to="",
            subject="",
            html="",
            body="",
            date=datetime.now(),
            content_type=ContentType.MULTIPART,
            flags=[],
            _account=logged_account,
        )
        mailbox = Mock()
        mailbox.path = "Mailbox"

        message.move(mailbox)

        imap_uid_mock.has_calls([call("Copy", "1", "Mailbox")])
        assert Flag.DELETED in message.flags

    @patch.object(IMAP4_SSL, "uid")
    @patch.object(IMAP4_SSL, "expunge")
    def test_move_message_with_expunge(
        self, imap_expunge_mock, imap_uid_mock, logged_account
    ):
        message = Message(
            uid="1",
            from_="",
            to="",
            subject="",
            html="",
            body="",
            date=datetime.now(),
            content_type=ContentType.MULTIPART,
            flags=[],
            _account=logged_account,
        )
        mailbox = Mock()
        mailbox.path = "Mailbox"

        message.move(mailbox, with_expunge=True)

        imap_uid_mock.has_calls([call("Copy", "1", "Mailbox")])
        imap_expunge_mock.assert_called_once()
        assert Flag.DELETED in message.flags


class TestMessageDecoders:
    @patch("ggmail.message.decode_header")
    def test_decode_subject(self, decode_header_mock):
        decode_header_mock.return_value = [("Subject", None)]
        assert decode_subject("") == "Subject"

    def test_decode_content_text(self):
        message = Mock()
        message.get_content_maintype.return_value = "text"
        message.get_payload.return_value = "body"

        assert decode_content(message) == ("body", None)

    def test_decode_content_multipart(self):
        message_body = Mock()
        message_body.get_payload.return_value = "body"
        message_body.get_content_type.return_value = "text/plain"
        message_html = Mock()
        message_html.get_payload.return_value = r"<html>body<\html>"
        message_html.get_content_type.return_value = "text/html"
        message = Mock()
        message.get_content_maintype.return_value = "multipart"
        message.walk.return_value = [message_body, message_html]

        assert decode_content(message) == ("body", r"<html>body<\html>")

    def test_decode_flags(self):
        header = b"6 (FLAGS (\\Flagged \\Seen) BODY[] {5043}"
        flags = decode_flags(header)

        assert Flag.FLAGGED in flags
        assert Flag.SEEN in flags
        assert len(flags) == 2

    def test_decode_uid(self):
        header = b"6 (UID 24"
        uid = decode_uid(header)

        assert uid == "24"


class TestMessageFactory:
    @patch("ggmail.message.message_from_bytes")
    @patch("ggmail.message.decode_subject")
    @patch("ggmail.message.decode_content")
    @patch("ggmail.message.decode_flags")
    @patch("ggmail.message.decode_uid")
    def test_message_factory(
        self,
        decode_uid_mock,
        decode_flags_mock,
        decode_content_mock,
        decode_subject_mock,
        email_mock,
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

        decode_content_mock.return_value = "body", r"<html>body<\html>"
        decode_subject_mock.return_value = "Subject"
        decode_flags_mock.return_value = []
        decode_uid_mock.return_value = "1"

        email_mock.return_value = message

        message = message_factory([b"", b""], ANY)

        assert message.uid == "1"
        assert message.subject == "Subject"
        assert message.from_ == "from@gmail.com"
        assert message.to == "to@gmail.com"
        assert message.body == "body"
        assert message.html == r"<html>body<\html>"
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
