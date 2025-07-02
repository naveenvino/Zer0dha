import pytest
from unittest.mock import patch, call

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
        assert resp.get_json() == {"order_ids": ["101"]}
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
        assert resp.get_json() == {"order_ids": ["111", "222"]}
        assert po.call_args_list == [
            call(**orders[0]),
            call(**orders[1])
        ]


def test_no_orders(client):
    with patch.object(KiteConnect, "place_order") as po:
        resp = client.post("/webhook", json={})
        assert resp.status_code == 200
        assert resp.get_json() == {"order_ids": []}
        po.assert_not_called()


def test_invalid_json(client):
    with patch.object(KiteConnect, "place_order") as po:
        resp = client.post("/webhook", data="{invalid", content_type="application/json")
        assert resp.status_code == 400
        po.assert_not_called()
