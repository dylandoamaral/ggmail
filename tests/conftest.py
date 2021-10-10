from imaplib import IMAP4_SSL
from unittest.mock import patch

from pytest import fixture

from ggmail.account import Account


@fixture
def account():
    return Account(username="test@gmail.com", password="secret")


@fixture
@patch.object(IMAP4_SSL, "login")
def logged_account(imap_login_mock, account):
    account.login()
    return account
