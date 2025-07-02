# coding: utf-8
"""Automated option selling example with stop-loss.

This script sells a NIFTY option and immediately places a stop-loss
order to limit risk. It uses regular orders and demonstrates how to
retrieve the option's last price to calculate the trigger.

Environment variables required::

    KITE_API_KEY    – Your Kite Connect API key.
    ACCESS_TOKEN    – A valid access token.

Update the ``option`` dictionary below to specify the option contract
and quantity to trade. ``stop_loss_percent`` controls how far away the
stop-loss trigger is from the sell price.
"""

import logging
import os
from kiteconnect import KiteConnect

logging.basicConfig(level=logging.DEBUG)

api_key = os.environ["KITE_API_KEY"]
access_token = os.environ["ACCESS_TOKEN"]

kite = KiteConnect(api_key=api_key)
kite.set_access_token(access_token)

# Option contract configuration
option = {
    "symbol": "NIFTY24AUG17500CE",
    "exchange": KiteConnect.EXCHANGE_NFO,
    "quantity": 75,
    "product": KiteConnect.PRODUCT_MIS,
}

# Stop-loss trigger as a percentage above the sell price
stop_loss_percent = 0.3  # 30%

instrument_key = f"{option['exchange']}:{option['symbol']}"
ltp = kite.ltp(instrument_key)[instrument_key]["last_price"]

sell_params = {
    "tradingsymbol": option["symbol"],
    "exchange": option["exchange"],
    "transaction_type": kite.TRANSACTION_TYPE_SELL,
    "quantity": option["quantity"],
    "order_type": kite.ORDER_TYPE_MARKET,
    "product": option["product"],
    "variety": kite.VARIETY_REGULAR,
}

sell_order_id = kite.place_order(**sell_params)
logging.info("Sell order placed: %s", sell_order_id)

trigger_price = round(ltp * (1 + stop_loss_percent), 1)

stop_params = {
    "tradingsymbol": option["symbol"],
    "exchange": option["exchange"],
    "transaction_type": kite.TRANSACTION_TYPE_BUY,
    "quantity": option["quantity"],
    "order_type": kite.ORDER_TYPE_SLM,
    "trigger_price": trigger_price,
    "product": option["product"],
    "variety": kite.VARIETY_REGULAR,
}

sl_order_id = kite.place_order(**stop_params)
logging.info(
    "Stop-loss order placed: %s with trigger price %s", sl_order_id, trigger_price
)
