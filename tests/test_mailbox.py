from ggmail.mailbox import MailboxKind, mailbox_factory


class TestMailboxFactory:
    def test_mailbox_custom(self):
        raw_mailbox_description = b'(\\HasNoChildren) "/" "Custom"'
        mailbox = mailbox_factory(raw_mailbox_description)
        assert mailbox.kind is MailboxKind.CUSTOM
        assert mailbox.has_children is False
        assert mailbox.label == "Custom"
        assert mailbox.path == "Custom"

    def test_mailbox_inbox(self):
        raw_mailbox_description = b'(\\HasNoChildren) "/" "INBOX"'
        mailbox = mailbox_factory(raw_mailbox_description)
        assert mailbox.kind is MailboxKind.INBOX
        assert mailbox.has_children is False
        assert mailbox.label == "Inbox"
        assert mailbox.path == "Inbox"

    def test_mailbox_special(self):
        raw_mailbox_description = b'(\\HasNoChildren \\Junk) "/" "[Gmail]/Spam"'
        mailbox = mailbox_factory(raw_mailbox_description)
        assert mailbox.kind is MailboxKind.JUNK
        assert mailbox.has_children is False
        assert mailbox.label == "Spam"
        assert mailbox.path == "[Gmail]/Spam"

    def test_mailbox_with_children(self):
        raw_mailbox_description = b'(\\HasChildren) "/" "Parents"'
        mailbox = mailbox_factory(raw_mailbox_description)
        assert mailbox.kind is MailboxKind.CUSTOM
        assert mailbox.has_children is True
        assert mailbox.label == "Parents"
        assert mailbox.path == "Parents"
