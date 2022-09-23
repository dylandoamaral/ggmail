from datetime import datetime
from imaplib import IMAP4_SSL
from unittest.mock import patch

from pytest import fixture

from ggmail.account import Account
from ggmail.authentication import Google
from ggmail.message import ContentType, Message


@fixture
def account():
    authentication = Google(username="test@gmail.com", password="secret")
    return Account(authentication=authentication)


@fixture
@patch.object(IMAP4_SSL, "login")
def logged_account(imap_login_mock, account):
    account.login()
    return account


@fixture
def message(logged_account):
    return Message(
        uid="1",
        from_="from@gmail.com",
        to="to@gmail.com",
        subject="Subject",
        html=r"<html>Body<\html>",
        body="Body",
        date=datetime.now(),
        content_type=ContentType.MULTIPART,
        flags=[],
        _account=logged_account,
    )


@fixture
def messages(message, logged_account):
    return [
        message,
        Message(
            uid="2",
            from_="from@gmail.com",
            to="to@gmail.com",
            subject="Subject",
            html=r"<html>Body<\html>",
            body="Body",
            date=datetime.now(),
            content_type=ContentType.MULTIPART,
            flags=[],
            _account=logged_account,
        ),
    ]
