import logging
from kiteconnect import KiteConnect

logging.basicConfig(level=logging.DEBUG)

kite = KiteConnect(api_key="your_api_key")

# Redirect the user to the login url obtained
# from kite.login_url(), and receive the request_token
# from the registered redirect url after the login flow.
# Once you have the request_token, obtain the access_token
# as follows.

# Generate a new session using the ``api_secret`` parameter
data = kite.generate_session("request_token_here", api_secret="your_secret")
kite.set_access_token(data["access_token"])

# Fetch margin detail for order/orders
try:
    # Fetch margin detail for single order
    order_param_single = [{
        "exchange": "NSE",
        "tradingsymbol": "INFY",
        "transaction_type": "BUY",
        "variety": "regular",
        "product": "MIS",
        "order_type": "MARKET",
        "quantity": 2
        }]

    margin_detail = kite.order_margins(order_param_single)
    logging.info("Required margin for single order: {}".format(margin_detail))    
    
    # Fetch margin detail for list of orders 
    order_param_multi = [{
        "exchange": "NSE",
        "tradingsymbol": "SBIN",
        "transaction_type": "BUY",
        "variety": "regular",
        "product": "MIS",
        "order_type": "MARKET",
        "quantity": 10
        },
        {
        "exchange": "NFO",
        "tradingsymbol": "TCS20DECFUT",
        "transaction_type": "BUY",
        "variety": "regular",
        "product": "MIS",
        "order_type": "LIMIT",
        "quantity": 5,
        "price":2725.30
        },
        {
        "exchange": "NFO",
        "tradingsymbol": "NIFTY20DECFUT",
        "transaction_type": "BUY",
        "variety": "bo",
        "product": "MIS",
        "order_type": "MARKET",
        "quantity": 5
    }]

    margin_detail = kite.order_margins(order_param_multi)
    logging.info("Required margin for order_list: {}".format(margin_detail))

    # Basket orders
    order_param_basket = [
    {
        "exchange": "NFO",
        "tradingsymbol": "NIFTY21JUN15400PE",
        "transaction_type": "BUY",
        "variety": "regular",
        "product": "MIS",
        "order_type": "MARKET",
        "quantity": 75
    },
	{
        "exchange": "NFO",
        "tradingsymbol": "NIFTY21JUN14450PE",
        "transaction_type": "SELL",
        "variety": "regular",
        "product": "MIS",
        "order_type": "MARKET",
        "quantity": 150
    }]

    margin_amount = kite.basket_order_margins(order_param_basket)
    logging.info("Required margin for basket order: {}".format(margin_amount))
    # Compact margin response
    margin_amount_comt = kite.basket_order_margins(order_param_basket, mode='compact')
    logging.info("Required margin for basket order in compact form: {}".format(margin_amount_comt))

except Exception as e:
    logging.info("Error fetching order margin: {}".format(e))


# Fetch virtual contract note charges
try:
    order_book_params = [
        {
            "order_id": "111111111",
            "exchange": "NSE",
            "tradingsymbol": "SBIN",
            "transaction_type": "BUY",
            "variety": "regular",
            "product": "CNC",
            "order_type": "MARKET",
            "quantity": 1,
            "average_price": 560
        },
        {
            "order_id": "2222222222",
            "exchange": "MCX",
            "tradingsymbol": "GOLDPETAL23AUGFUT",
            "transaction_type": "SELL",
            "variety": "regular",
            "product": "NRML",
            "order_type": "LIMIT",
            "quantity": 1,
            "average_price": 5862
        },
        {
            "order_id": "3333333333",
            "exchange": "NFO",
            "tradingsymbol": "NIFTY23AUG17900PE",
            "transaction_type": "BUY",
            "variety": "regular",
            "product": "NRML",
            "order_type": "LIMIT",
            "quantity": 100,
            "average_price": 1.5
        }]

    order_book_charges = kite.get_virtual_contract_note(order_book_params)
    logging.info("Virtual contract note charges: {}".format(order_book_charges))
except Exception as e:
    logging.info("Error fetching virtual contract note charges: {}".format(e))