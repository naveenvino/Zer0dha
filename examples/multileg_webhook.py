# coding: utf-8
"""Webhook server for trading multi-leg option strategies via TradingView alerts.

This example extends :mod:`examples.tradingview_webhook` by using
``KiteConnect.place_spread_order`` to execute all option legs atomically. It is
useful for strategies such as selling NIFTY weekly options with a hedging leg.

The script expects these environment variables:

``KITE_API_KEY``      – Your Kite Connect API key.
``KITE_API_SECRET``   – API secret used when generating the access token.
``ACCESS_TOKEN``      – A valid access token.

TradingView alerts should POST JSON data to ``/webhook`` with a ``legs`` list
containing parameters similar to :py:meth:`KiteConnect.place_order`::

    {
        "legs": [
            {"symbol": "NIFTY24AUG17450CE", "transaction_type": "SELL", "quantity": 75},
            {"symbol": "NIFTY24AUG17350CE", "transaction_type": "BUY", "quantity": 75}
        ]
    }

Exit orders can be sent via the ``exit`` key with parameters accepted by
:py:meth:`KiteConnect.exit_order`.
"""

import logging
import os
from flask import Flask, request, jsonify
from kiteconnect import KiteConnect

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key=os.environ["KITE_API_KEY"])
kite.set_access_token(os.environ["ACCESS_TOKEN"])

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def tradingview_webhook():
    """Receive TradingView webhook and place/exit multi-leg orders."""
    payload = request.get_json(force=True) or {}
    legs = payload.get("legs") or []
    exit_orders = payload.get("exit") or []

    if not isinstance(legs, list):
        legs = [legs]
    if not isinstance(exit_orders, list):
        exit_orders = [exit_orders]

    spread_legs = []
    for leg in legs:
        params = {
            "tradingsymbol": leg.get("symbol") or leg.get("tradingsymbol"),
            "exchange": leg.get("exchange", kite.EXCHANGE_NFO),
            "transaction_type": leg.get("transaction_type"),
            "quantity": leg.get("quantity", 1),
            "order_type": leg.get("order_type", kite.ORDER_TYPE_MARKET),
            "product": leg.get("product", kite.PRODUCT_MIS),
            "variety": leg.get("variety", kite.VARIETY_REGULAR),
        }
        spread_legs.append({k: v for k, v in params.items() if v is not None})

    order_ids = []
    if spread_legs:
        order_ids = kite.place_spread_order(spread_legs)

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
