# -*- coding: utf-8 -*-
"""
Kite Connect API client for Python -- [kite.trade](https://kite.trade).

Zerodha Technology Pvt. Ltd. (c) 2021

License
-------
KiteConnect Python library is licensed under the MIT License

The library
-----------
Kite Connect is a set of REST-like APIs that expose
many capabilities required to build a complete
investment and trading platform. Execute orders in
real time, manage user portfolio, stream live market
data (WebSockets), and more, with the simple HTTP API collection

This module provides an easy to use abstraction over the HTTP APIs.
The HTTP calls have been converted to methods and their JSON responses
are returned as native Python structures, for example, dicts, lists, bools etc.
See the **[Kite Connect API documentation](https://kite.trade/docs/connect/v3/)**
for the complete list of APIs, supported parameters and values, and response formats.

Getting started
---------------
    #!python
    import logging
    from kiteconnect import KiteConnect

    logging.basicConfig(level=logging.DEBUG)

    kite = KiteConnect(api_key="your_api_key")

    # Redirect the user to the login url obtained
    # from kite.login_url(), and receive the request_token
    # from the registered redirect url after the login flow.
    # Once you have the request_token, obtain the access_token
    # as follows.

    data = kite.generate_session("request_token_here", api_secret="your_secret")
    kite.set_access_token(data["access_token"])

    # Place an order
    try:
        order_id = kite.place_order(variety=kite.VARIETY_REGULAR,
                                    tradingsymbol="INFY",
                                    exchange=kite.EXCHANGE_NSE,
                                    transaction_type=kite.TRANSACTION_TYPE_BUY,
                                    quantity=1,
                                    order_type=kite.ORDER_TYPE_MARKET,
                                    product=kite.PRODUCT_CNC,
                                    validity=kite.VALIDITY_DAY)

        logging.info("Order placed. ID is: {}".format(order_id))
    except Exception as e:
        logging.info("Order placement failed: {}".format(e.message))

    # Fetch all orders
    kite.orders()

    # Get instruments
    kite.instruments()

    # Place an mutual fund order
    kite.place_mf_order(
        tradingsymbol="INF090I01239",
        transaction_type=kite.TRANSACTION_TYPE_BUY,
        amount=5000,
        tag="mytag"
    )

    # Cancel a mutual fund order
    kite.cancel_mf_order(order_id="order_id")

    # Get mutual fund instruments
    kite.mf_instruments()

A typical web application
-------------------------
In a typical web application where a new instance of
views, controllers etc. are created per incoming HTTP
request, you will need to initialise a new instance of
Kite client per request as well. This is because each
individual instance represents a single user that's
authenticated, unlike an **admin** API where you may
use one instance to manage many users.

Hence, in your web application, typically:

- You will initialise an instance of the Kite client
- Redirect the user to the `login_url()`
- At the redirect url endpoint, obtain the
`request_token` from the query parameters
- Initialise a new instance of Kite client,
use `generate_session()` to obtain the `access_token`
along with authenticated user data
- Store this response in a session and use the
stored `access_token` and initialise instances
of Kite client for subsequent API calls.

Exceptions
----------
Kite Connect client saves you the hassle of detecting API errors
by looking at HTTP codes or JSON error responses. Instead,
it raises aptly named **[exceptions](exceptions.m.html)** that you can catch.
"""

from __future__ import unicode_literals, absolute_import

from kiteconnect import exceptions
from kiteconnect.connect import KiteConnect
from kiteconnect.ticker import KiteTicker
from kiteconnect.async_connect import AsyncKiteConnect
from kiteconnect.async_ticker import AsyncKiteTicker
from kiteconnect.advanced_orders import place_cover_order, place_bracket_order, place_amo_order, place_iceberg_order
from kiteconnect.portfolio import get_current_portfolio
from kiteconnect.risk_management import set_stop_loss, set_target_profit
from kiteconnect.historical_data_utils import get_historical_data_dataframe
from kiteconnect.technical_indicators import calculate_sma
from kiteconnect.charting import plot_candlestick_chart
from kiteconnect.config_manager import save_config, load_config
from kiteconnect.error_handling import KiteConnectError, OrderPlacementError, DataFetchError, InvalidRequestError
from kiteconnect.logging_config import setup_logging
from kiteconnect.predictive_models import train_price_prediction_model, predict_price
from kiteconnect.realtime_data import RealtimeMarketDataProcessor
from kiteconnect.trade_journal import init_db, insert_trade, get_all_trades, get_trades_dataframe, analyze_trades
from kiteconnect.data_cache import save_historical_data, load_historical_data
from kiteconnect.backtesting.core import run_backtest
from kiteconnect.backtesting.metrics import calculate_performance_metrics
from kiteconnect.backtesting.visualizer import plot_equity_curve
from kiteconnect.backtesting.optimizer import optimize_strategy_parameters
from kiteconnect.backtesting.analysis import walk_forward_analysis
from kiteconnect.risk_management.dashboard import RiskManagementDashboard
from kiteconnect.risk_management.alerts import PnLAlert
from kiteconnect.ml import *
from kiteconnect.notifications import *

__all__ = [
    "KiteConnect",
    "KiteTicker",
    "AsyncKiteConnect",
    "AsyncKiteTicker",
    "exceptions",
    "place_cover_order",
    "place_bracket_order",
    "place_amo_order",
    "place_iceberg_order",
    "get_current_portfolio",
    "run_backtest",
    "set_stop_loss",
    "set_target_profit",
    "get_historical_data_dataframe",
    "calculate_sma",
    "calculate_rsi",
    "calculate_macd",
    "calculate_bollinger_bands",
    "calculate_stochastic_oscillator",
    "calculate_atr",
    "plot_candlestick_chart",
    "send_telegram_message",
    "save_config",
    "load_config",
    "KiteConnectError",
    "OrderPlacementError",
    "DataFetchError",
    "InvalidRequestError",
    "setup_logging",
    "train_price_prediction_model",
    "predict_price",
    "RealtimeMarketDataProcessor",
    "init_db",
    "insert_trade",
    "get_all_trades",
    "get_trades_dataframe",
    "analyze_trades",
    "save_historical_data",
    "load_historical_data",
    "run_backtest",
    "calculate_performance_metrics",
    "plot_equity_curve",
    "optimize_strategy_parameters",
    "walk_forward_analysis",
    "RiskManagementDashboard",
    "PnLAlert",
    "create_features",
    "PredictiveModel",
    "send_email",
]
