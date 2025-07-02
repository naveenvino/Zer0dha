# coding: utf-8
"""Simple webhook server to place orders from TradingView alerts.

The script expects the following environment variables to be set:

``KITE_API_KEY``      – Your Kite Connect API key.
``KITE_API_SECRET``   – API secret used when generating the access token.
``ACCESS_TOKEN``      – A valid access token for the above key.

TradingView alerts should POST JSON data to ``/webhook`` in the following
format::

    {
        "orders": [
            {
                "symbol": "NIFTY24AUG17450CE",
                "transaction_type": "BUY",
                "quantity": 75,
                "exchange": "NFO",
                "order_type": "MARKET",
                "product": "MIS"
            },
            {
                "symbol": "NIFTY24AUG17650CE",
                "transaction_type": "SELL",
                "quantity": 75,
                "exchange": "NFO",
                "order_type": "MARKET",
                "product": "MIS"
            }
        ]
    }

Every entry in ``orders`` maps directly to the parameters accepted by
:py:meth:`KiteConnect.place_order`. Multiple entries can be sent to execute
multi-leg option strategies.

Exit orders can be sent via the ``exit_orders`` (or ``exit``) key which should
contain the parameters required by :py:meth:`KiteConnect.exit_order`.
"""

import logging
import os
from flask import Flask, request, jsonify
from kiteconnect import KiteConnect

logging.basicConfig(level=logging.DEBUG)

kite_api_key = os.environ["KITE_API_KEY"]
kite_api_secret = os.environ.get("KITE_API_SECRET")
access_token = os.environ["ACCESS_TOKEN"]

kite = KiteConnect(api_key=kite_api_key)
kite.set_access_token(access_token)

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def tradingview_webhook():
    """Receive TradingView webhook and place/exit orders."""
    payload = request.get_json(force=True) or {}
    orders = payload.get("orders") or []
    exit_orders = payload.get("exit_orders") or payload.get("exit") or []

    if not isinstance(orders, list):
        orders = [orders]
    if not isinstance(exit_orders, list):
        exit_orders = [exit_orders]

    order_ids = []
    for order in orders:
        params = {
            "tradingsymbol": order.get("symbol") or order.get("tradingsymbol"),
            "exchange": order.get("exchange", kite.EXCHANGE_NSE),
            "transaction_type": order.get("transaction_type"),
            "quantity": order.get("quantity", 1),
            "order_type": order.get("order_type", kite.ORDER_TYPE_MARKET),
            "product": order.get("product", kite.PRODUCT_CNC),
            "variety": order.get("variety", kite.VARIETY_REGULAR),
        }

        # Filter out unset keys
        params = {k: v for k, v in params.items() if v is not None}

        order_id = kite.place_order(**params)
        order_ids.append(order_id)

    exited_order_ids = []
    for exit_order in exit_orders:
        params = {
            "variety": exit_order.get("variety", kite.VARIETY_REGULAR),
            "order_id": exit_order.get("order_id"),
            "parent_order_id": exit_order.get("parent_order_id"),
        }

        params = {k: v for k, v in params.items() if v is not None}
        if "order_id" in params:
            exited_order_ids.append(
                kite.exit_order(params.pop("variety"), params.pop("order_id"), **params)
            )

    return jsonify({"order_ids": order_ids, "exit_order_ids": exited_order_ids})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
