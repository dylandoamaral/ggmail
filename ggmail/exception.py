class LoginFailed(Exception):
    pass


class MailboxFetchingFailed(Exception):
    pass


class MailboxParsingFailed(Exception):
    pass


class NotConnected(Exception):
    pass


class AlreadyConnected(Exception):
    pass


class WrongUTF7String(Exception):
    pass
