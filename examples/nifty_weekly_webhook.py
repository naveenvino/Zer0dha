# coding: utf-8
"""Simple webhook server for NIFTY weekly option strategies.

This example shows how TradingView alerts can trigger multi-leg option
orders with a hedging leg using :class:`KiteConnect`.

Environment variables required:
``KITE_API_KEY``      – Your Kite Connect API key.
``KITE_API_SECRET``   – API secret used when generating the access token.
``ACCESS_TOKEN``      – A valid access token for the above key.

TradingView should POST JSON to ``/webhook`` with the following structure::

    {
        "action": "enter",              # or "exit"
        "expiry": "2024-08-29",        # ISO date for the weekly expiry
        "strike": 22200,                # At-the-money strike
        "right": "CE",                 # "CE" or "PE"
        "quantity": 50,
        "hedge_offset": 200             # distance of the hedge strike
    }

When ``action`` is ``"enter"`` two legs are placed sequentially:
1. Sell the specified strike.
2. Buy the hedge leg ``strike + hedge_offset``.

"exit" requests must provide ``order_ids`` with the IDs returned when
placing the orders.
"""

import datetime as _dt
import logging
import os

from flask import Flask, jsonify, request
from kiteconnect import KiteConnect

logging.basicConfig(level=logging.DEBUG)

kite_api_key = os.environ["KITE_API_KEY"]
access_token = os.environ["ACCESS_TOKEN"]

kite = KiteConnect(api_key=kite_api_key)
kite.set_access_token(access_token)

app = Flask(__name__)


def _option_symbol(expiry: str, strike: int, right: str) -> str:
    """Return the option trading symbol for NIFTY weekly expiry."""
    d = _dt.date.fromisoformat(expiry)
    return f"NIFTY{d.strftime('%y%b').upper()}{int(strike)}{right.upper()}"


@app.route("/webhook", methods=["POST"])
def tradingview_webhook():
    payload = request.get_json(force=True) or {}
    action = payload.get("action")

    if action == "enter":
        strike = payload["strike"]
        right = payload.get("right", "CE")
        qty = payload.get("quantity", 1)
        hedge_offset = int(payload.get("hedge_offset", 0))
        expiry = payload["expiry"]

        legs = [
            {
                "variety": kite.VARIETY_REGULAR,
                "exchange": kite.EXCHANGE_NFO,
                "tradingsymbol": _option_symbol(expiry, strike, right),
                "transaction_type": kite.TRANSACTION_TYPE_SELL,
                "quantity": qty,
                "product": kite.PRODUCT_MIS,
                "order_type": kite.ORDER_TYPE_MARKET,
            }
        ]
        if hedge_offset:
            legs.append(
                {
                    "variety": kite.VARIETY_REGULAR,
                    "exchange": kite.EXCHANGE_NFO,
                    "tradingsymbol": _option_symbol(expiry, strike + hedge_offset, right),
                    "transaction_type": kite.TRANSACTION_TYPE_BUY,
                    "quantity": qty,
                    "product": kite.PRODUCT_MIS,
                    "order_type": kite.ORDER_TYPE_MARKET,
                }
            )
        order_ids = kite.place_spread_order(legs)
        return jsonify({"order_ids": order_ids})

    elif action == "exit":
        exited = []
        for oid in payload.get("order_ids", []):
            exited.append(kite.exit_order(kite.VARIETY_REGULAR, oid))
        return jsonify({"exit_order_ids": exited})

    return jsonify({"error": "invalid action"}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
