import os
import pytest
from unittest.mock import patch, call

# Ensure required environment variables are available before importing
# the webhook example. These defaults let the import succeed without
# external setup.
os.environ.setdefault("KITE_API_KEY", "test_key")
os.environ.setdefault("KITE_API_SECRET", "test_secret")
os.environ.setdefault("ACCESS_TOKEN", "test_token")

from examples import tradingview_webhook
from kiteconnect.connect import KiteConnect


@pytest.fixture
def client():
    """Flask test client for the webhook example."""
    tradingview_webhook.app.config['TESTING'] = True
    with tradingview_webhook.app.test_client() as client:
        yield client


def test_single_order_defaults_variety(client):
    order = {
        "exchange": "NSE",
        "tradingsymbol": "SBIN",
        "transaction_type": "BUY",
        "quantity": 1,
        "order_type": "MARKET",
        "product": "CNC"
    }
    expected = order.copy()
    expected["variety"] = tradingview_webhook.kite.VARIETY_REGULAR

    with patch.object(KiteConnect, "place_order", return_value="101") as po:
        resp = client.post("/webhook", json={"orders": order})
        assert resp.status_code == 200
        assert resp.get_json() == {
            "order_ids": ["101"],
            "exit_order_ids": [],
        }
        po.assert_called_once_with(**expected)


def test_multiple_orders(client):
    orders = [
        {
            "exchange": "NSE",
            "tradingsymbol": "SBIN",
            "transaction_type": "BUY",
            "quantity": 1,
            "order_type": "MARKET",
            "product": "CNC",
            "variety": "amo"
        },
        {
            "exchange": "NSE",
            "tradingsymbol": "INFY",
            "transaction_type": "SELL",
            "quantity": 2,
            "order_type": "LIMIT",
            "product": "CNC",
            "variety": "regular"
        }
    ]
    with patch.object(KiteConnect, "place_order", side_effect=["111", "222"]) as po:
        resp = client.post("/webhook", json={"orders": orders})
        assert resp.status_code == 200
        assert resp.get_json() == {
            "order_ids": ["111", "222"],
            "exit_order_ids": [],
        }
        assert po.call_args_list == [
            call(**orders[0]),
            call(**orders[1])
        ]


def test_no_orders(client):
    with patch.object(KiteConnect, "place_order") as po:
        resp = client.post("/webhook", json={})
        assert resp.status_code == 200
        assert resp.get_json() == {"order_ids": [], "exit_order_ids": []}
        po.assert_not_called()


def test_invalid_json(client):
    with patch.object(KiteConnect, "place_order") as po:
        resp = client.post("/webhook", data="{invalid", content_type="application/json")
        assert resp.status_code == 400
        po.assert_not_called()


def test_exit_orders(client):
    exits = [{"variety": "co", "order_id": "abc", "parent_order_id": "p1"}]
    with patch.object(KiteConnect, "exit_order", return_value="abc") as eo:
        resp = client.post("/webhook", json={"exit_orders": exits})
        assert resp.status_code == 200
        assert resp.get_json() == {"order_ids": [], "exit_order_ids": ["abc"]}
        eo.assert_called_once_with("co", "abc", parent_order_id="p1")
