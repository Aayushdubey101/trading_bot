import argparse
import sys
import textwrap
import asyncio
import uvicorn

from ..core.config import settings
from ..core.logging import setup_logging


def main():
    parser = argparse.ArgumentParser(
        prog="trading-bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent("""\
            Binance Futures Testnet Trading Bot — Primetrade.ai
            ────────────────────────────────────────────────────
            Commands:
              serve   Start the FastAPI server (+ WebSocket feed + strategies)
              place   Place a single order directly via CLI (bypasses strategy engine)
              account Show account balances
        """),
    )

    parser.add_argument("command", choices=["serve", "place", "account"])
    parser.add_argument("--host",       default=settings.api_host)
    parser.add_argument("--port",       type=int, default=settings.api_port)
    parser.add_argument("--symbol",     default=None, help="e.g. BTCUSDT")
    parser.add_argument("--side",       default=None, help="BUY or SELL")
    parser.add_argument("--type",       default="MARKET", help="MARKET | LIMIT | STOP_MARKET")
    parser.add_argument("--qty",        default=None, help="Order quantity")
    parser.add_argument("--price",      default=None, help="Price (LIMIT / STOP_MARKET)")
    parser.add_argument("--api-key",    default=None)
    parser.add_argument("--api-secret", default=None)

    args = parser.parse_args()
    setup_logging()

    if args.command == "serve":
        print(f"Starting API server on {args.host}:{args.port}")
        uvicorn.run(
            "bot.api.server:app",
            host=args.host,
            port=args.port,
            log_level=settings.log_level.lower(),
        )

    elif args.command == "place":
        asyncio.run(_cli_place(args))

    elif args.command == "account":
        asyncio.run(_cli_account(args))

    else:
        parser.print_help()
        sys.exit(1)


# ── Async CLI helpers ─────────────────────────────────────────────────────────

async def _cli_place(args):
    from ..client.async_client import BinanceAsyncClient, BinanceAPIError
    from ..core.validators import validate_all

    try:
        params = validate_all(
            symbol     = args.symbol or "",
            side       = args.side   or "",
            order_type = args.type,
            quantity   = args.qty    or "0",
            price      = args.price,
        )
    except ValueError as exc:
        print(f"\n✘  Validation error: {exc}\n")
        sys.exit(1)

    print(f"\n  Symbol:     {params['symbol']}")
    print(f"  Side:       {params['side']}")
    print(f"  Type:       {params['order_type']}")
    print(f"  Quantity:   {params['quantity']}")
    print(f"  Price:      {params['price'] or 'N/A (MARKET)'}\n")

    client = BinanceAsyncClient(api_key=args.api_key, api_secret=args.api_secret)
    try:
        result = await client.place_order(
            symbol     = params["symbol"],
            side       = params["side"],
            order_type = params["order_type"],
            quantity   = params["quantity"],
            price      = params["price"],
        )
        print(f"  ✔  Order placed! orderId={result.get('orderId')}  status={result.get('status')}")
        print(f"     executedQty={result.get('executedQty')}  avgPrice={result.get('avgPrice')}\n")
    except BinanceAPIError as exc:
        print(f"  ✘  API error [{exc.code}]: {exc.msg}\n")
        sys.exit(1)
    finally:
        await client.close()


async def _cli_account(args):
    from ..client.async_client import BinanceAsyncClient, BinanceAPIError
    client = BinanceAsyncClient(api_key=args.api_key, api_secret=args.api_secret)
    try:
        data   = await client.get_account()
        assets = [a for a in data.get("assets", []) if float(a.get("walletBalance", 0)) > 0]
        print("\n  ── Account Balances (Testnet) ──────────────────────")
        if not assets:
            print("  No funded assets found.")
        for a in assets:
            print(f"  {a['asset']:<8}  Balance: {a['walletBalance']}   Available: {a['availableBalance']}")
        print()
    except BinanceAPIError as exc:
        print(f"  ✘  API error [{exc.code}]: {exc.msg}\n")
        sys.exit(1)
    finally:
        await client.close()


if __name__ == "__main__":
    main()
