from imaplib import IMAP4
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from ggmail.account import Account
from ggmail.exception import (
    AlreadyConnected,
    LoginFailed,
    MailboxFetchingFailed,
    MailboxNotFound,
    NotConnected,
)
from ggmail.mailbox import Mailbox, MailboxKind


@fixture
@patch("ggmail.account.IMAP4_SSL")
def account(imap_mock):
    return Account(username="test@gmail.com", password="secret")


@fixture
def logged_account(account):
    account.login()
    return account


class TestAccount:
    def test_login_success(self, account):
        account.login()
        assert account.is_connected == True

    def test_login_already_connected(self, account):
        account.login()

        with raises(AlreadyConnected):
            account.login()

    @patch("ggmail.account.IMAP4_SSL")
    def test_login_imap_error(self, imap_mock):
        imap_mock.return_value.login.side_effect = IMAP4.error()
        account = Account(username="test@gmail.com", password="secret")

        with raises(LoginFailed):
            account.login()

    def test_logout_success(self, logged_account):
        logged_account.logout()
        assert logged_account.is_connected == False

    def test_logout_not_connected(self, account):
        with raises(NotConnected):
            account.logout()

    @patch("ggmail.account.Account._imap")
    def test_fetch_mailboxes_success(self, imap_instance_mock, logged_account):
        imap_instance_mock.list.return_value = "OK", [
            b'(\\HasNoChildren) "/" "Custom"',
            b'(\\HasNoChildren) "/" "INBOX"',
            b'(\\HasNoChildren \\Junk) "/" "[Gmail]/Spam"',
        ]

        mailboxes = logged_account.fetch_mailboxes()
        assert len(mailboxes) == 3

    @patch("ggmail.account.Account._imap")
    def test_fetch_mailboxes_ko(self, imap_instance_mock, logged_account):
        imap_instance_mock.list.return_value = "KO", []

        with raises(MailboxFetchingFailed):
            logged_account.fetch_mailboxes()

    def test_fetch_mailboxes_not_connected(self, account):
        with raises(NotConnected):
            account.fetch_mailboxes()

    @patch("ggmail.account.Account.fetch_mailboxes")
    @pytest.mark.parametrize(
        "kind,function",
        [
            pytest.param(MailboxKind.INBOX, "inbox", id="inbox"),
            pytest.param(MailboxKind.TRASH, "trash", id="trash"),
            pytest.param(MailboxKind.DRAFTS, "drafts", id="drafts"),
            pytest.param(MailboxKind.IMPORTANT, "important", id="important"),
            pytest.param(MailboxKind.SENT, "sent", id="sent"),
            pytest.param(MailboxKind.NOSELECT, "no_select", id="no_select"),
            pytest.param(MailboxKind.FLAGGED, "flagged", id="flagged"),
            pytest.param(MailboxKind.JUNK, "junk", id="junk"),
            pytest.param(MailboxKind.ALL, "all_", id="all"),
        ],
    )
    def test_mailbox_with_kind(self, fetch_mailboxes_mock, account, kind, function):
        mailbox = Mailbox(label="T", path="P/T", kind=kind, has_children=False, raw=b"")
        fetch_mailboxes_mock.return_value = [mailbox]
        assert getattr(account, function)().kind is kind

    @patch("ggmail.account.Account.fetch_mailboxes")
    def test_customs(self, fetch_mailboxes_mock, account):
        fetch_mailboxes_mock.return_value = [
            Mailbox(
                label="T",
                path="P/T",
                kind=MailboxKind.CUSTOM,
                has_children=False,
                raw=b"",
            ),
            Mailbox(
                label="A",
                path="B/A",
                kind=MailboxKind.CUSTOM,
                has_children=False,
                raw=b"",
            ),
            Mailbox(
                label="C",
                path="D/C",
                kind=MailboxKind.INBOX,
                has_children=False,
                raw=b"",
            ),
        ]
        assert len(account.customs()) == 2

    @patch("ggmail.account.Account.fetch_mailboxes")
    def test_mailbox_from_kind_not_found(self, fetch_mailboxes_mock, account):
        fetch_mailboxes_mock.return_value = []
        with raises(MailboxNotFound):
            account.mailbox_from_kind(MailboxKind.ALL)
