# The Kite Connect API Python client - v4

[![PyPI](https://img.shields.io/pypi/v/kiteconnect.svg)](https://pypi.python.org/pypi/kiteconnect)
[![Build Status](https://travis-ci.org/zerodhatech/pykiteconnect.svg?branch=kite3)](https://travis-ci.org/zerodhatech/pykiteconnect)
[![Windows Build Status](https://ci.appveyor.com/api/projects/status/github/zerodhatech/pykiteconnect?svg=true)](https://ci.appveyor.com/project/rainmattertech/pykiteconnect)
[![codecov.io](https://codecov.io/gh/zerodhatech/pykiteconnect/branch/kite3/graphs/badge.svg?branch=kite3)](https://codecov.io/gh/zerodhatech/pykiteconnect/branch/kite3)

The official Python client for communicating with the [Kite Connect API](https://kite.trade).

Kite Connect is a set of REST-like APIs that expose many capabilities required to build a complete investment and trading platform. Execute orders in real time, manage user portfolio, stream live market data (WebSockets), and more, with the simple HTTP API collection.

[Zerodha Technology](https://zerodha.com) (c) 2021. Licensed under the MIT License.

## Documentation

- [Python client documentation](https://kite.trade/docs/pykiteconnect/v4)
- [Kite Connect HTTP API documentation](https://kite.trade/docs/connect/v3)

## v4 - Breaking changes

- Renamed ticker fields as per [kite connect doc](https://kite.trade/docs/connect/v3/websocket/#quote-packet-structure)
- Renamed `bsecds` to `bcd` in `ticker.EXCHANGE_MAP`

## v5 - Breaking changes

- **Drop Support for Python 2.7**: Starting from version v5, support for Python 2.7 has been discontinued. This decision was made due to the [announcement](https://github.com/actions/setup-python/issues/672) by `setup-python`, which stopped supporting Python 2.x since May 2023.

- **For Python 2.x Users**: If you are using Python 2.x, you can continue using the `kiteconnect` library, but please stick to the <= 4.x.x versions of the library. You can find the previous releases on the [PyKiteConnect GitHub Releases](https://github.com/zerodha/pykiteconnect/releases) page.
- **Python typing support requires Python 3.7 or higher** to take advantage of the type hints included in this package.

## Installing the client

You can install the pre release via pip

```
pip install --upgrade kiteconnect
```

Its recommended to update `setuptools` to latest if you are facing any issue while installing

```
pip install -U pip setuptools
```

Since some of the dependencies uses C extensions it has to compiled before installing the package.

### Linux, BSD and macOS

- On Linux, and BSDs, you will need a C compiler (such as GCC).

#### Debian/Ubuntu

```
apt-get install libffi-dev python-dev python3-dev
```

#### Centos/RHEL/Fedora

```
yum install libffi-devel python3-devel python-devel
```

#### macOS/OSx

```
xcode-select --install
```

### Microsoft Windows

Each Python version uses a specific compiler version (e.g. CPython 2.7 uses Visual C++ 9.0, CPython 3.3 uses Visual C++ 10.0, etc). So, you need to install the compiler version that corresponds to your Python version

- Python 2.6, 2.7, 3.0, 3.1, 3.2 - [Microsoft Visual C++ 9.0](https://wiki.python.org/moin/WindowsCompilers#Microsoft_Visual_C.2B-.2B-_9.0_standalone:_Visual_C.2B-.2B-_Compiler_for_Python_2.7_.28x86.2C_x64.29)
- Python 3.3, 3.4 - [Microsoft Visual C++ 10.0](https://wiki.python.org/moin/WindowsCompilers#Microsoft_Visual_C.2B-.2B-_10.0_standalone:_Windows_SDK_7.1_.28x86.2C_x64.2C_ia64.29)
- Python 3.5, 3.6 - [Microsoft Visual C++ 14.0](https://wiki.python.org/moin/WindowsCompilers#Microsoft_Visual_C.2B-.2B-_14.0_standalone:_Visual_C.2B-.2B-_Build_Tools_2015_.28x86.2C_x64.2C_ARM.29)

For more details check [official Python documentation](https://wiki.python.org/moin/WindowsCompilers).

## Building an algo trading bot

1. **Setup login** – Use `KiteConnect` to obtain an `access_token` after the user logs in.
2. **Subscribe to WebSocket data** – Connect using `KiteTicker` and subscribe to the required instrument tokens.
3. **Place orders** – Call `KiteConnect.place_order()` to execute trades programmatically.
4. **Handle errors** – Catch `KiteException` derivatives to gracefully handle API or network issues.

For reference, see the login and order example from [Issue&nbsp;1](examples/simple.py) and the WebSocket example from [Issue&nbsp;2](examples/ticker.py).

## API usage

```python
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
    order_id = kite.place_order(tradingsymbol="INFY",
                                exchange=kite.EXCHANGE_NSE,
                                transaction_type=kite.TRANSACTION_TYPE_BUY,
                                quantity=1,
                                variety=kite.VARIETY_AMO,
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

# Close the session when done
kite.close()

# Or use as a context manager
with KiteConnect(api_key="your_api_key") as ck:
    ck.instruments()
```

Refer to the [Python client documentation](https://kite.trade/docs/pykiteconnect/v4) for the complete list of supported methods.

## Async API usage

```python
import asyncio
from kiteconnect import AsyncKiteConnect

async def main():
    kite = AsyncKiteConnect(api_key="your_api_key")
    data = await kite.generate_session("request_token_here", api_secret="your_secret")
    kite.set_access_token(data["access_token"])
    orders = await kite.orders()
    await kite.close()

asyncio.run(main())
```


## WebSocket usage

```python
import logging
from kiteconnect import KiteTicker

logging.basicConfig(level=logging.DEBUG)

# Initialise
kws = KiteTicker("your_api_key", "your_access_token")

def on_ticks(ws, ticks):
    # Callback to receive ticks.
    logging.debug("Ticks: {}".format(ticks))

def on_connect(ws, response):
    # Callback on successful connect.
    # Subscribe to a list of instrument_tokens (RELIANCE and ACC here).
    ws.subscribe([738561, 5633])

    # Set RELIANCE to tick in `full` mode.
    ws.set_mode(ws.MODE_FULL, [738561])

def on_close(ws, code, reason):
    # On connection close stop the main loop
    # Reconnection will not happen after executing `ws.stop()`
    ws.stop()

# Assign the callbacks.
kws.on_ticks = on_ticks
kws.on_connect = on_connect
kws.on_close = on_close

# Infinite loop on the main thread. Nothing after this will run.
# You have to use the pre-defined callbacks to manage subscriptions.
kws.connect()
```

### Async WebSocket usage

```python
import asyncio
from kiteconnect import AsyncKiteTicker

async def main():
    kws = AsyncKiteTicker("your_api_key", "your_access_token")

    async def on_ticks(ws, ticks):
        print(ticks)

    kws.on_ticks = on_ticks
    await kws.connect()

asyncio.run(main())
```

## Run unit tests

Install the development dependencies and install the project in editable mode first:

```sh
pip install -r dev_requirements.txt && pip install -e .
```

This includes `autobahn[twisted]==19.11.2` which is required for the WebSocket tests.

```sh
python setup.py test
```

or

```sh
pytest -s tests/unit --cov-report html:cov_html --cov=./
```

## Run integration tests

```sh
pytest -s tests/integration/ --cov-report html:cov_html --cov=./  --api-key api_key --access-token access_token
```

## Generate documentation

```sh
pip install pdoc

pdoc --html --html-dir docs kiteconnect
```

## TradingView integration

`examples/tradingview_webhook.py` exposes a small Flask server that accepts
TradingView webhooks and forwards them to `KiteConnect`.

### Deployment steps

1. **Install dependencies**
   ```sh
   pip install Flask && pip install -e .
   ```
2. **Export credentials** – the server relies on a few environment variables:
   - `KITE_API_KEY` – your API key from the Kite developer console.
   - `KITE_API_SECRET` – API secret used when generating the access token.
   - `ACCESS_TOKEN` – a valid token obtained via `KiteConnect.generate_session`.

   ```sh
   export KITE_API_KEY="your_api_key"
   export KITE_API_SECRET="your_api_secret"
   export ACCESS_TOKEN="your_access_token"
   ```
3. **Start the server**
   ```sh
   python examples/tradingview_webhook.py
   ```
4. **Configure TradingView** to POST alerts to `http://<server-ip>:5000/webhook`.

TradingView should POST JSON to `/webhook` using the following structure:

```json
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
```

Each item in `orders` maps to the arguments of
`KiteConnect.place_order`. Multiple items may be provided to execute
multi-leg option strategies.
For a standalone demonstration of multi-leg spreads refer to
[`examples/multi_leg_option.py`](examples/multi_leg_option.py).
Exit orders can be submitted via the `exit_orders` key which maps to the
arguments of `KiteConnect.exit_order`.

An extended example `examples/nifty_option_seller.py` demonstrates how to
configure a NIFTY option selling strategy via a `/config` endpoint and trigger
it using TradingView alerts posted to `/webhook`.

The script `examples/option_seller_with_stoploss.py` shows a standalone
automation that sells a single option contract and places a corresponding
stop-loss order for risk management.

## Changelog

[Check release notes](https://github.com/zerodha/pykiteconnect/releases)
