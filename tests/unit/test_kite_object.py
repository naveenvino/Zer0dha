# coding: utf-8
import pytest
from mock import patch
import responses
import requests
import warnings

from kiteconnect import KiteConnect
import kiteconnect.exceptions as ex


def get_fake_token(self, route, params=None):
    return {
        "access_token": "TOKEN",
        "login_time": None
    }


def get_fake_delete(self, route, params=None):
    return {"message": "token invalidated"}


class TestKiteConnectObject:

    def test_login_url(self, kiteconnect):
        assert kiteconnect.login_url() == "https://kite.zerodha.com/connect/login?api_key=<API-KEY>&v=3"

    def test_request_without_pooling(self, kiteconnect):
        assert isinstance(kiteconnect.reqsession, requests.Session) is True
        assert kiteconnect.reqsession.request is not None

    def test_request_pooling(self, kiteconnect_with_pooling):
        assert isinstance(kiteconnect_with_pooling.reqsession, requests.Session) is True
        assert kiteconnect_with_pooling.reqsession.request is not None
        http_adapter = kiteconnect_with_pooling.reqsession.adapters['https://']
        assert http_adapter._pool_maxsize == 10
        assert http_adapter._pool_connections == 20
        assert http_adapter._pool_block is False
        assert http_adapter.max_retries.total == 2

    @responses.activate
    def test_set_session_expiry_hook_meth(self, kiteconnect):

        def mock_hook():
            raise ex.TokenException("token expired it seems! please login again")

        kiteconnect.set_session_expiry_hook(mock_hook)

        # Now lets try raising TokenException
        responses.add(
            responses.GET,
            "{0}{1}".format(kiteconnect.root, kiteconnect._routes["portfolio.positions"]),
            body='{"error_type": "TokenException", "message": "Please login again"}',
            content_type="application/json",
            status=403
        )
        with pytest.raises(ex.TokenException) as exc:
            kiteconnect.positions()
            assert exc.message == "token expired it seems! please login again"

    def test_set_access_token_meth(self, kiteconnect):
        assert kiteconnect.access_token == "<ACCESS-TOKEN>"
        # Modify the access token now
        kiteconnect.set_access_token("<MY-ACCESS-TOKEN>")
        assert kiteconnect.access_token == "<MY-ACCESS-TOKEN>"
        # Change it back
        kiteconnect.set_access_token("<ACCESS-TOKEN>")

    @patch.object(KiteConnect, "_post", get_fake_token)
    def test_generate_session(self, kiteconnect):
        resp = kiteconnect.generate_session(
            request_token="<REQUEST-TOKEN>",
            api_secret="<API-SECRET>"
        )
        assert resp["access_token"] == "TOKEN"
        assert kiteconnect.access_token == "TOKEN"

        # Change it back
        kiteconnect.set_access_token("<ACCESS-TOKEN>")

    @patch.object(KiteConnect, "_delete", get_fake_delete)
    def test_invalidate_token(self, kiteconnect):
        resp = kiteconnect.invalidate_access_token(access_token="<ACCESS-TOKEN>")
        assert resp["message"] == "token invalidated"

    def test_disable_warnings_called_when_ssl_disabled(self):
        """Ensure urllib3 warnings are disabled when disable_ssl is True."""
        with patch("requests.packages.urllib3.disable_warnings") as dw:
            KiteConnect(api_key="<API-KEY>", disable_ssl=True)
            dw.assert_called_once()

    def test_disable_warnings_not_called_by_default(self):
        """Ensure urllib3 warnings remain when disable_ssl is False."""
        with patch("requests.packages.urllib3.disable_warnings") as dw:
            KiteConnect(api_key="<API-KEY>")
            dw.assert_not_called()

    def test_warning_filter_updated_when_ssl_disabled(self):
        """HTTP warnings should be ignored when SSL verification is off."""
        with warnings.catch_warnings():
            warnings.resetwarnings()
            KiteConnect(api_key="<API-KEY>", disable_ssl=True)
            assert any(
                f[0] == "ignore" and f[2] == requests.packages.urllib3.exceptions.HTTPWarning
                for f in warnings.filters
            )

    def test_warning_filter_unmodified_when_ssl_enabled(self):
        """HTTP warnings remain enabled when SSL verification is on."""
        with warnings.catch_warnings():
            warnings.resetwarnings()
            KiteConnect(api_key="<API-KEY>")
            assert not any(
                f[0] == "ignore" and f[2] == requests.packages.urllib3.exceptions.HTTPWarning
                for f in warnings.filters
            )

    def test_close_closes_session(self, kiteconnect):
        """Calling close() should close the underlying requests session."""
        with patch.object(kiteconnect.reqsession, "close") as c:
            kiteconnect.close()
            c.assert_called_once()

    def test_context_manager_closes_session(self):
        """KiteConnect should support usage as a context manager."""
        kite = KiteConnect(api_key="<API-KEY>")
        with patch.object(kite.reqsession, "close") as c:
            with kite as k:
                assert k is kite
            c.assert_called_once()
