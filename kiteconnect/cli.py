"""Simple command line interface for KiteConnect."""

import argparse
import json

from kiteconnect.connect import KiteConnect


# Individual command handlers -------------------------------------------------

def _cmd_login(args: argparse.Namespace) -> None:
    kite = KiteConnect(api_key=args.api_key)
    data = kite.generate_session(args.request_token, api_secret=args.api_secret)
    print(data.get("access_token"))


def _cmd_place_order(args: argparse.Namespace) -> None:
    kite = KiteConnect(api_key=args.api_key)
    kite.set_access_token(args.access_token)
    order_id = kite.place_order(
        variety=args.variety,
        tradingsymbol=args.symbol,
        exchange=args.exchange,
        transaction_type=args.transaction_type,
        quantity=args.quantity,
        order_type=args.order_type,
        product=args.product,
    )
    print(order_id)


def _cmd_holdings(args: argparse.Namespace) -> None:
    kite = KiteConnect(api_key=args.api_key)
    kite.set_access_token(args.access_token)
    holdings = kite.holdings()
    print(json.dumps(holdings, indent=2))


# Parser setup ----------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="KiteConnect CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    # Login command
    login = sub.add_parser("login", help="Generate an access token")
    login.add_argument("--api-key", required=True)
    login.add_argument("--api-secret", required=True)
    login.add_argument("--request-token", required=True)
    login.set_defaults(func=_cmd_login)

    # Place order command
    po = sub.add_parser("place-order", help="Place an order")
    po.add_argument("--api-key", required=True)
    po.add_argument("--access-token", required=True)
    po.add_argument("--symbol", required=True)
    po.add_argument("--exchange", required=True)
    po.add_argument("--transaction-type", required=True)
    po.add_argument("--quantity", type=int, required=True)
    po.add_argument("--order-type", required=True)
    po.add_argument("--product", required=True)
    po.add_argument("--variety", default="regular")
    po.set_defaults(func=_cmd_place_order)

    # Holdings command
    hold = sub.add_parser("holdings", help="List holdings")
    hold.add_argument("--api-key", required=True)
    hold.add_argument("--access-token", required=True)
    hold.set_defaults(func=_cmd_holdings)

    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
