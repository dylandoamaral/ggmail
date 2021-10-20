# Account exception
class LoginFailed(Exception):
    pass


class NotConnected(Exception):
    pass


class AlreadyConnected(Exception):
    pass


# Mailbox exception
class MailboxFetchingFailed(Exception):
    pass


class MailboxParsingFailed(Exception):
    pass


class MailboxNotFound(Exception):
    pass


class MailboxAlreadyExists(Exception):
    pass


class MailboxNotDeletable(Exception):
    pass


# Message exception
class MessageSearchingFailed(Exception):
    pass


class MessageFetchingFailed(Exception):
    pass


class FlagNotAttached(Exception):
    pass


class FlagAlreadyAttached(Exception):
    pass


# Utf exception
class WrongUTF7String(Exception):
    pass
