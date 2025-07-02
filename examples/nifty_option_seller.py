# coding: utf-8
"""Example option seller webapp using TradingView alerts.

This example stores a simple NIFTY option selling strategy configuration and
executes the orders when TradingView sends an alert to ``/webhook``.
It is meant as a demonstration of the Kite Connect API and should be used with
caution in a real trading environment.

Environment variables required::

    KITE_API_KEY    – Your Kite Connect API key.
    ACCESS_TOKEN    – A valid access token.

Option legs and exit parameters can be configured by sending a JSON payload to
``/config``::

    {
        "spread_legs": [
            {
                "symbol": "NIFTY24AUG17450CE",
                "transaction_type": "SELL",
                "quantity": 75
            },
            {
                "symbol": "NIFTY24AUG17650CE",
                "transaction_type": "BUY",
                "quantity": 75
            }
        ],
        "exit": {
            "profit": 1000,
            "stop_loss": -500
        }
    }

A POST request to ``/webhook`` will place all configured legs. The example does
not evaluate exit conditions and is kept intentionally simple.
"""

import logging
import os
from flask import Flask, request, jsonify
from kiteconnect import KiteConnect

logging.basicConfig(level=logging.DEBUG)

api_key = os.environ["KITE_API_KEY"]
access_token = os.environ["ACCESS_TOKEN"]

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

app = Flask(__name__)

strategy_config = {"spread_legs": [], "exit": {}}


@app.route("/config", methods=["GET", "POST"])
def config():
    """Get or update option strategy configuration."""
    if request.method == "POST":
        payload = request.get_json(force=True) or {}
        strategy_config["spread_legs"] = payload.get("spread_legs", [])
        strategy_config["exit"] = payload.get("exit", {})
        return jsonify(strategy_config)

    return jsonify(strategy_config)


@app.route("/webhook", methods=["POST"])
def webhook():
    """Execute configured legs when TradingView triggers an alert."""
    orders = strategy_config.get("spread_legs", [])
    order_ids = []
    for order in orders:
        params = {
            "tradingsymbol": order.get("symbol") or order.get("tradingsymbol"),
            "exchange": order.get("exchange", kite.EXCHANGE_NFO),
            "transaction_type": order.get("transaction_type"),
            "quantity": order.get("quantity", 1),
            "order_type": order.get("order_type", kite.ORDER_TYPE_MARKET),
            "product": order.get("product", kite.PRODUCT_MIS),
            "variety": order.get("variety", kite.VARIETY_REGULAR),
        }
        params = {k: v for k, v in params.items() if v is not None}
        order_ids.append(kite.place_order(**params))

    return jsonify({"order_ids": order_ids, "config": strategy_config})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5010, debug=True)
