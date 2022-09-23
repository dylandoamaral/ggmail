from imaplib import IMAP4, IMAP4_SSL
from unittest.mock import patch

import pytest
from pytest import raises

from ggmail.account import Account
from ggmail.authentication import Google, GoogleOAuth2, Outlook
from ggmail.exception import AlreadyConnected, LoginFailed


class TestAuthenticationLogin:
    google = Google(username="test@gmail.com", password="secret")
    google_oauth2 = GoogleOAuth2(username="test@gmail.com", token="secret")
    outlook = Outlook(username="test@gmail.com", password="secret")

    @patch.object(IMAP4_SSL, "authenticate")
    @patch.object(IMAP4_SSL, "login")
    @pytest.mark.parametrize(
        "authentication",
        [
            pytest.param(google, id="google",),
            pytest.param(google_oauth2, id="google_oauth2"),
            pytest.param(outlook, id="outlook"),
        ],
    )
    def test_login_success(
        self, imap_login_mock, imap_authenticate_mock, authentication
    ):
        account = Account(authentication=authentication)
        account.login()
        assert account.is_connected is True

    @patch.object(IMAP4_SSL, "authenticate")
    @patch.object(IMAP4_SSL, "login")
    @pytest.mark.parametrize(
        "authentication",
        [
            pytest.param(google, id="google",),
            pytest.param(google_oauth2, id="google_oauth2"),
            pytest.param(outlook, id="outlook"),
        ],
    )
    def test_login_already_connected(
        self, imap_login_mock, imap_authenticate_mock, authentication
    ):
        account = Account(authentication=authentication)
        account.login()

        with raises(AlreadyConnected):
            account.login()

    @patch.object(IMAP4_SSL, "authenticate")
    @patch.object(IMAP4_SSL, "login")
    @pytest.mark.parametrize(
        "authentication",
        [
            pytest.param(google, id="google",),
            pytest.param(google_oauth2, id="google_oauth2"),
            pytest.param(outlook, id="outlook"),
        ],
    )
    def test_login_imap_error(
        self, imap_login_mock, imap_authenticate_mock, authentication
    ):
        imap_login_mock.side_effect = IMAP4.error()
        imap_authenticate_mock.side_effect = IMAP4.error()

        account = Account(authentication=authentication)

        with raises(LoginFailed):
            account.login()
