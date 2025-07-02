# coding: utf-8
"""Simple webhook server to place orders from TradingView alerts.

Run this example after replacing the API credentials and access token.
TradingView alerts should POST JSON to ``/webhook`` in the format::

    {
        "api_key": "your_api_key",
        "access_token": "your_access_token",
        "orders": [
            {
                "exchange": "NSE",
                "tradingsymbol": "SBIN",
                "transaction_type": "BUY",
                "quantity": 1,
                "order_type": "MARKET",
                "product": "CNC",
                "variety": "regular"
            }
        ]
    }

Multiple orders can be passed in the ``orders`` list. Each object is mapped
as-is to :py:meth:`KiteConnect.place_order` keyword arguments.
"""

import logging
from flask import Flask, request, jsonify
from kiteconnect import KiteConnect

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="your_api_key")
kite.set_access_token("your_access_token")

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def tradingview_webhook():
    """Receive TradingView webhook and place orders."""
    payload = request.get_json(force=True) or {}
    orders = payload.get("orders") or []
    if not isinstance(orders, list):
        orders = [orders]

    order_ids = []
    for order in orders:
        params = order.copy()
        # Default to regular order if variety is not specified
        params.setdefault("variety", kite.VARIETY_REGULAR)
        order_id = kite.place_order(**params)
        order_ids.append(order_id)

    return jsonify({"order_ids": order_ids})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
