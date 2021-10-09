from imaplib import IMAP4, IMAP4_SSL
from unittest.mock import patch

import pytest
from pytest import fixture, raises

from ggmail.account import Account
from ggmail.exception import (
    AlreadyConnected,
    LoginFailed,
    MailboxAlreadyExists,
    MailboxFetchingFailed,
    MailboxNotFound,
    NotConnected,
)
from ggmail.mailbox import Mailbox, MailboxKind


@fixture
@patch.object(IMAP4_SSL, "login")
def logged_account(imap_login_mock, account):
    account.login()
    return account


class TestAccountLogin:
    @patch.object(IMAP4_SSL, "login")
    def test_login_success(self, imap_login_mock, account):
        account.login()
        assert account.is_connected == True

    @patch.object(IMAP4_SSL, "login")
    def test_login_already_connected(self, imap_login_mock, account):
        account.login()

        with raises(AlreadyConnected):
            account.login()

    @patch.object(IMAP4_SSL, "login")
    def test_login_imap_error(self, imap_login_mock):
        imap_login_mock.side_effect = IMAP4.error()
        account = Account(username="test@gmail.com", password="secret")

        with raises(LoginFailed):
            account.login()


class TestAccountLogout:
    def test_logout_success(self, logged_account):
        logged_account.logout()
        assert logged_account.is_connected == False

    def test_logout_not_connected(self, account):
        with raises(NotConnected):
            account.logout()


class TestAccountMailboxes:
    @patch.object(IMAP4_SSL, "list")
    def test_mailboxes_success(self, imap_list_mock, logged_account):
        imap_list_mock.return_value = "OK", [
            b'(\\HasNoChildren) "/" "Custom"',
            b'(\\HasNoChildren) "/" "INBOX"',
            b'(\\HasNoChildren \\Junk) "/" "[Gmail]/Spam"',
        ]

        mailboxes = logged_account.mailboxes()
        assert len(mailboxes) == 3

    @patch.object(IMAP4_SSL, "list")
    def test_mailboxes_ko(self, imap_list_mock, logged_account):
        imap_list_mock.return_value = "KO", []

        with raises(MailboxFetchingFailed):
            logged_account.mailboxes()

    def test_mailboxes_not_connected(self, account):
        with raises(NotConnected):
            account.mailboxes()

    @patch.object(Account, "mailboxes")
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
    def test_mailbox_with_kind(self, account_mailboxes_mock, account, kind, function):
        mailbox = Mailbox(
            label="T",
            path="T",
            kind=kind,
            has_children=False,
            raw=b"",
            _account=account,
        )
        account_mailboxes_mock.return_value = [mailbox]
        assert getattr(account, function)().kind is kind

    @patch.object(Account, "mailboxes")
    def test_customs(self, account_mailboxes_mock, account):
        account_mailboxes_mock.return_value = [
            Mailbox(
                label="T",
                path="T",
                kind=MailboxKind.CUSTOM,
                has_children=False,
                raw=b"",
                _account=account,
            ),
            Mailbox(
                label="A",
                path="A",
                kind=MailboxKind.CUSTOM,
                has_children=False,
                raw=b"",
                _account=account,
            ),
            Mailbox(
                label="C",
                path="C",
                kind=MailboxKind.INBOX,
                has_children=False,
                raw=b"",
                _account=account,
            ),
        ]
        assert len(account.customs()) == 2

    @patch.object(Account, "mailboxes")
    def test_mailbox_from_kind_not_found(self, account_mailboxes_mock, account):
        account_mailboxes_mock.return_value = []
        with raises(MailboxNotFound):
            account.mailbox_from_kind(MailboxKind.ALL)


class TestAccountRenameMailbox:
    @patch.object(IMAP4_SSL, "rename")
    @patch.object(Account, "mailboxes")
    def test_rename_mailbox(
        self, account_mailboxes_mock, imap_rename_mock, logged_account
    ):
        account_mailboxes_mock.return_value = [
            Mailbox(
                label="Master",
                path="Master",
                kind=MailboxKind.INBOX,
                has_children=True,
                raw=b"",
                _account=logged_account,
            )
        ]
        inbox = logged_account.inbox()
        inbox.rename("Main")

        assert inbox.label == "Main"

    @patch.object(IMAP4_SSL, "rename")
    @patch.object(Account, "mailboxes")
    def test_rename_mailbox_with_child_and_parent(
        self, account_mailboxes_mock, imap_rename_mock, logged_account
    ):
        account_mailboxes_mock.return_value = [
            Mailbox(
                label="Parent",
                path="Parent",
                kind=MailboxKind.ALL,
                has_children=True,
                raw=b"",
                _account=logged_account,
            ),
            Mailbox(
                label="Master",
                path="Parent/Master",
                kind=MailboxKind.INBOX,
                has_children=True,
                raw=b"",
                _account=logged_account,
            ),
            Mailbox(
                label="Nested",
                path="Parent/Master/Nested",
                kind=MailboxKind.TRASH,
                has_children=False,
                raw=b"",
                _account=logged_account,
            ),
        ]
        inbox = logged_account.inbox()
        inbox.rename("Main")

        trash = logged_account.trash()

        assert inbox.label == "Main"
        assert inbox.path == "Parent/Main"
        assert trash.path == "Parent/Main/Nested"

    @patch.object(Account, "mailboxes")
    def test_rename_mailbox_already_exists(
        self, account_mailboxes_mock, logged_account
    ):
        account_mailboxes_mock.return_value = [
            Mailbox(
                label="Master",
                path="Master",
                kind=MailboxKind.INBOX,
                has_children=True,
                raw=b"",
                _account=logged_account,
            ),
            Mailbox(
                label="Main",
                path="Main",
                kind=MailboxKind.TRASH,
                has_children=False,
                raw=b"",
                _account=logged_account,
            ),
        ]
        inbox = logged_account.inbox()

        with raises(MailboxAlreadyExists):
            inbox.rename("Main")


class TestAccountMoveMailbox:
    @patch.object(IMAP4_SSL, "rename")
    @patch.object(Account, "mailboxes")
    def test_move_mailbox(
        self, account_mailboxes_mock, imap_rename_mock, logged_account
    ):
        account_mailboxes_mock.return_value = [
            Mailbox(
                label="Master",
                path="Master",
                kind=MailboxKind.INBOX,
                has_children=True,
                raw=b"",
                _account=logged_account,
            )
        ]
        inbox = logged_account.inbox()
        inbox.move("Main")

        assert inbox.path == "Main"

    @patch.object(IMAP4_SSL, "rename")
    @patch.object(Account, "mailboxes")
    def test_move_mailbox_with_child_and_parent(
        self, account_mailboxes_mock, imap_rename_mock, logged_account
    ):
        account_mailboxes_mock.return_value = [
            Mailbox(
                label="Parent",
                path="Parent",
                kind=MailboxKind.ALL,
                has_children=True,
                raw=b"",
                _account=logged_account,
            ),
            Mailbox(
                label="Master",
                path="Parent/Master",
                kind=MailboxKind.INBOX,
                has_children=True,
                raw=b"",
                _account=logged_account,
            ),
            Mailbox(
                label="Nested",
                path="Parent/Master/Nested",
                kind=MailboxKind.TRASH,
                has_children=False,
                raw=b"",
                _account=logged_account,
            ),
        ]
        inbox = logged_account.inbox()
        inbox.move("Master")

        trash = logged_account.trash()

        assert inbox.path == "Master"
        assert trash.path == "Master/Nested"

    @patch.object(Account, "mailboxes")
    def test_mobe_mailbox_optimisation(self, account_mailboxes_mock, logged_account):
        account_mailboxes_mock.return_value = [
            Mailbox(
                label="Master",
                path="Master",
                kind=MailboxKind.INBOX,
                has_children=True,
                raw=b"",
                _account=logged_account,
            )
        ]

        inbox = logged_account.inbox()
        inbox.move("Master")

    @patch.object(Account, "mailboxes")
    def test_rename_mailbox_already_exists(
        self, account_mailboxes_mock, logged_account
    ):
        account_mailboxes_mock.return_value = [
            Mailbox(
                label="Master",
                path="Master",
                kind=MailboxKind.INBOX,
                has_children=True,
                raw=b"",
                _account=logged_account,
            ),
            Mailbox(
                label="Main",
                path="Main",
                kind=MailboxKind.TRASH,
                has_children=False,
                raw=b"",
                _account=logged_account,
            ),
        ]
        inbox = logged_account.inbox()

        with raises(MailboxAlreadyExists):
            inbox.move("Main")


class TestAccountSelectMailbox:
    @patch.object(IMAP4_SSL, "select")
    @patch.object(Account, "mailboxes")
    def test_select_mailbox(
        self, account_mailboxes_mock, imap_select_mock, logged_account
    ):
        mailbox = Mailbox(
            label="Master",
            path="Master",
            kind=MailboxKind.INBOX,
            has_children=True,
            raw=b"",
            _account=logged_account,
        )
        account_mailboxes_mock.return_value = [mailbox]

        inbox = logged_account.inbox()
        inbox.select()

        assert logged_account.selected_mailbox == mailbox

    @patch.object(IMAP4_SSL, "select")
    @patch.object(Account, "mailboxes")
    def test_select_mailbox_from_path(
        self, account_mailboxes_mock, imap_select_mock, logged_account
    ):
        mailbox = Mailbox(
            label="Master",
            path="Master",
            kind=MailboxKind.INBOX,
            has_children=True,
            raw=b"",
            _account=logged_account,
        )
        account_mailboxes_mock.return_value = [mailbox]

        logged_account.select_mailbox_from_path("Master")

        assert logged_account.selected_mailbox == mailbox
