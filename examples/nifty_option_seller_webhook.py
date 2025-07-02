# coding: utf-8
"""TradingView webhook for NIFTY option selling with hedge legs.

This Flask application exposes ``/webhook`` to receive TradingView alerts
and places four orders: sell call and put at the given strike and buy
hedge legs ``hedge_offset`` points away. Exit order IDs can be provided via
``exit_order_ids``.

Environment variables required:
``KITE_API_KEY``      – Kite Connect API key
``ACCESS_TOKEN``      – Access token for the above key
``KITE_API_SECRET``   – Optional, needed only when generating a new token
"""

import logging
import os
from flask import Flask, request, jsonify
from kiteconnect import KiteConnect

logging.basicConfig(level=logging.DEBUG)

kite_api_key = os.environ["KITE_API_KEY"]
access_token = os.environ["ACCESS_TOKEN"]

kite = KiteConnect(api_key=kite_api_key)
kite.set_access_token(access_token)

app = Flask(__name__)


def _symbol(expiry: str, strike: int, option: str) -> str:
    """Return a NIFTY option symbol like ``NIFTY24AUG17650CE``."""
    return f"NIFTY{expiry}{strike}{option}"


@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle TradingView webhook and place option orders."""
    payload = request.get_json(force=True) or {}
    strike = int(payload["strike"])
    expiry = payload["expiry"]
    qty = int(payload.get("quantity", 50))
    hedge = int(payload.get("hedge_offset", 200))
    product = payload.get("product", kite.PRODUCT_MIS)
    order_type = payload.get("order_type", kite.ORDER_TYPE_MARKET)
    variety = payload.get("variety", kite.VARIETY_REGULAR)

    orders = [
        {
            "tradingsymbol": _symbol(expiry, strike, "CE"),
            "exchange": kite.EXCHANGE_NFO,
            "transaction_type": kite.TRANSACTION_TYPE_SELL,
            "quantity": qty,
            "order_type": order_type,
            "product": product,
            "variety": variety,
        },
        {
            "tradingsymbol": _symbol(expiry, strike, "PE"),
            "exchange": kite.EXCHANGE_NFO,
            "transaction_type": kite.TRANSACTION_TYPE_SELL,
            "quantity": qty,
            "order_type": order_type,
            "product": product,
            "variety": variety,
        },
        {
            "tradingsymbol": _symbol(expiry, strike + hedge, "CE"),
            "exchange": kite.EXCHANGE_NFO,
            "transaction_type": kite.TRANSACTION_TYPE_BUY,
            "quantity": qty,
            "order_type": order_type,
            "product": product,
            "variety": variety,
        },
        {
            "tradingsymbol": _symbol(expiry, strike - hedge, "PE"),
            "exchange": kite.EXCHANGE_NFO,
            "transaction_type": kite.TRANSACTION_TYPE_BUY,
            "quantity": qty,
            "order_type": order_type,
            "product": product,
            "variety": variety,
        },
    ]

    order_ids = [kite.place_order(**o) for o in orders]

    exited_order_ids = []
    for oid in payload.get("exit_order_ids", []):
        exited_order_ids.append(kite.exit_order(variety, oid))

    return jsonify({"order_ids": order_ids, "exit_order_ids": exited_order_ids})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
