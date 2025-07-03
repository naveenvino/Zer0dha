from typing import Optional
from typing import List
from kiteconnect import KiteConnect
from kiteconnect.error_handling import InvalidRequestError, OrderPlacementError

def place_cover_order(
    kite: KiteConnect,
    tradingsymbol: str,
    exchange: str,
    transaction_type: str,
    quantity: int,
    product: str,
    order_type: str,
    price: Optional[float] = None,
    trigger_price: float = None,
    tag: Optional[str] = None,
) -> str:
    """
    Place a Cover Order (CO).

    A Cover Order combines a market or limit order with a compulsory stop-loss order.
    The stop-loss order is placed simultaneously with the main order.

    :param kite: An initialized KiteConnect object.
    :param tradingsymbol: The instrument's trading symbol (e.g., "INFY").
    :param exchange: The exchange on which the order is to be placed (e.g., kite.EXCHANGE_NSE).
    :param transaction_type: "BUY" or "SELL" (kite.TRANSACTION_TYPE_BUY or kite.TRANSACTION_TYPE_SELL).
    :param quantity: The quantity of the instrument to trade.
    :param product: The product type (e.g., kite.PRODUCT_MIS).
    :param order_type: The order type (e.g., kite.ORDER_TYPE_MARKET, kite.ORDER_TYPE_LIMIT).
    :param price: The price for LIMIT orders. Required for LIMIT and SL orders.
    :param trigger_price: The trigger price for the stop-loss leg of the CO. Required for CO.
    :param tag: An optional tag to identify the order.
    :return: The order ID.
    """
    if not all([tradingsymbol, exchange, transaction_type, quantity, product, order_type]):
        raise InvalidRequestError("Missing required parameters for placing cover order.")
    if not isinstance(quantity, int) or quantity <= 0:
        raise InvalidRequestError("Quantity must be a positive integer.")
    if trigger_price is None:
        raise InvalidRequestError("trigger_price is required for Cover Orders.")

    try:
        return kite.place_order(
            variety=kite.VARIETY_CO,
            exchange=exchange,
            tradingsymbol=tradingsymbol,
            transaction_type=transaction_type,
            quantity=quantity,
            product=product,
            order_type=order_type,
            price=price,
            trigger_price=trigger_price,
            tag=tag,
        )
    except Exception as e:
        raise OrderPlacementError(f"Failed to place cover order for {tradingsymbol}", original_exception=e)

def modify_cover_order(
    kite: KiteConnect,
    order_id: str,
    quantity: Optional[int] = None,
    price: Optional[float] = None,
    trigger_price: Optional[float] = None,
) -> str:
    """
    Modify an open Cover Order (CO).

    :param kite: An initialized KiteConnect object.
    :param order_id: The ID of the order to modify.
    :param quantity: The new quantity.
    :param price: The new price for LIMIT orders.
    :param trigger_price: The new trigger price for the stop-loss leg.
    :return: The modified order ID.
    """
    try:
        return kite.modify_order(
            variety=kite.VARIETY_CO,
            order_id=order_id,
            quantity=quantity,
            price=price,
            trigger_price=trigger_price,
        )
    except Exception as e:
        raise OrderPlacementError(f"Failed to modify cover order {order_id}", original_exception=e)

def place_bracket_order(
    kite: KiteConnect,
    tradingsymbol: str,
    exchange: str,
    transaction_type: str,
    quantity: int,
    price: Optional[float] = None,
    disclosed_quantity: Optional[int] = None,
    validity: Optional[str] = None,
    tag: Optional[str] = None,
    squareoff: float = None,
    stoploss: float = None,
    trailing_stoploss: float = None,
) -> str:
    """
    Place a Bracket Order (BO).

    A Bracket Order is a three-legged order that includes a main order, a stop-loss order,
    and a target order. It allows traders to limit their losses and lock in profits.

    :param kite: An initialized KiteConnect object.
    :param tradingsymbol: The instrument's trading symbol (e.g., "INFY").
    :param exchange: The exchange on which the order is to be placed (e.g., kite.EXCHANGE_NSE).
    :param transaction_type: "BUY" or "SELL" (kite.TRANSACTION_TYPE_BUY or kite.TRANSACTION_TYPE_SELL).
    :param quantity: The quantity of the instrument to trade.
    :param price: The price for LIMIT orders. Required for LIMIT and SL orders.
    :param disclosed_quantity: The quantity that should be disclosed in the market depth.
    :param validity: The validity of the order (e.g., kite.VALIDITY_DAY, kite.VALIDITY_IOC).
    :param tag: An optional tag to identify the order.
    :param squareoff: The target price difference (in absolute points) for profit booking.
    :param stoploss: The stop-loss price difference (in absolute points).
    :param trailing_stoploss: The trailing stop-loss value (in absolute points).
    :return: The order ID.
    """
    if squareoff is None or stoploss is None:
        raise InvalidRequestError("squareoff and stoploss are required for Bracket Orders.")

    try:
        return kite.place_order(
            variety=kite.VARIETY_REGULAR, # Corrected to REGULAR
            exchange=exchange,
            tradingsymbol=tradingsymbol,
            transaction_type=transaction_type,
            quantity=quantity,
            product=kite.PRODUCT_MIS,  # Bracket orders are typically MIS product type
            order_type=kite.ORDER_TYPE_LIMIT, # BOs are typically limit orders
            price=price,
            disclosed_quantity=disclosed_quantity,
            validity=validity,
            tag=tag,
            squareoff=squareoff,
            stoploss=stoploss,
            trailing_stoploss=trailing_stoploss,
        )
    except Exception as e:
        raise OrderPlacementError(f"Failed to place bracket order for {tradingsymbol}", original_exception=e)

def modify_bracket_order(
    kite: KiteConnect,
    order_id: str,
    quantity: Optional[int] = None,
    price: Optional[float] = None,
    trigger_price: Optional[float] = None,
    squareoff: Optional[float] = None,
    stoploss: Optional[float] = None,
    trailing_stoploss: Optional[float] = None,
) -> str:
    """
    Modify an open Bracket Order (BO).

    :param kite: An initialized KiteConnect object.
    :param order_id: The ID of the order to modify.
    :param quantity: The new quantity.
    :param price: The new price for the main order.
    :param trigger_price: The new trigger price for the stop-loss leg.
    :param squareoff: The new target price difference.
    :param stoploss: The new stop-loss price difference.
    :param trailing_stoploss: The new trailing stop-loss value.
    :return: The modified order ID.
    """
    try:
        return kite.modify_order(
            variety=kite.VARIETY_REGULAR, # BOs are modified as regular orders
            order_id=order_id,
            quantity=quantity,
            price=price,
            trigger_price=trigger_price,
            squareoff=squareoff,
            stoploss=stoploss,
            trailing_stoploss=trailing_stoploss,
        )
    except Exception as e:
        raise OrderPlacementError(f"Failed to modify bracket order {order_id}", original_exception=e)

def place_amo_order(
    kite: KiteConnect,
    tradingsymbol: str,
    exchange: str,
    transaction_type: str,
    quantity: int,
    product: str,
    order_type: str,
    price: Optional[float] = None,
    validity: Optional[str] = None,
    disclosed_quantity: Optional[int] = None,
    trigger_price: Optional[float] = None,
    tag: Optional[str] = None,
) -> str:
    """
    Place an After Market Order (AMO).

    AMO orders are placed after regular market hours and are executed during the next trading session.

    :param kite: An initialized KiteConnect object.
    :param tradingsymbol: The instrument's trading symbol (e.g., "INFY").
    :param exchange: The exchange on which the order is to be placed (e.g., kite.EXCHANGE_NSE).
    :param transaction_type: "BUY" or "SELL" (kite.TRANSACTION_TYPE_BUY or kite.TRANSACTION_TYPE_SELL).
    :param quantity: The quantity of the instrument to trade.
    :param product: The product type (e.g., kite.PRODUCT_CNC, kite.PRODUCT_MIS).
    :param order_type: The order type (e.g., kite.ORDER_TYPE_MARKET, kite.ORDER_TYPE_LIMIT).
    :param price: The price for LIMIT orders. Required for LIMIT and SL orders.
    :param validity: The validity of the order (e.g., kite.VALIDITY_DAY).
    :param disclosed_quantity: The quantity that should be disclosed in the market depth.
    :param trigger_price: The trigger price for SL and SL-M orders.
    :param tag: An optional tag to identify the order.
    :return: The order ID.
    """
    try:
        return kite.place_order(
            variety=kite.VARIETY_AMO,
            exchange=exchange,
            tradingsymbol=tradingsymbol,
            transaction_type=transaction_type,
            quantity=quantity,
            product=product,
            order_type=order_type,
            price=price,
            validity=validity,
            disclosed_quantity=disclosed_quantity,
            trigger_price=trigger_price,
            tag=tag,
        )
    except Exception as e:
        raise OrderPlacementError(f"Failed to place AMO order for {tradingsymbol}", original_exception=e)

def modify_amo_order(
    kite: KiteConnect,
    order_id: str,
    quantity: Optional[int] = None,
    price: Optional[float] = None,
    order_type: Optional[str] = None,
    validity: Optional[str] = None,
    disclosed_quantity: Optional[int] = None,
    trigger_price: Optional[float] = None,
) -> str:
    """
    Modify an open After Market Order (AMO).

    :param kite: An initialized KiteConnect object.
    :param order_id: The ID of the order to modify.
    :param quantity: The new quantity.
    :param price: The new price.
    :param order_type: The new order type.
    :param validity: The new validity.
    :param disclosed_quantity: The new disclosed quantity.
    :param trigger_price: The new trigger price.
    :return: The modified order ID.
    """
    try:
        return kite.modify_order(
            variety=kite.VARIETY_AMO,
            order_id=order_id,
            quantity=quantity,
            price=price,
            order_type=order_type,
            validity=validity,
            disclosed_quantity=disclosed_quantity,
            trigger_price=trigger_price,
        )
    except Exception as e:
        raise OrderPlacementError(f"Failed to modify AMO order {order_id}", original_exception=e)

def place_iceberg_order(
    kite: KiteConnect,
    tradingsymbol: str,
    exchange: str,
    transaction_type: str,
    quantity: int,
    product: str,
    order_type: str,
    price: Optional[float] = None,
    validity: Optional[str] = None,
    disclosed_quantity: Optional[int] = None,
    trigger_price: Optional[float] = None,
    tag: Optional[str] = None,
    iceberg_legs: int = None,
    iceberg_quantity: int = None,
) -> str:
    """
    Place an Iceberg Order.

    Iceberg orders are large orders split into smaller, visible "legs" to avoid impacting the market price.

    :param kite: An initialized KiteConnect object.
    :param tradingsymbol: The instrument's trading symbol (e.g., "INFY").
    :param exchange: The exchange on which the order is to be placed (e.g., kite.EXCHANGE_NSE).
    :param transaction_type: "BUY" or "SELL" (kite.TRANSACTION_TYPE_BUY or kite.TRANSACTION_TYPE_SELL).
    :param quantity: The total quantity of the instrument to trade.
    :param product: The product type (e.g., kite.PRODUCT_CNC, kite.PRODUCT_MIS).
    :param order_type: The order type (e.g., kite.ORDER_TYPE_MARKET, kite.ORDER_TYPE_LIMIT).
    :param price: The price for LIMIT orders. Required for LIMIT and SL orders.
    :param validity: The validity of the order (e.g., kite.VALIDITY_DAY).
    :param disclosed_quantity: The quantity that should be disclosed in the market depth.
    :param trigger_price: The trigger price for SL and SL-M orders.
    :param tag: An optional tag to identify the order.
    :param iceberg_legs: The number of legs the iceberg order should be split into.
    :param iceberg_quantity: The quantity of each leg (if not specified, quantity will be split equally).
    :return: The order ID.
    """
    if iceberg_legs is None:
        raise InvalidRequestError("iceberg_legs is required for Iceberg Orders.")

    try:
        return kite.place_order(
            variety=kite.VARIETY_ICEBERG,
            exchange=exchange,
            tradingsymbol=tradingsymbol,
            transaction_type=transaction_type,
            quantity=quantity,
            product=product,
            order_type=order_type,
            price=price,
            validity=validity,
            disclosed_quantity=disclosed_quantity,
            trigger_price=trigger_price,
            tag=tag,
            iceberg_legs=iceberg_legs,
            iceberg_quantity=iceberg_quantity,
        )
    except Exception as e:
        raise OrderPlacementError(f"Failed to place iceberg order for {tradingsymbol}", original_exception=e)

def modify_iceberg_order(
    kite: KiteConnect,
    order_id: str,
    quantity: Optional[int] = None,
    price: Optional[float] = None,
    order_type: Optional[str] = None,
    validity: Optional[str] = None,
    disclosed_quantity: Optional[int] = None,
    trigger_price: Optional[float] = None,
    iceberg_legs: Optional[int] = None,
    iceberg_quantity: Optional[int] = None,
) -> str:
    """
    Modify an open Iceberg Order.

    :param kite: An initialized KiteConnect object.
    :param order_id: The ID of the order to modify.
    :param quantity: The new total quantity.
    :param price: The new price.
    :param order_type: The new order type.
    :param validity: The new validity.
    :param disclosed_quantity: The new disclosed quantity.
    :param trigger_price: The new trigger price.
    :param iceberg_legs: The new number of legs.
    :param iceberg_quantity: The new quantity of each leg.
    :return: The modified order ID.
    """
    try:
        return kite.modify_order(
            variety=kite.VARIETY_ICEBERG,
            order_id=order_id,
            quantity=quantity,
            price=price,
            order_type=order_type,
            validity=validity,
            disclosed_quantity=disclosed_quantity,
            trigger_price=trigger_price,
            iceberg_legs=iceberg_legs,
            iceberg_quantity=iceberg_quantity,
        )
    except Exception as e:
        raise OrderPlacementError(f"Failed to modify iceberg order {order_id}", original_exception=e)

def cancel_advanced_order(
    kite: KiteConnect,
    variety: str,
    order_id: str,
    parent_order_id: Optional[str] = None,
) -> str:
    """
    Cancels an advanced order (CO, BO, AMO, Iceberg).

    :param kite: An initialized KiteConnect object.
    :param variety: The variety of the order (e.g., kite.VARIETY_CO, kite.VARIETY_AMO, kite.VARIETY_ICEBERG).
    :param order_id: The ID of the order to cancel.
    :param parent_order_id: Optional parent order ID for BOs.
    :return: The cancelled order ID.
    """
    try:
        return kite.cancel_order(
            variety=variety,
            order_id=order_id,
            parent_order_id=parent_order_id,
        )
    except Exception as e:
        raise OrderPlacementError(f"Failed to cancel order {order_id} of variety {variety}", original_exception=e)

def cancel_all_orders(kite: KiteConnect, order_type: Optional[str] = None) -> List[str]:
    """
    Cancels all pending orders, optionally filtered by order type.

    :param kite: An initialized KiteConnect object.
    :param order_type: Optional filter for order type (e.g., kite.ORDER_TYPE_LIMIT).
    :return: A list of cancelled order IDs.
    """
    cancelled_order_ids = []
    try:
        orders = kite.orders()
        for order in orders:
            if order['status'] == "PENDING" and (order_type is None or order['order_type'] == order_type):
                try:
                    cancelled_id = kite.cancel_order(order['variety'], order['order_id'])
                    cancelled_order_ids.append(cancelled_id)
                except Exception as e:
                    print(f"Error cancelling order {order['order_id']}: {e}")
    except Exception as e:
        raise DataFetchError("Failed to fetch orders for bulk cancellation.", original_exception=e)
    return cancelled_order_ids
