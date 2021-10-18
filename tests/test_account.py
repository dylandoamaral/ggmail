from imaplib import IMAP4_SSL
from unittest.mock import ANY, Mock, call, patch

import pytest
from pytest import fixture, raises

from ggmail.account import Account
from ggmail.exception import (
    FlagAlreadyAttached,
    FlagNotAttached,
    MailboxAlreadyExists,
    MailboxFetchingFailed,
    MailboxNotDeletable,
    MailboxNotFound,
    MessageFetchingFailed,
    MessageSearchingFailed,
    NotConnected,
)
from ggmail.flag import Flag
from ggmail.mailbox import Mailbox, MailboxKind
from ggmail.policy import all_


@fixture
def logged_account_with_inbox(logged_account):
    mailbox = Mailbox(
        label="Inbox",
        path="Inbox",
        kind=MailboxKind.INBOX,
        has_children=True,
        raw=b"",
        _account=logged_account,
    )
    logged_account._mailboxes = [mailbox]
    return logged_account


class TestAccountLogout:
    def test_logout_success(self, logged_account):
        logged_account.logout()
        assert logged_account.is_connected is False

    def test_logout_not_connected(self, account):
        with raises(NotConnected):
            account.logout()


class TestAccountContextManager:
    @patch.object(IMAP4_SSL, "logout")
    @patch.object(IMAP4_SSL, "login")
    def test_context_manager(self, imap_login_mock, imap_logout_mock, account):
        with account:
            pass

        imap_login_mock.assert_called_once()
        imap_logout_mock.assert_called_once()


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
    def test_move_mailbox_optimisation(self, account_mailboxes_mock, logged_account):
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
    def test_move_mailbox_already_exists(self, account_mailboxes_mock, logged_account):
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

    def test_move_mailbox_not_connected(self, account):
        with raises(NotConnected):
            account.move_mailbox(Mock(), "")


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

    def test_select_mailbox_not_connected(self, account):
        with raises(NotConnected):
            account.select_mailbox(Mock())


class TestAccountCreateMailbox:
    @patch.object(IMAP4_SSL, "create")
    @patch.object(Account, "mailboxes")
    def test_create_mailbox(
        self, account_mailboxes_mock, imap_create_mock, logged_account
    ):
        account_mailboxes_mock.return_value = []
        mailbox = logged_account.create_mailbox("Parent/New")
        assert mailbox.label == "New"
        assert mailbox.path == "Parent/New"
        imap_create_mock.assert_called_once_with("Parent/New")

    @patch.object(Account, "mailboxes")
    def test_create_mailbox_already_exists(
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
            )
        ]

        with raises(MailboxAlreadyExists):
            logged_account.create_mailbox("Master")

    def test_create_mailbox_not_connected(self, account):
        with raises(NotConnected):
            account.create_mailbox("")


class TestAccountDeleteMailbox:
    @patch.object(IMAP4_SSL, "delete")
    @patch.object(Account, "mailboxes")
    def test_delete_mailbox(
        self, account_mailboxes_mock, imap_delete_mock, logged_account
    ):
        mailbox = Mailbox(
            label="Master",
            path="Master",
            kind=MailboxKind.CUSTOM,
            has_children=True,
            raw=b"",
            _account=logged_account,
        )
        account_mailboxes_mock.return_value = [mailbox]
        mailbox = logged_account.delete_mailbox(mailbox)

        assert len(logged_account.mailboxes()) == 0
        imap_delete_mock.assert_called_once_with("Master")

    @patch.object(IMAP4_SSL, "delete")
    @patch.object(Account, "mailboxes")
    def test_delete_mailbox_from_path(
        self, account_mailboxes_mock, imap_delete_mock, logged_account
    ):
        account_mailboxes_mock.return_value = [
            Mailbox(
                label="Master",
                path="Master",
                kind=MailboxKind.CUSTOM,
                has_children=True,
                raw=b"",
                _account=logged_account,
            )
        ]

        logged_account.delete_mailbox_from_path("Master")

        assert len(logged_account.mailboxes()) == 0
        imap_delete_mock.assert_called_once_with("Master")

    @patch.object(IMAP4_SSL, "delete")
    @patch.object(Account, "mailboxes")
    def test_delete_mailbox_not_found(
        self, account_mailboxes_mock, imap_delete_mock, logged_account
    ):
        account_mailboxes_mock.return_value = []

        mailbox = Mailbox(
            label="Master",
            path="Master",
            kind=MailboxKind.CUSTOM,
            has_children=True,
            raw=b"",
            _account=logged_account,
        )

        with raises(MailboxNotFound):
            logged_account.delete_mailbox(mailbox)

    @patch.object(IMAP4_SSL, "delete")
    @patch.object(Account, "mailboxes")
    def test_delete_mailbox_not_deletable(
        self, account_mailboxes_mock, imap_delete_mock, logged_account
    ):
        account_mailboxes_mock.return_value = []

        mailbox = Mailbox(
            label="Inbox",
            path="Inbox",
            kind=MailboxKind.INBOX,
            has_children=True,
            raw=b"",
            _account=logged_account,
        )

        with raises(MailboxNotDeletable):
            logged_account.delete_mailbox(mailbox)

    def test_delete_mailbox_not_connected(self, account):
        with raises(NotConnected):
            account.delete_mailbox_from_path("")


class TestAccountSearchMessage:
    @patch.object(IMAP4_SSL, "select")
    @patch.object(IMAP4_SSL, "uid")
    def test_search_message_uids(
        self, imap_uid_mock, imap_search_mock, logged_account_with_inbox
    ):
        imap_uid_mock.return_value = "OK", [b"1 2 3"]
        inbox = logged_account_with_inbox.inbox()
        message_ids = inbox.search_uids(all_)
        assert message_ids == ["1", "2", "3"]
        imap_uid_mock.assert_called_once_with("SEARCH", None, "ALL")
        imap_search_mock.assert_called_once()

    @patch.object(IMAP4_SSL, "uid")
    def test_search_message_uids_empty(self, imap_uid_mock, logged_account):
        imap_uid_mock.return_value = "OK", [b""]
        message_ids = logged_account.search_message_uids()
        assert message_ids == []

    @patch.object(IMAP4_SSL, "uid")
    def test_search_message_uids_ko(self, imap_search_mock, logged_account):
        imap_search_mock.return_value = "KO", []

        with raises(MessageSearchingFailed):
            logged_account.search_message_uids()

    def test_search_message_uids_not_connected(self, account):
        with raises(NotConnected):
            account.search_message_uids()

    @patch.object(IMAP4_SSL, "fetch")
    @patch.object(Account, "search_message_uids")
    @patch("ggmail.account.message_factory")
    def test_search_messages(
        self,
        message_factory_mock,
        account_search_message_uids_mock,
        imap_fetch_mock,
        logged_account,
    ):
        account_search_message_uids_mock.return_value = ["1", "2"]
        imap_fetch_mock.return_value = "OK", [b"msg1", b")", b"msg2", b")"]
        message_factory_mock.return_value = Mock()

        messages = logged_account.search_messages()

        assert len(messages) == 2
        message_factory_mock.assert_has_calls(
            [call("1", b"msg1", ANY), call("2", b"msg2", ANY)]
        )

    @patch.object(Account, "search_message_uids")
    @patch("ggmail.account.message_factory")
    def test_search_messages_empty(
        self,
        message_factory_mock,
        account_search_message_uids_mock,
        logged_account,
    ):
        account_search_message_uids_mock.return_value = []
        message_factory_mock.return_value = Mock()

        messages = logged_account.search_messages()

        assert len(messages) == 0

    @patch.object(IMAP4_SSL, "select")
    @patch.object(IMAP4_SSL, "fetch")
    @patch.object(Account, "search_message_uids")
    @patch("ggmail.account.message_factory")
    def test_search_messages_from_mailbox(
        self,
        message_factory_mock,
        account_search_message_uids_mock,
        imap_fetch_mock,
        imap_select_mock,
        logged_account_with_inbox,
    ):
        account_search_message_uids_mock.return_value = ["1", "2"]
        imap_fetch_mock.return_value = "OK", [b"msg1", b")", b"msg2", b")"]
        message_factory_mock.return_value = Mock()

        inbox = logged_account_with_inbox.inbox()
        messages = inbox.search()

        assert len(messages) == 2
        message_factory_mock.assert_has_calls(
            [call("1", b"msg1", ANY), call("2", b"msg2", ANY)]
        )

    @patch.object(IMAP4_SSL, "fetch")
    @patch.object(Account, "search_message_uids")
    def test_search_messages_ko(
        self,
        account_search_message_uids_mock,
        imap_fetch_mock,
        logged_account,
    ):
        account_search_message_uids_mock.return_value = ["1", "2"]
        imap_fetch_mock.return_value = "KO", []

        with raises(MessageFetchingFailed):
            logged_account.search_messages()

    def test_search_message_not_connected(self, account):
        with raises(NotConnected):
            account.search_messages()


class TestAccountExpunge:
    @patch.object(IMAP4_SSL, "expunge")
    def test_expunge(self, imap_expunge_mock, logged_account):
        logged_account.expunge()
        imap_expunge_mock.assert_called_once()


class TestAccountBulkOperation:
    @patch.object(IMAP4_SSL, "uid")
    def test_copy_messages(self, imap_uid_mock, logged_account_with_inbox, messages):
        inbox = logged_account_with_inbox.inbox()
        logged_account_with_inbox.copy_messages(messages, inbox)
        imap_uid_mock.assert_called_once_with("COPY", "1,2", inbox.path)

    @patch.object(IMAP4_SSL, "uid")
    def test_move_messages(self, imap_uid_mock, logged_account_with_inbox, messages):
        inbox = logged_account_with_inbox.inbox()
        logged_account_with_inbox.move_messages(messages, inbox)
        imap_uid_mock.has_calls(
            call("COPY", "1,2", inbox.path),  # Copy from the origin
            call("STORE", "1,2", "+FLAGS", "\\Deleted"),  # Remove the origin
        )
        for message in messages:
            assert Flag.DELETED in message.flags

    @patch.object(IMAP4_SSL, "expunge")
    @patch.object(IMAP4_SSL, "uid")
    def test_move_messages_with_expunge(
        self, imap_uid_mock, imap_expungd_mock, logged_account_with_inbox, messages
    ):
        inbox = logged_account_with_inbox.inbox()
        logged_account_with_inbox.move_messages(messages, inbox, with_expunge=True)
        imap_uid_mock.has_calls(
            call("COPY", "1,2", inbox.path),  # Copy from the origin
            call("STORE", "1,2", "+FLAGS", "\\Deleted"),  # Remove the origin
        )
        imap_expungd_mock.assert_called_once()
        for message in messages:
            assert Flag.DELETED in message.flags

    @patch.object(IMAP4_SSL, "uid")
    def test_add_flag_messages(
        self, imap_uid_mock, logged_account_with_inbox, messages
    ):
        logged_account_with_inbox.add_flag_messages(messages, Flag.FLAGGED)
        imap_uid_mock.assert_called_once_with("STORE", "1,2", "+FLAGS", "\\Flagged")
        for message in messages:
            assert Flag.FLAGGED in message.flags

    def test_add_flag_messages_already_attached(
        self, logged_account_with_inbox, messages
    ):
        for message in messages:
            message.flags.append(Flag.FLAGGED)

        with raises(FlagAlreadyAttached):
            logged_account_with_inbox.add_flag_messages(messages, Flag.FLAGGED)

    @patch.object(IMAP4_SSL, "uid")
    def test_remove_flag_messages(
        self, imap_uid_mock, logged_account_with_inbox, messages
    ):
        for message in messages:
            message.flags.append(Flag.FLAGGED)
        logged_account_with_inbox.remove_flag_messages(messages, Flag.FLAGGED)
        imap_uid_mock.assert_called_once_with("STORE", "1,2", "-FLAGS", "\\Flagged")
        for message in messages:
            assert Flag.FLAGGED not in message.flags

    def test_remove_flag_messages_not_attached(
        self, logged_account_with_inbox, messages
    ):
        with raises(FlagNotAttached):
            logged_account_with_inbox.remove_flag_messages(messages, Flag.FLAGGED)
