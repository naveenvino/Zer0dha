from typing import Dict, List, Optional
from kiteconnect import KiteConnect
from kiteconnect.error_handling import InvalidRequestError, OrderPlacementError, DataFetchError

def set_stop_loss(
    kite: KiteConnect,
    position: Dict,
    stop_loss_percentage: Optional[float] = None,
    stop_loss_points: Optional[float] = None,
    tag: Optional[str] = None,
) -> str:
    """
    Sets a stop-loss order for a given open position.

    :param kite: An initialized KiteConnect object.
    :param position: A dictionary representing the open position (from kite.positions()).
    :param stop_loss_percentage: Stop loss as a percentage of the entry price.
    :param stop_loss_points: Stop loss as absolute points from the entry price.
    :param tag: An optional tag to identify the order.
    :return: The order ID of the placed stop-loss order.
    """
    if not (stop_loss_percentage or stop_loss_points):
        raise InvalidRequestError("Either stop_loss_percentage or stop_loss_points must be provided.")

    tradingsymbol = position['tradingsymbol']
    exchange = position['exchange']
    quantity = position['quantity']
    average_price = position['average_price']
    transaction_type = kite.TRANSACTION_TYPE_SELL if position['quantity'] > 0 else kite.TRANSACTION_TYPE_BUY

    # Fetch current LTP
    try:
        ltp_data = kite.ltp([f"{exchange}:{tradingsymbol}"])
        current_ltp = ltp_data[f"{exchange}:{tradingsymbol}"]['last_price']
    except Exception as e:
        raise DataFetchError(f"Failed to fetch LTP for {tradingsymbol}", original_exception=e)

    if stop_loss_percentage:
        trigger_price = current_ltp * (1 - stop_loss_percentage / 100) if transaction_type == kite.TRANSACTION_TYPE_BUY \
                        else current_ltp * (1 + stop_loss_percentage / 100)
    elif stop_loss_points:
        trigger_price = current_ltp - stop_loss_points if transaction_type == kite.TRANSACTION_TYPE_BUY \
                        else current_ltp + stop_loss_points

    # Place SL-M order
    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=exchange,
            tradingsymbol=tradingsymbol,
            transaction_type=transaction_type,
            quantity=abs(quantity),
            product=kite.PRODUCT_MIS, # Assuming MIS for intraday positions
            order_type=kite.ORDER_TYPE_SLM,
            trigger_price=round(trigger_price, 2),
            tag=tag,
        )
        return order_id
    except Exception as e:
        raise OrderPlacementError(f"Failed to place stop-loss order for {tradingsymbol}", original_exception=e)

def set_target_profit(
    kite: KiteConnect,
    position: Dict,
    target_profit_percentage: Optional[float] = None,
    target_profit_points: Optional[float] = None,
    tag: Optional[str] = None,
) -> str:
    """
    Sets a target profit order for a given open position.

    :param kite: An initialized KiteConnect object.
    :param position: A dictionary representing the open position (from kite.positions()).
    :param target_profit_percentage: Target profit as a percentage of the entry price.
    :param target_profit_points: Target profit as absolute points from the entry price.
    :param tag: An optional tag to identify the order.
    :return: The order ID of the placed target profit order.
    """
    if not (target_profit_percentage or target_profit_points):
        raise InvalidRequestError("Either target_profit_percentage or target_profit_points must be provided.")

    tradingsymbol = position['tradingsymbol']
    exchange = position['exchange']
    quantity = position['quantity']
    average_price = position['average_price']
    transaction_type = kite.TRANSACTION_TYPE_BUY if position['quantity'] > 0 else kite.TRANSACTION_TYPE_SELL

    # Fetch current LTP
    try:
        ltp_data = kite.ltp([f"{exchange}:{tradingsymbol}"])
        current_ltp = ltp_data[f"{exchange}:{tradingsymbol}"]['last_price']
    except Exception as e:
        raise DataFetchError(f"Failed to fetch LTP for {tradingsymbol}", original_exception=e)

    if target_profit_percentage:
        price = current_ltp * (1 + target_profit_percentage / 100) if transaction_type == kite.TRANSACTION_TYPE_BUY 
                else current_ltp * (1 - target_profit_percentage / 100)
    elif target_profit_points:
        price = current_ltp + target_profit_points if transaction_type == kite.TRANSACTION_TYPE_BUY 
                else current_ltp - target_profit_points

    # Place LIMIT order
    try:
        order_id = kite.place_order(
            variety=kite.VARIETY_REGULAR,
            exchange=exchange,
            tradingsymbol=tradingsymbol,
            transaction_type=transaction_type,
            quantity=abs(quantity),
            product=kite.PRODUCT_MIS, # Assuming MIS for intraday positions
            order_type=kite.ORDER_TYPE_LIMIT,
            price=round(price, 2),
            tag=tag,
        )
        return order_id
    except Exception as e:
        raise OrderPlacementError(f"Failed to place target profit order for {tradingsymbol}", original_exception=e)
