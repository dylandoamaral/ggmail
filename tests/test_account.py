from imaplib import IMAP4
from unittest.mock import patch

from pytest import fixture, raises

from ggmail.account import Account
from ggmail.exception import (
    AlreadyConnected,
    LoginFailed,
    MailboxFetchingFailed,
    NotConnected,
)


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
