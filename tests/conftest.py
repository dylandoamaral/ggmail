from pytest import fixture

from ggmail.account import Account


@fixture
def account():
    return Account(username="test@gmail.com", password="secret")
