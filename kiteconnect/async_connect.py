# -*- coding: utf-8 -*-
"""
    connect.py

    API wrapper for Kite Connect REST APIs.

    :copyright: (c) 2021 by Zerodha Technology.
    :license: see LICENSE for details.
"""
from six import StringIO, PY2
from six.moves.urllib.parse import urljoin
import csv
import json
import dateutil.parser
import hashlib
import logging
import datetime
import aiohttp
import asyncio
import warnings

from .__version__ import __version__, __title__
import kiteconnect.exceptions as ex

log = logging.getLogger(__name__)


class AsyncKiteConnect(object):
    """
    The Kite Connect API wrapper class.

    In production, you may initialise a single instance of this class per `api_key`.
    """

    # Default root API endpoint. It's possible to
    # override this by passing the `root` parameter during initialisation.
    _default_root_uri = "https://api.kite.trade"
    _default_login_uri = "https://kite.zerodha.com/connect/login"
    _default_timeout = 7  # In seconds

    # Kite connect header version
    kite_header_version = "3"

    # Constants
    # Products
    PRODUCT_MIS = "MIS"
    PRODUCT_CNC = "CNC"
    PRODUCT_NRML = "NRML"
    PRODUCT_CO = "CO"

    # Order types
    ORDER_TYPE_MARKET = "MARKET"
    ORDER_TYPE_LIMIT = "LIMIT"
    ORDER_TYPE_SLM = "SL-M"
    ORDER_TYPE_SL = "SL"

    # Varieties
    VARIETY_REGULAR = "regular"
    VARIETY_CO = "co"
    VARIETY_AMO = "amo"
    VARIETY_ICEBERG = "iceberg"
    VARIETY_AUCTION = "auction"

    # Transaction type
    TRANSACTION_TYPE_BUY = "BUY"
    TRANSACTION_TYPE_SELL = "SELL"

    # Validity
    VALIDITY_DAY = "DAY"
    VALIDITY_IOC = "IOC"
    VALIDITY_TTL = "TTL"

    # Position Type
    POSITION_TYPE_DAY = "day"
    POSITION_TYPE_OVERNIGHT = "overnight"

    # Exchanges
    EXCHANGE_NSE = "NSE"
    EXCHANGE_BSE = "BSE"
    EXCHANGE_NFO = "NFO"
    EXCHANGE_CDS = "CDS"
    EXCHANGE_BFO = "BFO"
    EXCHANGE_MCX = "MCX"
    EXCHANGE_BCD = "BCD"

    # Margins segments
    MARGIN_EQUITY = "equity"
    MARGIN_COMMODITY = "commodity"

    # Status constants
    STATUS_COMPLETE = "COMPLETE"
    STATUS_REJECTED = "REJECTED"
    STATUS_CANCELLED = "CANCELLED"

    # GTT order type
    GTT_TYPE_OCO = "two-leg"
    GTT_TYPE_SINGLE = "single"

    # GTT order status
    GTT_STATUS_ACTIVE = "active"
    GTT_STATUS_TRIGGERED = "triggered"
    GTT_STATUS_DISABLED = "disabled"
    GTT_STATUS_EXPIRED = "expired"
    GTT_STATUS_CANCELLED = "cancelled"
    GTT_STATUS_REJECTED = "rejected"
    GTT_STATUS_DELETED = "deleted"

    # URIs to various calls
    _routes = {
        "api.token": "/session/token",
        "api.token.invalidate": "/session/token",
        "api.token.renew": "/session/refresh_token",
        "user.profile": "/user/profile",
        "user.margins": "/user/margins",
        "user.margins.segment": "/user/margins/{segment}",

        "orders": "/orders",
        "trades": "/trades",

        "order.info": "/orders/{order_id}",
        "order.place": "/orders/{variety}",
        "order.modify": "/orders/{variety}/{order_id}",
        "order.cancel": "/orders/{variety}/{order_id}",
        "order.trades": "/orders/{order_id}/trades",

        "portfolio.positions": "/portfolio/positions",
        "portfolio.holdings": "/portfolio/holdings",
        "portfolio.holdings.auction": "/portfolio/holdings/auctions",
        "portfolio.positions.convert": "/portfolio/positions",

        # MF api endpoints
        "mf.orders": "/mf/orders",
        "mf.order.info": "/mf/orders/{order_id}",
        "mf.order.place": "/mf/orders",
        "mf.order.cancel": "/mf/orders/{order_id}",

        "mf.sips": "/mf/sips",
        "mf.sip.info": "/mf/sips/{sip_id}",
        "mf.sip.place": "/mf/sips",
        "mf.sip.modify": "/mf/sips/{sip_id}",
        "mf.sip.cancel": "/mf/sips/{sip_id}",

        "mf.holdings": "/mf/holdings",
        "mf.instruments": "/mf/instruments",

        "market.instruments.all": "/instruments",
        "market.instruments": "/instruments/{exchange}",
        "market.margins": "/margins/{segment}",
        "market.historical": "/instruments/historical/{instrument_token}/{interval}",
        "market.trigger_range": "/instruments/trigger_range/{transaction_type}",

        "market.quote": "/quote",
        "market.quote.ohlc": "/quote/ohlc",
        "market.quote.ltp": "/quote/ltp",

        # GTT endpoints
        "gtt": "/gtt/triggers",
        "gtt.place": "/gtt/triggers",
        "gtt.info": "/gtt/triggers/{trigger_id}",
        "gtt.modify": "/gtt/triggers/{trigger_id}",
        "gtt.delete": "/gtt/triggers/{trigger_id}",

        # Margin computation endpoints
        "order.margins": "/margins/orders",
        "order.margins.basket": "/margins/basket",
        "order.contract_note": "/charges/orders",
    }

    def __init__(self,
                 api_key,
                 access_token=None,
                 root=None,
                 debug=False,
                 timeout=None,
                 proxies=None,
                 pool=None,
                 disable_ssl=False):
        """
        Initialise a new Kite Connect client instance.

        - `api_key` is the key issued to you
        - `access_token` is the token obtained after the login flow in
            exchange for the `request_token` . Pre-login, this will default to None,
        but once you have obtained it, you should
        persist it in a database or session to pass
        to the Kite Connect class initialisation for subsequent requests.
        - `root` is the API end point root. Unless you explicitly
        want to send API requests to a non-default endpoint, this
        can be ignored.
        - `debug`, if set to True, will serialise and print requests
        and responses to stdout.
        - `timeout` is the time (seconds) for which the API client will wait for
        a request to complete before it fails. Defaults to 7 seconds
        - `proxies` to set requests proxy.
        Check [python requests documentation](http://docs.python-requests.org/en/master/user/advanced/#proxies) for usage and examples.
        - `pool` is manages request pools. It takes a dict of params accepted by HTTPAdapter as described here in [python requests documentation](http://docs.python-requests.org/en/master/api/#requests.adapters.HTTPAdapter)
        - `disable_ssl` disables the SSL verification while making a request.
        If set requests won't throw SSLError if its set to custom `root` url without SSL.
        """
        self.debug = debug
        self.api_key = api_key
        self.session_expiry_hook = None
        self.disable_ssl = disable_ssl
        self.access_token = access_token
        self.proxies = proxies if proxies else {}

        self.root = root or self._default_root_uri
        self.timeout = timeout or self._default_timeout

        # Create aiohttp client session
        self.session = aiohttp.ClientSession()

        # Disable SSL warnings only when verification is turned off
        if disable_ssl:
            warnings.filterwarnings("ignore", category=RuntimeWarning)

    async def close(self):
        """Close the underlying HTTP session."""
        if getattr(self, "session", None) is not None:
            await self.session.close()

    # ----------------------------------------------------------------
    # Context manager support
    # ----------------------------------------------------------------
    def __enter__(self):
        """Return self when entering context manager."""
        return self

    def __exit__(self, exc_type, exc, tb):
        """Close the HTTP session on exiting context manager."""
        asyncio.get_event_loop().run_until_complete(self.close())

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    def set_session_expiry_hook(self, method):
        """
        Set a callback hook for session (`TokenError` -- timeout, expiry etc.) errors.

        An `access_token` (login session) can become invalid for a number of
        reasons, but it doesn't make sense for the client to
        try and catch it during every API call.

        A callback method that handles session errors
        can be set here and when the client encounters
        a token error at any point, it'll be called.

        This callback, for instance, can log the user out of the UI,
        clear session cookies, or initiate a fresh login.
        """
        if not callable(method):
            raise TypeError("Invalid input type. Only functions are accepted.")

        self.session_expiry_hook = method

    async def set_access_token(self, access_token):
        """Set the `access_token` received after a successful authentication."""
        self.access_token = access_token

    async def login_url(self):
        """Get the remote login url to which a user should be redirected to initiate the login flow."""
        return "%s?api_key=%s&v=%s" % (self._default_login_uri, self.api_key, self.kite_header_version)

    async def generate_session(self, request_token, api_secret):
        """
        Generate user session details like `access_token` etc by exchanging `request_token`.
        Access token is automatically set if the session is retrieved successfully.

        Do the token exchange with the `request_token` obtained after the login flow,
        and retrieve the `access_token` required for all subsequent requests. The
        response contains not just the `access_token`, but metadata for
        the user who has authenticated.

        - `request_token` is the token obtained from the GET paramers after a successful login redirect.
        - `api_secret` is the API api_secret issued with the API key.
        """
        h = hashlib.sha256(self.api_key.encode("utf-8") + request_token.encode("utf-8") + api_secret.encode("utf-8"))
        checksum = h.hexdigest()

        resp = await self._post("api.token", params={
            "api_key": self.api_key,
            "request_token": request_token,
            "checksum": checksum
        })

        if "access_token" in resp:
            self.set_access_token(resp["access_token"])

        if resp["login_time"] and len(resp["login_time"]) == 19:
            resp["login_time"] = dateutil.parser.parse(resp["login_time"])

        return resp

    async def invalidate_access_token(self, access_token=None):
        """
        Kill the session by invalidating the access token.

        - `access_token` to invalidate. Default is the active `access_token`.
        """
        access_token = access_token or self.access_token
        return await self._delete("api.token.invalidate", params={
            "api_key": self.api_key,
            "access_token": access_token
        })

    async def renew_access_token(self, refresh_token, api_secret):
        """
        Renew expired `refresh_token` using valid `refresh_token`.

        - `refresh_token` is the token obtained from previous successful login flow.
        - `api_secret` is the API api_secret issued with the API key.
        """
        h = hashlib.sha256(self.api_key.encode("utf-8") + refresh_token.encode("utf-8") + api_secret.encode("utf-8"))
        checksum = h.hexdigest()

        resp = await self._post("api.token.renew", params={
            "api_key": self.api_key,
            "refresh_token": refresh_token,
            "checksum": checksum
        })

        if "access_token" in resp:
            self.set_access_token(resp["access_token"])

        return resp

    async def invalidate_refresh_token(self, refresh_token):
        """
        Invalidate refresh token.

        - `refresh_token` is the token which is used to renew access token.
        """
        return await self._delete("api.token.invalidate", params={
            "api_key": self.api_key,
            "refresh_token": refresh_token
        })

    async def margins(self, segment=None):
        """Get account balance and cash margin details for a particular segment.

        - `segment` is the trading segment (eg: equity or commodity)
        """
        if segment:
            return await self._get("user.margins.segment", url_args={"segment": segment})
        else:
            return await self._get("user.margins")

    async def profile(self):
        """Get user profile details."""
        return await self._get("user.profile")

    # orders
    async def place_order(self,
                    variety,
                    exchange,
                    tradingsymbol,
                    transaction_type,
                    quantity,
                    product,
                    order_type,
                    price=None,
                    validity=None,
                    validity_ttl=None,
                    disclosed_quantity=None,
                    trigger_price=None,
                    iceberg_legs=None,
                    iceberg_quantity=None,
                    auction_number=None,
                    tag=None):
        """Place an order."""
        params = locals()
        del (params["self"])

        for k in list(params.keys()):
            if params[k] is None:
                del (params[k])

        return await self._post("order.place",
                          url_args={"variety": variety},
                          params=params)["order_id"]

    async def modify_order(self,
                     variety,
                     order_id,
                     parent_order_id=None,
                     quantity=None,
                     price=None,
                     order_type=None,
                     trigger_price=None,
                     validity=None,
                     disclosed_quantity=None):
        """Modify an open order."""
        params = locals()
        del (params["self"])

        for k in list(params.keys()):
            if params[k] is None:
                del (params[k])

        return await self._put("order.modify",
                         url_args={"variety": variety, "order_id": order_id},
                         params=params)["order_id"]

    async def cancel_order(self, variety, order_id, parent_order_id=None):
        """Cancel an order."""
        return await self._delete("order.cancel",
                            url_args={"variety": variety, "order_id": order_id},
                            params={"parent_order_id": parent_order_id})["order_id"]

    async def exit_order(self, variety, order_id, parent_order_id=None):
        """Exit a CO order."""
        return self.cancel_order(variety, order_id, parent_order_id=parent_order_id)

    async def place_spread_order(self, legs, cancel_on_failure=True):
        """Place multiple legs of a spread sequentially.

        Each leg in ``legs`` should be a dictionary of the same parameters that
        :py:meth:`place_order` accepts. If ``cancel_on_failure`` is ``True`` and
        any leg fails to be placed, all previously placed legs are cancelled
        before the exception is propagated.

        Returns a list of order ids corresponding to each successfully placed
        leg.
        """

        order_ids = []
        for idx, leg in enumerate(legs):
            try:
                order_ids.append(self.place_order(**leg))
            except Exception:
                if cancel_on_failure and order_ids:
                    for oid, prev_leg in zip(order_ids, legs[:idx]):
                        try:
                            self.cancel_order(prev_leg.get("variety"), oid)
                        except Exception as e:
                            log.exception("Failed to cancel order %s: %s", oid, e)
                raise

        return order_ids

    def _format_response(self, data):
        """Parse and format responses."""

        if type(data) == list:
            _list = data
        elif type(data) == dict:
            _list = [data]

        for item in _list:
            # Convert date time string to datetime object
            for field in ["order_timestamp", "exchange_timestamp", "created", "last_instalment", "fill_timestamp", "timestamp", "last_trade_time"]:
                if item.get(field) and len(item[field]) == 19:
                    item[field] = dateutil.parser.parse(item[field])

        return _list[0] if type(data) == dict else _list

    # orderbook and tradebook
    async def orders(self):
        """Get list of orders."""
        return self._format_response(await self._get("orders"))

    async def order_history(self, order_id):
        """
        Get history of individual order.

        - `order_id` is the ID of the order to retrieve order history.
        """
        return self._format_response(await self._get("order.info", url_args={"order_id": order_id}))

    async def trades(self):
        """
        Retrieve the list of trades executed (all or ones under a particular order).

        An order can be executed in tranches based on market conditions.
        These trades are individually recorded under an order.
        """
        return self._format_response(await self._get("trades"))

    async def order_trades(self, order_id):
        """
        Retrieve the list of trades executed for a particular order.

        - `order_id` is the ID of the order to retrieve trade history.
        """
        return self._format_response(await self._get("order.trades", url_args={"order_id": order_id}))

    async def positions(self):
        """Retrieve the list of positions."""
        return await self._get("portfolio.positions")

    async def holdings(self):
        """Retrieve the list of equity holdings."""
        return await self._get("portfolio.holdings")

    async def get_auction_instruments(self):
        """ Retrieves list of available instruments for a auction session """
        return await self._get("portfolio.holdings.auction")

    async def convert_position(self,
                         exchange,
                         tradingsymbol,
                         transaction_type,
                         position_type,
                         quantity,
                         old_product,
                         new_product):
        """Modify an open position's product type."""
        return await self._put("portfolio.positions.convert", params={
            "exchange": exchange,
            "tradingsymbol": tradingsymbol,
            "transaction_type": transaction_type,
            "position_type": position_type,
            "quantity": quantity,
            "old_product": old_product,
            "new_product": new_product
        })

    async def mf_orders(self, order_id=None):
        """Get all mutual fund orders or individual order info."""
        if order_id:
            return self._format_response(await self._get("mf.order.info", url_args={"order_id": order_id}))
        else:
            return self._format_response(await self._get("mf.orders"))

    async def place_mf_order(self,
                       tradingsymbol,
                       transaction_type,
                       quantity=None,
                       amount=None,
                       tag=None):
        """Place a mutual fund order."""
        return await self._post("mf.order.place", params={
            "tradingsymbol": tradingsymbol,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "amount": amount,
            "tag": tag
        })

    async def cancel_mf_order(self, order_id):
        """Cancel a mutual fund order."""
        return await self._delete("mf.order.cancel", url_args={"order_id": order_id})

    async def mf_sips(self, sip_id=None):
        """Get list of all mutual fund SIP's or individual SIP info."""
        if sip_id:
            return self._format_response(await self._get("mf.sip.info", url_args={"sip_id": sip_id}))
        else:
            return self._format_response(await self._get("mf.sips"))

    async def place_mf_sip(self,
                     tradingsymbol,
                     amount,
                     instalments,
                     frequency,
                     initial_amount=None,
                     instalment_day=None,
                     tag=None):
        """Place a mutual fund SIP."""
        return await self._post("mf.sip.place", params={
            "tradingsymbol": tradingsymbol,
            "amount": amount,
            "initial_amount": initial_amount,
            "instalments": instalments,
            "frequency": frequency,
            "instalment_day": instalment_day,
            "tag": tag
        })

    async def modify_mf_sip(self,
                      sip_id,
                      amount=None,
                      status=None,
                      instalments=None,
                      frequency=None,
                      instalment_day=None):
        """Modify a mutual fund SIP."""
        return await self._put("mf.sip.modify",
                         url_args={"sip_id": sip_id},
                         params={
                             "amount": amount,
                             "status": status,
                             "instalments": instalments,
                             "frequency": frequency,
                             "instalment_day": instalment_day
                         })

    async def cancel_mf_sip(self, sip_id):
        """Cancel a mutual fund SIP."""
        return await self._delete("mf.sip.cancel", url_args={"sip_id": sip_id})

    async def mf_holdings(self):
        """Get list of mutual fund holdings."""
        return await self._get("mf.holdings")

    async def mf_instruments(self):
        """Get list of mutual fund instruments."""
        return self._parse_mf_instruments(await self._get("mf.instruments"))

    async def instruments(self, exchange=None):
        """
        Retrieve the list of market instruments available to trade.

        Note that the results could be large, several hundred KBs in size,
        with tens of thousands of entries in the list.

        - `exchange` is specific exchange to fetch (Optional)
        """
        if exchange:
            return self._parse_instruments(await self._get("market.instruments", url_args={"exchange": exchange}))
        else:
            return self._parse_instruments(await self._get("market.instruments.all"))

    async def quote(self, *instruments):
        """
        Retrieve quote for list of instruments.

        - `instruments` is a list of instruments, Instrument are in the format of `exchange:tradingsymbol`. For example NSE:INFY
        """
        ins = list(instruments)

        # If first element is a list then accept it as instruments list for legacy reason
        if len(instruments) > 0 and type(instruments[0]) == list:
            ins = instruments[0]

        data = await self._get("market.quote", params={"i": ins})
        return {key: self._format_response(data[key]) for key in data}

    async def ohlc(self, *instruments):
        """
        Retrieve OHLC and market depth for list of instruments.

        - `instruments` is a list of instruments, Instrument are in the format of `exchange:tradingsymbol`. For example NSE:INFY
        """
        ins = list(instruments)

        # If first element is a list then accept it as instruments list for legacy reason
        if len(instruments) > 0 and type(instruments[0]) == list:
            ins = instruments[0]

        return await self._get("market.quote.ohlc", params={"i": ins})

    async def ltp(self, *instruments):
        """
        Retrieve last price for list of instruments.

        - `instruments` is a list of instruments, Instrument are in the format of `exchange:tradingsymbol`. For example NSE:INFY
        """
        ins = list(instruments)

        # If first element is a list then accept it as instruments list for legacy reason
        if len(instruments) > 0 and type(instruments[0]) == list:
            ins = instruments[0]

        return await self._get("market.quote.ltp", params={"i": ins})

    async def historical_data(self, instrument_token, from_date, to_date, interval, continuous=False, oi=False):
        """
        Retrieve historical data (candles) for an instrument.

        Although the actual response JSON from the API does not have field
        names such has 'open', 'high' etc., this function call structures
        the data into an array of objects with field names. For example:

        - `instrument_token` is the instrument identifier (retrieved from the instruments()) call.
        - `from_date` is the From date (datetime object or string in format of yyyy-mm-dd HH:MM:SS.
        - `to_date` is the To date (datetime object or string in format of yyyy-mm-dd HH:MM:SS).
        - `interval` is the candle interval (minute, day, 5 minute etc.).
        - `continuous` is a boolean flag to get continuous data for futures and options instruments.
        - `oi` is a boolean flag to get open interest.
        """
        date_string_format = "%Y-%m-%d %H:%M:%S"
        from_date_string = from_date.strftime(date_string_format) if type(from_date) == datetime.datetime else from_date
        to_date_string = to_date.strftime(date_string_format) if type(to_date) == datetime.datetime else to_date

        data = await self._get("market.historical",
                         url_args={"instrument_token": instrument_token, "interval": interval},
                         params={
                             "from": from_date_string,
                             "to": to_date_string,
                             "interval": interval,
                             "continuous": 1 if continuous else 0,
                             "oi": 1 if oi else 0
                         })

        return self._format_historical(data)

    async def _format_historical(self, data):
        records = []
        for d in data["candles"]:
            record = {
                "date": dateutil.parser.parse(d[0]),
                "open": d[1],
                "high": d[2],
                "low": d[3],
                "close": d[4],
                "volume": d[5],
            }
            if len(d) == 7:
                record["oi"] = d[6]
            records.append(record)

        return records

    async def trigger_range(self, transaction_type, *instruments):
        """Retrieve the buy/sell trigger range for Cover Orders."""
        ins = list(instruments)

        # If first element is a list then accept it as instruments list for legacy reason
        if len(instruments) > 0 and type(instruments[0]) == list:
            ins = instruments[0]

        return await self._get("market.trigger_range",
                         url_args={"transaction_type": transaction_type.lower()},
                         params={"i": ins})

    async def get_gtts(self):
        """Fetch list of gtt existing in an account"""
        return await self._get("gtt")

    async def get_gtt(self, trigger_id):
        """Fetch details of a GTT"""
        return await self._get("gtt.info", url_args={"trigger_id": trigger_id})

    async def _get_gtt_payload(self, trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders):
        """Get GTT payload"""
        if type(trigger_values) != list:
            raise ex.InputException("invalid type for `trigger_values`")
        if trigger_type == self.GTT_TYPE_SINGLE and len(trigger_values) != 1:
            raise ex.InputException("invalid `trigger_values` for single leg order type")
        elif trigger_type == self.GTT_TYPE_OCO and len(trigger_values) != 2:
            raise ex.InputException("invalid `trigger_values` for OCO order type")

        condition = {
            "exchange": exchange,
            "tradingsymbol": tradingsymbol,
            "trigger_values": trigger_values,
            "last_price": last_price,
        }

        gtt_orders = []
        for o in orders:
            # Assert required keys inside gtt order.
            for req in ["transaction_type", "quantity", "order_type", "product", "price"]:
                if req not in o:
                    raise ex.InputException("`{req}` missing inside orders".format(req=req))
            gtt_orders.append({
                "exchange": exchange,
                "tradingsymbol": tradingsymbol,
                "transaction_type": o["transaction_type"],
                "quantity": int(o["quantity"]),
                "order_type": o["order_type"],
                "product": o["product"],
                "price": float(o["price"]),
            })

        return condition, gtt_orders

    async def place_gtt(
        self, trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders
    ):
        """
        Place GTT order

        - `trigger_type` The type of GTT order(single/two-leg).
        - `tradingsymbol` Trading symbol of the instrument.
        - `exchange` Name of the exchange.
        - `trigger_values` Trigger values (json array).
        - `last_price` Last price of the instrument at the time of order placement.
        - `orders` JSON order array containing following fields
            - `transaction_type` BUY or SELL
            - `quantity` Quantity to transact
            - `price` The min or max price to execute the order at (for LIMIT orders)
        """
        # Validations.
        if trigger_type not in [self.GTT_TYPE_OCO, self.GTT_TYPE_SINGLE]:
            raise ex.InputException(
                "invalid `trigger_type` %s. Supported values are `%s` or `%s`" % (
                    trigger_type,
                    self.GTT_TYPE_SINGLE,
                    self.GTT_TYPE_OCO,
                )
            )
        condition, gtt_orders = self._get_gtt_payload(trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders)

        return await self._post("gtt.place", params={
            "condition": json.dumps(condition),
            "orders": json.dumps(gtt_orders),
            "type": trigger_type})

    async def modify_gtt(
        self, trigger_id, trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders
    ):
        """
        Modify GTT order

        - `trigger_type` The type of GTT order(single/two-leg).
        - `tradingsymbol` Trading symbol of the instrument.
        - `exchange` Name of the exchange.
        - `trigger_values` Trigger values (json array).
        - `last_price` Last price of the instrument at the time of order placement.
        - `orders` JSON order array containing following fields
            - `transaction_type` BUY or SELL
            - `quantity` Quantity to transact
            - `price` The min or max price to execute the order at (for LIMIT orders)
        """
        condition, gtt_orders = self._get_gtt_payload(trigger_type, tradingsymbol, exchange, trigger_values, last_price, orders)

        return await self._put("gtt.modify",
                         url_args={"trigger_id": trigger_id},
                         params={
                             "condition": json.dumps(condition),
                             "orders": json.dumps(gtt_orders),
                             "type": trigger_type})

    async def delete_gtt(self, trigger_id):
        """Delete a GTT order."""
        return await self._delete("gtt.delete", url_args={"trigger_id": trigger_id})

    async def order_margins(self, params):
        """
        Calculate margins for requested order list considering the existing positions and open orders

        - `params` is list of orders to retrive margins detail
        """
        return await self._post("order.margins", params=params, is_json=True)

    async def basket_order_margins(self, params, consider_positions=True, mode=None):
        """
        Calculate total margins required for basket of orders including margin benefits

        - `params` is list of orders to fetch basket margin
        - `consider_positions` is a boolean to consider users positions
        - `mode` is margin response mode type. compact - Compact mode will only give the total margins
        """
        return await self._post("order.margins.basket",
                          params=params,
                          is_json=True,
                          query_params={'consider_positions': consider_positions, 'mode': mode})

    async def get_virtual_contract_note(self, params):
        """
        Calculates detailed charges order-wise for the order book
        - `params` is list of orders to fetch charges detail
        """
        return await self._post("order.contract_note",
                          params=params,
                          is_json=True)

    def _warn(self, message):
        """ Add deprecation warning message """
        warnings.simplefilter('always', DeprecationWarning)
        warnings.warn(message, DeprecationWarning)

    def _parse_instruments(self, data):
        # decode to string for Python 3
        d = data
        # Decode unicode data
        if not PY2 and type(d) == bytes:
            d = data.decode("utf-8").strip()

        records = []
        reader = csv.DictReader(StringIO(d))

        for row in reader:
            row["instrument_token"] = int(row["instrument_token"])
            row["last_price"] = float(row["last_price"])
            row["strike"] = float(row["strike"])
            row["tick_size"] = float(row["tick_size"])
            row["lot_size"] = int(row["lot_size"])

            # Parse date
            if len(row["expiry"]) == 10:
                row["expiry"] = dateutil.parser.parse(row["expiry"]).date()

            records.append(row)

        return records

    def _parse_mf_instruments(self, data):
        # decode to string for Python 3
        d = data
        if not PY2 and type(d) == bytes:
            d = data.decode("utf-8").strip()

        records = []
        reader = csv.DictReader(StringIO(d))

        for row in reader:
            row["minimum_purchase_amount"] = float(row["minimum_purchase_amount"])
            row["purchase_amount_multiplier"] = float(row["purchase_amount_multiplier"])
            row["minimum_additional_purchase_amount"] = float(row["minimum_additional_purchase_amount"])
            row["minimum_redemption_quantity"] = float(row["minimum_redemption_quantity"])
            row["redemption_quantity_multiplier"] = float(row["redemption_quantity_multiplier"])
            row["purchase_allowed"] = bool(int(row["purchase_allowed"]))
            row["redemption_allowed"] = bool(int(row["redemption_allowed"]))
            row["last_price"] = float(row["last_price"])

            # Parse date
            if len(row["last_price_date"]) == 10:
                row["last_price_date"] = dateutil.parser.parse(row["last_price_date"]).date()

            records.append(row)

        return records

    def _user_agent(self):
        return (__title__ + "-python/").capitalize() + __version__

    async def _get(self, route, url_args=None, params=None, is_json=False):
        """Alias for sending a GET request."""
        return await self._request(route, "GET", url_args=url_args, params=params, is_json=is_json)

    async def _post(self, route, url_args=None, params=None, is_json=False, query_params=None):
        """Alias for sending a POST request."""
        return await self._request(route, "POST", url_args=url_args, params=params, is_json=is_json, query_params=query_params)

    async def _put(self, route, url_args=None, params=None, is_json=False, query_params=None):
        """Alias for sending a PUT request."""
        return await self._request(route, "PUT", url_args=url_args, params=params, is_json=is_json, query_params=query_params)

    async def _delete(self, route, url_args=None, params=None, is_json=False):
        """Alias for sending a DELETE request."""
        return await self._request(route, "DELETE", url_args=url_args, params=params, is_json=is_json)

    async def _request(self, route, method, url_args=None, params=None, is_json=False, query_params=None):
        """Make an HTTP request."""
        # Form a restful URL
        if url_args:
            uri = self._routes[route].format(**url_args)
        else:
            uri = self._routes[route]

        url = urljoin(self.root, uri)

        # Custom headers
        headers = {
            "X-Kite-Version": self.kite_header_version,
            "User-Agent": self._user_agent()
        }

        if self.api_key and self.access_token:
            # set authorization header
            auth_header = self.api_key + ":" + self.access_token
            headers["Authorization"] = "token {}".format(auth_header)

        if self.debug:
            log.debug("Request: {method} {url} {params} {headers}".format(method=method, url=url, params=params, headers=headers))

        # prepare url query params
        if method in ["GET", "DELETE"]:
            query_params = params

        json_data = params if (method in ["POST", "PUT"] and is_json) else None
        data = params if (method in ["POST", "PUT"] and not is_json) else None

        try:
            async with self.session.request(
                method,
                url,
                json=json_data,
                data=data,
                params=query_params,
                headers=headers,
                ssl=not self.disable_ssl,
                allow_redirects=True,
                timeout=self.timeout,
            ) as r:
                if self.debug:
                    log.debug("Response: {code} {content}".format(code=r.status, content=await r.text()))

                content_type = r.headers.get("content-type", "")
                if "json" in content_type:
                    try:
                        data = await r.json()
                    except Exception:
                        raise ex.DataException(
                            "Couldn't parse the JSON response received from the server: {content}".format(content=await r.text())
                        )

                    if data.get("status") == "error" or data.get("error_type"):
                        if self.session_expiry_hook and r.status == 403 and data.get("error_type") == "TokenException":
                            self.session_expiry_hook()

                        exp = getattr(ex, data.get("error_type"), ex.GeneralException)
                        raise exp(data.get("message"), code=r.status)

                    return data.get("data")
                elif "csv" in content_type:
                    return await r.read()
                else:
                    raise ex.DataException(
                        "Unknown Content-Type ({content_type}) with response: ({content})".format(
                            content_type=content_type,
                            content=await r.text(),
                        )
                    )
        except Exception as e:
            raise e

