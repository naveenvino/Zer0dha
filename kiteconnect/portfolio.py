from typing import Dict, List
from kiteconnect import KiteConnect

def get_current_portfolio(
    kite: KiteConnect
) -> Dict[str, List[Dict]]:
    """
    Fetches current positions and holdings and calculates their live value.

    :param kite: An initialized KiteConnect object.
    :return: A dictionary containing 'positions' and 'holdings' with live values.
    """
    try:
        positions = kite.positions()["day"] + kite.positions()["overnight"]
        holdings = kite.holdings()
    except Exception as e:
        raise DataFetchError("Failed to fetch positions or holdings.", original_exception=e)

    all_instruments = set()
    for item in positions:
        all_instruments.add(f"{item['exchange']}:{item['tradingsymbol']}")
    for item in holdings:
        all_instruments.add(f"{item['exchange']}:{item['tradingsymbol']}")

    try:
        ltp_data = kite.ltp(list(all_instruments))
    except Exception as e:
        raise DataFetchError("Failed to fetch LTP data.", original_exception=e)

    # Calculate live value for positions
    for pos in positions:
        instrument_key = f"{pos['exchange']}:{pos['tradingsymbol']}"
        if instrument_key in ltp_data and ltp_data[instrument_key]:
            pos['last_price'] = ltp_data[instrument_key]['last_price']
            pos['current_value'] = pos['last_price'] * pos['quantity']
            pos['pnl'] = (pos['last_price'] - pos['average_price']) * pos['quantity']
        else:
            pos['last_price'] = None
            pos['current_value'] = None
            pos['pnl'] = None

    # Calculate live value for holdings
    for hld in holdings:
        instrument_key = f"{hld['exchange']}:{hld['tradingsymbol']}"
        if instrument_key in ltp_data and ltp_data[instrument_key]:
            hld['last_price'] = ltp_data[instrument_key]['last_price']
            hld['current_value'] = hld['last_price'] * hld['quantity']
            hld['pnl'] = (hld['last_price'] - hld['average_price']) * hld['quantity']
        else:
            hld['last_price'] = None
            hld['current_value'] = None
            hld['pnl'] = None

    return {
        "positions": positions,
        "holdings": holdings
    }
